import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

DEPENDENCIES_AVAILABLE = all(importlib.util.find_spec(name) for name in ("fastapi", "sqlalchemy", "geoalchemy2"))


@unittest.skipUnless(DEPENDENCIES_AVAILABLE, "FastAPI/SQLAlchemy dependencies are not installed")
class ApiPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_directory = tempfile.TemporaryDirectory()
        os.environ["DATABASE_URL"] = f"sqlite:///{Path(cls.temp_directory.name) / 'api-test.db'}"
        os.environ["DEMO_MODE"] = "true"
        os.environ["PHOTOGRAMMETRY_PROVIDER"] = "mock"
        os.environ["DETECTOR_PROVIDER"] = "mock"
        os.environ["SEGMENTATION_PROVIDER"] = "mock"
        from fastapi.testclient import TestClient
        from apps.api.app.main import app

        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        if DEPENDENCIES_AVAILABLE:
            cls.client_context.__exit__(None, None, None)
            cls.temp_directory.cleanup()

    def test_process_request_persists_job_artifacts_and_detection(self):
        site = self.client.post("/sites", json={"name": "API Test Yard", "latitude": 29.76, "longitude": -95.30}).json()
        capture_response = self.client.post("/captures", json={"site_id": site["id"], "label": "Mock flight", "captured_at": "2026-09-23T12:00:00Z"})
        self.assertEqual(capture_response.status_code, 200)
        capture = capture_response.json()

        response = self.client.post(f"/captures/{capture['id']}/process", json={"image_urls": ["mock://DJI_0001.JPG"]})
        self.assertEqual(response.status_code, 202)
        job_id = response.json()["job_id"]

        job = self.client.get(f"/processing/jobs/{job_id}")
        self.assertEqual(job.status_code, 200)
        self.assertEqual(job.json()["state"], "succeeded")
        self.assertEqual(job.json()["current_step"], "PersistResult")
        self.assertEqual({item["role"] for item in job.json()["artifacts"]}, {"orthomosaic", "point_cloud", "tile"})

        detections = self.client.get(f"/captures/{capture['id']}/detections")
        self.assertEqual(detections.status_code, 200)
        self.assertEqual(len(detections.json()), 1)
        self.assertEqual(detections.json()[0]["class_name"], "truck")


if __name__ == "__main__":
    unittest.main()
