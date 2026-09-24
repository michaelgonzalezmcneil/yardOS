import unittest

from packages.contracts import Capture, ProcessingJob, ProcessingState
from packages.database import InMemoryRepository
from packages.events import InMemoryEventBus
from services.photogrammetry import MockPhotogrammetryProvider
from services.segmentation import MockSegmentationProvider
from services.vision.providers import MockDetectorProvider
from services.tracking import SimpleTrackingProvider
from services.change_detection import SimpleDifferenceProvider
from services.worker import CapturePipeline


class WorkerPipelineTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryRepository()
        self.events = InMemoryEventBus()
        self.pipeline = CapturePipeline(
            MockPhotogrammetryProvider(),
            MockDetectorProvider(),
            MockSegmentationProvider(),
            self.repository,
            self.events,
            tracking=SimpleTrackingProvider(),
            change_detection=SimpleDifferenceProvider(),
            poll_interval_seconds=0,
        )

    def test_requested_job_runs_full_mock_dag(self):
        capture = Capture(site_id="houston-test", label="Mock API capture", id="capture-test")
        job = ProcessingJob(capture_id=capture.id, id="job-test")

        result = self.pipeline.run(capture, ["mock://DJI_0001.JPG"], job=job)

        self.assertEqual(result.job.id, "job-test")
        self.assertEqual(result.job.state, ProcessingState.SUCCEEDED)
        self.assertEqual(result.job.current_step, "CaptureComplete")
        self.assertEqual(len(result.artifacts), 3)
        self.assertEqual(len(result.detections), 1)
        self.assertIsNotNone(result.detections[0].centroid_geo)
        self.assertIn(result.detections[0].id, self.repository.detections)
        self.assertEqual(len(result.tracks), 1)
        self.assertEqual(self.events.events[-1].type, "CaptureCompleted")
        self.assertEqual(
            [event.type for event in self.events.events],
            [
                "CaptureUploaded",
                "ExtractMetadata",
                "ValidateCapture",
                "RunPhotogrammetry",
                "OrthomosaicReady",
                "GenerateTiles",
                "RunDetection",
                "RunSegmentation",
                "GeoreferenceResults",
                "PersistResults",
                "RunTracking",
                "TrackingCompleted",
                "ComparePreviousCapture",
                "ChangeDetectionCompleted",
                "RunAnalytics",
                "CaptureCompleted",
            ],
        )

    def test_failure_is_persisted_and_emitted(self):
        capture = Capture(site_id="houston-test", label="Empty capture", id="capture-empty")
        job = ProcessingJob(capture_id=capture.id, id="job-empty")

        with self.assertRaisesRegex(ValueError, "at least one image"):
            self.pipeline.run(capture, [], job=job)

        self.assertEqual(self.repository.jobs[job.id].state, ProcessingState.FAILED)
        self.assertIn("at least one image", self.repository.jobs[job.id].error)
        self.assertEqual(self.events.events[-1].type, "CaptureFailed")

    def test_job_must_belong_to_capture(self):
        capture = Capture(site_id="houston-test", label="Mismatch", id="capture-one")
        job = ProcessingJob(capture_id="capture-two")
        with self.assertRaisesRegex(ValueError, "IDs do not match"):
            self.pipeline.run(capture, ["mock://DJI_0001.JPG"], job=job)

    def test_rerun_is_idempotent_for_artifacts_and_detections(self):
        capture = Capture(site_id="houston-test", label="Retry", id="capture-retry")
        job = ProcessingJob(capture_id=capture.id, id="job-retry")

        first = self.pipeline.run(capture, ["mock://DJI_0001.JPG"], job=job)
        second = self.pipeline.run(capture, ["mock://DJI_0001.JPG"], job=job)

        self.assertEqual([item.id for item in first.artifacts], [item.id for item in second.artifacts])
        self.assertEqual([item.id for item in first.detections], [item.id for item in second.detections])
        self.assertEqual(len(self.repository.detections), 1)
        self.assertEqual(second.job.attempts, 2)


if __name__ == "__main__":
    unittest.main()
