import unittest

from app.labels import LABEL_MAP


class LabelMapTest(unittest.TestCase):
    def test_label_map_has_eight_classes(self) -> None:
        self.assertEqual(len(LABEL_MAP), 8)
        self.assertEqual(LABEL_MAP["MEL"], "Melanoma")


if __name__ == "__main__":
    unittest.main()
