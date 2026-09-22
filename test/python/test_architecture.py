import os
import unittest
from unittest.mock import patch

from services.change_detection.service import ObjectDifferenceBaseline
from services.drone.providers import MAVSDKDroneProvider
from services.geospatial.pipeline import GeoReferenceService, InferencePipeline, RasterReference, TileService, suppress_duplicates


class FakeImage:
    width = 1800
    height = 1024
    def crop(self, box):
        image = FakeImage()
        image.width, image.height = box[2] - box[0], box[3] - box[1]
        return image


class SeamDetector:
    def detect_image(self, image):
        # The same object appears in both overlapping tiles near their shared seam.
        return [{"class": "truck", "confidence": .9, "bbox": {"x": 900 if image.width == 1024 else 4, "y": 100, "width": 80, "height": 40}}]


class ArchitectureTests(unittest.TestCase):
    def test_affine_and_axis_order_are_explicit(self):
        reference = RasterReference(2, 0, 500_000, 0, -2, 3_300_000, "EPSG:32615")
        service = GeoReferenceService(reference, transformer=lambda easting, northing: ((easting - 500_000) / 100_000 - 95, (northing - 3_300_000) / 100_000 + 29))
        longitude, latitude = service.pixel_to_geo(100, 50)
        self.assertAlmostEqual(longitude, -94.998)
        self.assertAlmostEqual(latitude, 28.999)

    def test_rotated_affine_transform(self):
        reference = RasterReference(2, .5, -95, .25, -2, 30, "EPSG:4326")
        self.assertEqual(reference.pixel_to_projected(4, 3), (-85.5, 25.0))

    def test_nms_removes_overlapping_same_class_boxes(self):
        rows = [
            {"class": "truck", "confidence": .95, "bbox": {"x": 100, "y": 100, "width": 100, "height": 50}},
            {"class": "truck", "confidence": .80, "bbox": {"x": 104, "y": 102, "width": 100, "height": 50}},
        ]
        self.assertEqual(len(suppress_duplicates(rows)), 1)

    def test_change_comparison_requires_alignment(self):
        with self.assertRaisesRegex(ValueError, "share a CRS"):
            ObjectDifferenceBaseline().compare([], [])

    def test_real_drone_requires_two_explicit_switches(self):
        with patch.dict(os.environ, {"DRONE_MODE": "mavsdk", "DRONE_ALLOW_REAL_FLIGHT": "false"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "DRONE_ALLOW_REAL_FLIGHT"):
                MAVSDKDroneProvider()


if __name__ == "__main__":
    unittest.main()
