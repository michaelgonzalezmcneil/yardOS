#!/usr/bin/env node
import { resolve } from "node:path";
import { NodeOdmClient, imagePathsFrom } from "../src/services/nodeodm.js";
import { detectOrthomosaic } from "../src/services/vision.js";

const inputs = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));
const skipVision = process.argv.includes("--skip-vision");
if (inputs.length === 0) {
  console.error("Usage: npm run process-test-scan -- <image-folder-or-images...>");
  process.exitCode = 1;
} else {
  try {
    const images = await imagePathsFrom(inputs);
    const client = new NodeOdmClient();
    const outputDirectory = resolve(process.env.NODEODM_OUTPUT_DIR || "./data/nodeodm-results");
    console.log(`Submitting ${images.length} images to ${client.baseUrl}...`);
    const result = await client.processScan(images, {
      outputDirectory,
      name: `YardOS test scan ${new Date().toISOString()}`,
      options: { "orthophoto-resolution": 5 },
      onProgress: (info) => console.log(`Task ${info.uuid}: ${info.progress ?? 0}% (status ${info.status?.code})`),
    });
    console.log(`Complete. Orthophoto: ${result.orthophotoPath}`);
    if (!skipVision) {
      console.log("Sending orthophoto to YardOS vision service...");
      const vision = await detectOrthomosaic({ scanId: result.taskId, imagePath: result.orthophotoPath });
      console.log(`Saved ${vision.record.detections.length} detections: ${vision.recordPath}`);
    }
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
