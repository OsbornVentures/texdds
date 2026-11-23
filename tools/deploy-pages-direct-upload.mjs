import { createHash } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const API_BASE = "https://api.cloudflare.com/client/v4";
const IGNORE_NAMES = new Set([
  ".DS_Store",
  ".git",
  ".wrangler",
  "_headers",
  "_redirects",
  "_routes.json",
  "_worker.js",
  "functions",
  "node_modules",
]);

const MIME = new Map([
  [".avif", "image/avif"],
  [".css", "text/css; charset=utf-8"],
  [".csv", "text/csv; charset=utf-8"],
  [".gif", "image/gif"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".js", "application/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".jsonl", "application/x-ndjson; charset=utf-8"],
  [".md", "text/markdown; charset=utf-8"],
  [".pdf", "application/pdf"],
  [".png", "image/png"],
  [".svg", "image/svg+xml; charset=utf-8"],
  [".txt", "text/plain; charset=utf-8"],
  [".webp", "image/webp"],
  [".xml", "application/xml; charset=utf-8"],
  [".yaml", "application/yaml; charset=utf-8"],
  [".yml", "application/yaml; charset=utf-8"],
]);

function parseEnv(text) {
  const values = new Map();
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const equals = line.indexOf("=");
    if (equals === -1) continue;
    const key = line.slice(0, equals).trim();
    let value = line.slice(equals + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    values.set(key, value);
  }
  return values;
}

async function apiFetch(url, options = {}, unwrap = true) {
  const response = await fetch(url, options);
  const text = await response.text();
  let json;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    json = { raw: text };
  }
  if (!response.ok || json.success === false) {
    const message = json.errors?.map((error) => error.message).join("; ") || text;
    throw new Error(`${response.status} ${response.statusText}: ${message}`);
  }
  return unwrap ? json.result : json;
}

function contentTypeFor(filePath) {
  const normalized = filePath.split(path.sep).join("/");
  if (normalized.endsWith("/.well-known/api-catalog")) {
    return 'application/linkset+json; profile="https://www.rfc-editor.org/info/rfc9727"; charset=utf-8';
  }
  return MIME.get(path.extname(filePath).toLowerCase()) || "application/octet-stream";
}

function assetHash(buffer, filePath) {
  const extension = path.extname(filePath).slice(1);
  return createHash("sha256")
    .update(buffer.toString("base64") + extension)
    .digest("hex")
    .slice(0, 32);
}

async function walkStaticFiles(root, dir = root, fileMap = new Map()) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_NAMES.has(entry.name)) continue;
    const absolute = path.join(dir, entry.name);
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory()) {
      await walkStaticFiles(root, absolute, fileMap);
      continue;
    }
    if (!entry.isFile()) continue;
    const buffer = await fs.readFile(absolute);
    const relative = path.relative(root, absolute).split(path.sep).join("/");
    const hash = assetHash(buffer, absolute);
    fileMap.set(relative, {
      absolute,
      buffer,
      contentType: contentTypeFor(absolute),
      hash,
      size: buffer.byteLength,
    });
  }
  return fileMap;
}

function chunk(items, size) {
  const chunks = [];
  for (let i = 0; i < items.length; i += size) {
    chunks.push(items.slice(i, i + size));
  }
  return chunks;
}

async function main() {
  const [
    staticDir = "texddssitefull",
    projectName = "texdds",
    branch = "main",
    commitMessage,
  ] = process.argv.slice(2);
  const root = path.resolve(staticDir);
  if (root !== path.resolve("texddssitefull") || projectName !== "texdds" || branch !== "main") {
    throw new Error("Only the tracked texddssitefull directory, texdds project and main branch may deploy. See docs/RELEASING.md.");
  }
  // No generation here: only the clean, pushed, validated and attested commit ships.
  const gate = spawnSync(process.env.PYTHON || "python", ["scripts/static_release.py", "gate"], {
    encoding: "utf8", windowsHide: true,
  });
  if (gate.status !== 0) throw new Error(`Repository-first preflight failed:\n${gate.error || gate.stderr || gate.stdout}`);
  const provenance = JSON.parse(gate.stdout);
  const manifestRead = spawnSync("git", ["show", `${provenance.commit}:docs/site-manifest.json`], { windowsHide: true });
  if (manifestRead.status !== 0) throw new Error("Cannot read the committed static manifest");
  const sourceManifestBytes = manifestRead.stdout;
  const sourceManifest = JSON.parse(sourceManifestBytes.toString("utf8"));
  const fileMap = await walkStaticFiles(root);
  const configs = new Map();
  for (const name of ["_headers", "_redirects"]) configs.set(name, await fs.readFile(path.join(root, name)));
  const snapshot = new Map([...fileMap].map(([name, file]) => [name, file.buffer]));
  for (const [name, data] of configs) snapshot.set(name, data);
  if (snapshot.size !== sourceManifest.files.length) throw new Error("Upload file count differs from the committed manifest");
  for (const expected of sourceManifest.files) {
    const bytes = snapshot.get(expected.path);
    if (!bytes || bytes.length !== expected.bytes || createHash("sha256").update(bytes).digest("hex") !== expected.sha256) {
      throw new Error(`Upload snapshot differs from committed file: ${expected.path}`);
    }
  }
  const envPath = path.resolve(".env");
  let env = new Map();
  try { env = parseEnv(await fs.readFile(envPath, "utf8")); }
  catch (error) { if (error.code !== "ENOENT") throw error; }
  const accountId = process.env.CLOUDFLARE_ACCOUNT_ID || env.get("CLOUDFLARE_ACCOUNT_ID");
  const apiToken = process.env.CLOUDFLARE_API_TOKEN || env.get("CLOUDFLARE_API_TOKEN");
  if (!accountId || !apiToken) {
    throw new Error("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN in .env");
  }

  const authHeaders = { Authorization: `Bearer ${apiToken}` };
  const tokenResult = await apiFetch(
    `${API_BASE}/accounts/${accountId}/pages/projects/${projectName}/upload-token`,
    { headers: authHeaders }
  );
  const uploadJwt = tokenResult.jwt;
  if (!uploadJwt) throw new Error("Cloudflare did not return a Pages upload JWT");

  const files = [...fileMap.values()];
  const hashes = files.map((file) => file.hash);
  const missing = await apiFetch(`${API_BASE}/pages/assets/check-missing`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${uploadJwt}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ hashes }),
  });
  const missingSet = new Set(missing);
  const missingFiles = files.filter((file) => missingSet.has(file.hash));

  for (const batch of chunk(missingFiles, 25)) {
    const payload = batch.map((file) => ({
      key: file.hash,
      value: file.buffer.toString("base64"),
      metadata: { contentType: file.contentType },
      base64: true,
    }));
    await apiFetch(`${API_BASE}/pages/assets/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${uploadJwt}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  }

  await apiFetch(`${API_BASE}/pages/assets/upsert-hashes`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${uploadJwt}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ hashes }),
  });

  const manifest = Object.fromEntries(
    [...fileMap.entries()].map(([fileName, file]) => [`/${fileName}`, file.hash])
  );
  const form = new FormData();
  form.append("manifest", JSON.stringify(manifest));
  form.append("branch", branch);
  form.append("commit_hash", provenance.commit);
  form.append("commit_dirty", "false");
  form.append("commit_message", commitMessage || `Deploy texdds ${provenance.commit}`);

  for (const [configName, bytes] of configs) {
    form.append(configName, new Blob([bytes], { type: "text/plain" }), configName);
  }

  const deployment = await apiFetch(
    `${API_BASE}/accounts/${accountId}/pages/projects/${projectName}/deployments`,
    {
      method: "POST",
      headers: authHeaders,
      body: form,
    }
  );

  const result = {
    sourceCommit: provenance.commit,
    workflowRun: provenance.workflowRun,
    siteManifestSha256: createHash("sha256").update(sourceManifestBytes).digest("hex"),
    projectName,
    branch,
    environment: deployment.environment,
    id: deployment.id,
    shortId: deployment.short_id,
    url: deployment.url,
    aliases: deployment.aliases,
    latestStage: deployment.latest_stage,
    fileCount: files.length,
    uploadedCount: missingFiles.length,
    reusedCount: files.length - missingFiles.length,
  };
  const receiptDir = path.resolve("docs/deployments");
  await fs.mkdir(receiptDir, { recursive: true });
  const receiptPath = path.join(receiptDir, `${provenance.commit.slice(0, 12)}-${deployment.id}.json`);
  const save = () => fs.writeFile(receiptPath, JSON.stringify(result, null, 2) + "\n");
  await save();
  let status = deployment;
  for (let attempt = 0; attempt < 30; attempt++) {
    status = await apiFetch(`${API_BASE}/accounts/${accountId}/pages/projects/${projectName}/deployments/${deployment.id}`, { headers: authHeaders });
    if (["success", "failure", "canceled"].includes(status.latest_stage?.status)) break;
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  const currentProject = await apiFetch(`${API_BASE}/accounts/${accountId}/pages/projects/${projectName}`, { headers: authHeaders });
  result.latestStage = status.latest_stage;
  result.isCanonicalProduction = currentProject.canonical_deployment?.id === deployment.id;
  result.assetManifestMatches = Object.keys(status.files || {}).length === fileMap.size &&
    [...fileMap].every(([name, file]) => status.files?.[`/${name}`] === file.hash);
  result.verifiedAt = new Date().toISOString();
  result.passed = status.latest_stage?.status === "success" && result.isCanonicalProduction && result.assetManifestMatches;
  await save();
  console.log(JSON.stringify(result, null, 2));
  console.log(`Commit and push the deployment receipt: ${path.relative(process.cwd(), receiptPath)}`);
  if (!result.passed) throw new Error("Deployment verification did not pass; inspect and preserve the receipt before further changes");
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
