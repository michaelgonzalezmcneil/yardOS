import unittest

from training.prepare_visdrone import convert_annotation


class VisDroneConversionTests(unittest.TestCase):
    def test_converts_truck_to_normalized_yolo(self):
        self.assertEqual(convert_annotation("100,50,200,100,1,6,0,0", 1000, 500), "2 0.200000 0.200000 0.200000 0.200000")

    def test_skips_ignored_and_unselected_classes(self):
        self.assertIsNone(convert_annotation("0,0,10,10,0,4,0,0", 100, 100))
        self.assertIsNone(convert_annotation("0,0,10,10,1,1,0,0", 100, 100))


if __name__ == "__main__":
    unittest.main()
