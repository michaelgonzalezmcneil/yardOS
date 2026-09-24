import { createWriteStream } from "node:fs";
import { mkdir, readFile, readdir, stat, writeFile } from "node:fs/promises";
import { basename, extname, join, resolve } from "node:path";
import { Readable } from "node:stream";
import { finished } from "node:stream/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const IMAGE_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".tif", ".tiff"]);

function isSupportedImagePath(path) {
  return IMAGE_EXTENSIONS.has(extname(path).toLowerCase());
}

export const TASK_STATUS = Object.freeze({
  QUEUED: 10,
  RUNNING: 20,
  FAILED: 30,
  COMPLETED: 40,
  CANCELED: 50,
});

export class NodeOdmError extends Error {
  constructor(message, details) {
    super(message);
    this.name = "NodeOdmError";
    this.details = details;
  }
}

export function nodeOdmConfig(env = process.env) {
  return {
    protocol: env.NODEODM_PROTOCOL || "http",
    host: env.NODEODM_HOST || "127.0.0.1",
    port: Number(env.NODEODM_PORT || 3000),
    pollIntervalMs: Number(env.NODEODM_POLL_INTERVAL_MS || 5000),
  };
}

export async function imagePathsFrom(input) {
  const values = Array.isArray(input) ? input : [input];
  const paths = [];
  for (const value of values) {
    const absolute = resolve(value);
    const stats = await stat(absolute);
    if (stats.isDirectory()) {
      const entries = await readdir(absolute, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isFile() && isSupportedImagePath(entry.name)) paths.push(join(absolute, entry.name));
      }
    } else if (isSupportedImagePath(absolute)) {
      paths.push(absolute);
    }
  }
  paths.sort();
  if (paths.length === 0) throw new NodeOdmError("No JPG, PNG, or TIFF images were found in the supplied paths.");
  return paths;
}

export class NodeOdmClient {
  constructor(config = nodeOdmConfig(), fetchImpl = globalThis.fetch) {
    this.baseUrl = `${config.protocol}://${config.host}:${config.port}`;
    this.pollIntervalMs = config.pollIntervalMs;
    this.fetch = fetchImpl;
  }

  async request(path, options) {
    let response;
    try {
      response = await this.fetch(`${this.baseUrl}${path}`, options);
    } catch (error) {
      throw new NodeOdmError(`Cannot reach NodeODM at ${this.baseUrl}. Is the Docker service running?`, error);
    }
    if (!response.ok) {
      const body = await response.text();
      throw new NodeOdmError(`NodeODM ${response.status} response for ${path}: ${body || response.statusText}`);
    }
    return response;
  }

  async health() {
    return (await this.request("/info")).json();
  }

  async submitImages(imageInput, { name = `YardOS scan ${new Date().toISOString()}`, options = {} } = {}) {
    const imagePaths = await imagePathsFrom(imageInput);
    const form = new FormData();
    for (const imagePath of imagePaths) {
      const data = await readFile(imagePath);
      form.append("images", new Blob([data]), basename(imagePath));
    }
    form.append("name", name);
    form.append("options", JSON.stringify(Object.entries(options).map(([optionName, value]) => ({ name: optionName, value }))));
    const result = await (await this.request("/task/new", { method: "POST", body: form })).json();
    if (!result.uuid) throw new NodeOdmError("NodeODM accepted the upload but did not return a task UUID.", result);
    return result.uuid;
  }

  async taskInfo(uuid) {
    return (await this.request(`/task/${encodeURIComponent(uuid)}/info`)).json();
  }

  async waitForCompletion(uuid, { intervalMs = this.pollIntervalMs, timeoutMs = 0, onProgress } = {}) {
    const startedAt = Date.now();
    for (;;) {
      const info = await this.taskInfo(uuid);
      onProgress?.(info);
      const code = info.status?.code;
      if (code === TASK_STATUS.COMPLETED) return info;
      if (code === TASK_STATUS.FAILED || code === TASK_STATUS.CANCELED) {
        throw new NodeOdmError(`NodeODM task ${uuid} ended with status ${code}.`, info);
      }
      if (timeoutMs > 0 && Date.now() - startedAt >= timeoutMs) throw new NodeOdmError(`Timed out waiting for NodeODM task ${uuid}.`, info);
      await new Promise((done) => setTimeout(done, intervalMs));
    }
  }

  async downloadAssets(uuid, destinationDirectory) {
    await mkdir(destinationDirectory, { recursive: true });
    const archivePath = join(destinationDirectory, `${uuid}-all.zip`);
    const response = await this.request(`/task/${encodeURIComponent(uuid)}/download/all.zip`);
    if (!response.body) throw new NodeOdmError("NodeODM returned an empty asset archive.");
    await finished(Readable.fromWeb(response.body).pipe(createWriteStream(archivePath)));
    return archivePath;
  }

  async extractOrthophoto(archivePath, destinationDirectory) {
    await mkdir(destinationDirectory, { recursive: true });
    const outputPath = join(destinationDirectory, "orthophoto.tif");
    try {
      const { stdout } = await execFileAsync("unzip", ["-p", archivePath, "odm_orthophoto/odm_orthophoto.tif"], { encoding: "buffer", maxBuffer: 1024 * 1024 * 1024 });
      await writeFile(outputPath, stdout);
    } catch (error) {
      throw new NodeOdmError(`Could not extract odm_orthophoto/odm_orthophoto.tif from ${archivePath}.`, error);
    }
    return outputPath;
  }

  async processScan(imageInput, { outputDirectory, name, options, intervalMs, timeoutMs, onProgress } = {}) {
    const taskId = await this.submitImages(imageInput, { name, options });
    await this.waitForCompletion(taskId, { intervalMs, timeoutMs, onProgress });
    const taskDirectory = join(resolve(outputDirectory || "./data/nodeodm-results"), taskId);
    const archivePath = await this.downloadAssets(taskId, taskDirectory);
    const orthophotoPath = await this.extractOrthophoto(archivePath, taskDirectory);
    return { taskId, archivePath, orthophotoPath };
  }
}
