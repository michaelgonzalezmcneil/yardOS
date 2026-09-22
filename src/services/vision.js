import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";

export class VisionServiceError extends Error {
  constructor(message, details) {
    super(message);
    this.name = "VisionServiceError";
    this.details = details;
  }
}

export async function detectOrthomosaic({ scanId, imagePath, serviceUrl = process.env.VISION_SERVICE_URL || "http://127.0.0.1:8000", outputDirectory = process.env.VISION_OUTPUT_DIR || "./data/vision", fetchImpl = globalThis.fetch }) {
  const form = new FormData();
  const contentType = /\.tiff?$/i.test(imagePath) ? "image/tiff" : /\.png$/i.test(imagePath) ? "image/png" : "image/jpeg";
  form.append("file", new Blob([await readFile(imagePath)], { type: contentType }), basename(imagePath));
  let response;
  try {
    response = await fetchImpl(`${serviceUrl.replace(/\/$/, "")}/detect`, { method: "POST", body: form });
  } catch (error) {
    throw new VisionServiceError(`Cannot reach YardOS vision service at ${serviceUrl}.`, error);
  }
  if (!response.ok) throw new VisionServiceError(`Vision service returned ${response.status}: ${await response.text()}`);
  const result = await response.json();
  const record = {
    scan_id: scanId,
    model_version: result.model_version,
    image_width: result.image_width,
    image_height: result.image_height,
    inference_time_ms: result.inference_time_ms,
    created_at: new Date().toISOString(),
    detections: result.detections.map((item, index) => ({
      id: `${scanId}-d${String(index + 1).padStart(5, "0")}`,
      scan_id: scanId,
      asset_class: item.class,
      confidence: item.confidence,
      bbox: item.bbox,
      center: item.center,
      model_version: result.model_version,
    })),
  };
  const destination = resolve(outputDirectory);
  await mkdir(destination, { recursive: true });
  const recordPath = join(destination, `${scanId}-detections.json`);
  await writeFile(recordPath, JSON.stringify(record, null, 2) + "\n");
  return { record, recordPath };
}
