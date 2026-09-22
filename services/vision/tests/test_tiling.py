import unittest

from app.domain import Detection
from app.tiling import intersection_over_union, non_max_suppression, tile_windows


class TilingTests(unittest.TestCase):
    def test_windows_cover_edges_with_overlap(self):
        windows = tile_windows(2500, 1800, 1024, 128)
        self.assertIn((1476, 776, 2500, 1800), windows)
        self.assertEqual(windows[0], (0, 0, 1024, 1024))

    def test_nms_removes_same_class_duplicate(self):
        strong = Detection("truck", 0.94, 100, 100, 120, 50)
        duplicate = Detection("truck", 0.75, 105, 102, 120, 50)
        other_class = Detection("car", 0.70, 105, 102, 120, 50)
        self.assertGreater(intersection_over_union(strong, duplicate), 0.5)
        self.assertEqual(non_max_suppression([duplicate, other_class, strong]), [strong, other_class])


if __name__ == "__main__":
    unittest.main()
