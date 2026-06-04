import unittest

from app.web import render_homepage


class WebRenderTest(unittest.TestCase):
    def test_homepage_contains_form_and_layout(self) -> None:
        html = render_homepage(
            explanation={
                "predicted_label": "Melanoma",
                "confidence": 0.91,
                "rationale": "Model tap trung vao vung sac to dam.",
                "overlay_png_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB",
                "focus_hint": "Vung mau nong la phan anh co anh huong lon.",
                "note": "Day la giai thich ho tro nghien cuu.",
            }
        )
        self.assertIn('action="/analyze"', html)
        self.assertIn('action="/screen"', html)
        self.assertIn("Tai anh len", html)
        self.assertIn("Sang loc 2 buoc", html)
        self.assertIn("/ledger/ui", html)
        self.assertIn("grid-template-columns: minmax(330px, 420px) minmax(0, 1fr)", html)
        self.assertIn("Giai thich AI", html)


if __name__ == "__main__":
    unittest.main()
