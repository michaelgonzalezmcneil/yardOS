import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { NodeOdmClient, TASK_STATUS, imagePathsFrom, nodeOdmConfig } from "../src/services/nodeodm.js";
import { detectOrthomosaic } from "../src/services/vision.js";

test("reads NodeODM host and port from the environment", () => {
  assert.deepEqual(nodeOdmConfig({ NODEODM_HOST: "nodeodm", NODEODM_PORT: "4444", NODEODM_PROTOCOL: "https", NODEODM_POLL_INTERVAL_MS: "25" }), {
    host: "nodeodm", port: 4444, protocol: "https", pollIntervalMs: 25,
  });
});

test("persists structured YardOS detections from the vision service", async () => {
  const directory = await mkdtemp(join(tmpdir(), "yardos-vision-"));
  const image = join(directory, "ortho.png");
  await writeFile(image, "fake-png");
  const fakeFetch = async () => Response.json({
    detections: [{ class: "truck", confidence: 0.94, bbox: { x: 20, y: 10, width: 12, height: 5 }, center: { x: 26, y: 12.5 } }],
    image_width: 100, image_height: 50, model_version: "test-model", inference_time_ms: 4,
  });
  const result = await detectOrthomosaic({ scanId: "scan-1", imagePath: image, outputDirectory: directory, fetchImpl: fakeFetch });
  assert.equal(result.record.detections[0].scan_id, "scan-1");
  assert.equal(result.record.detections[0].asset_class, "truck");
});

test("collects only supported image files", async () => {
  const directory = await mkdtemp(join(tmpdir(), "yardos-nodeodm-"));
  await Promise.all([writeFile(join(directory, "b.PNG"), "b"), writeFile(join(directory, "a.jpg"), "a"), writeFile(join(directory, "notes.txt"), "ignore")]);
  assert.deepEqual((await imagePathsFrom(directory)).map((path) => path.split("/").at(-1)), ["a.jpg", "b.PNG"]);
});

test("submits images and polls until completion", async () => {
  const directory = await mkdtemp(join(tmpdir(), "yardos-nodeodm-"));
  const image = join(directory, "scan.jpg");
  await writeFile(image, "fake-jpeg");
  let polls = 0;
  const fakeFetch = async (url, options) => {
    if (url.endsWith("/task/new")) {
      assert.equal(options.method, "POST");
      assert.equal(options.body.get("name"), "test scan");
      assert.equal(options.body.getAll("images").length, 1);
      return Response.json({ uuid: "task-123" });
    }
    polls += 1;
    return Response.json({ uuid: "task-123", progress: polls === 1 ? 50 : 100, status: { code: polls === 1 ? TASK_STATUS.RUNNING : TASK_STATUS.COMPLETED } });
  };
  const client = new NodeOdmClient({ protocol: "http", host: "localhost", port: 3000, pollIntervalMs: 0 }, fakeFetch);
  assert.equal(await client.submitImages([image], { name: "test scan" }), "task-123");
  const result = await client.waitForCompletion("task-123", { intervalMs: 0 });
  assert.equal(result.status.code, TASK_STATUS.COMPLETED);
  assert.equal(polls, 2);
});
