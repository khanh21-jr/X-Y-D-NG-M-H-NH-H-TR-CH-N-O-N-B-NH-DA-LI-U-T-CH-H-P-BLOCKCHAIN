import tempfile
import unittest
import os
from pathlib import Path

from app import ledger


class LedgerTest(unittest.TestCase):
    def test_append_validate_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            original_path = ledger.LEDGER_PATH
            original_backend = os.environ.get("LEDGER_BACKEND")
            try:
                os.environ["LEDGER_BACKEND"] = "local"
                ledger.LEDGER_PATH = Path(tmp) / "prediction_chain.json"
                block = ledger.append_prediction(
                    source="test",
                    image_name="a.jpg",
                    image_bytes=b"abc",
                    model_dir="local-model",
                    top_k=3,
                    predictions=[{"code": "MEL", "label": "Melanoma", "score": 0.9}],
                )
                self.assertEqual(block.index, 0)
                self.assertTrue(block.signature)

                validation = ledger.validate_chain()
                self.assertTrue(validation["valid"])
                self.assertEqual(validation["length"], 1)

                json_export = ledger.export_chain_json()
                csv_export = ledger.export_chain_csv()
                self.assertIn('"signature"', json_export)
                self.assertIn("signature", csv_export)
            finally:
                ledger.LEDGER_PATH = original_path
                if original_backend is None:
                    os.environ.pop("LEDGER_BACKEND", None)
                else:
                    os.environ["LEDGER_BACKEND"] = original_backend


if __name__ == "__main__":
    unittest.main()
