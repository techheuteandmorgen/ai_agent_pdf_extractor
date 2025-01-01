import unittest
from unittest.mock import patch, MagicMock
import os
from app.preprocessing import process_pdf

class TestPreprocessing(unittest.TestCase):
    @patch("app.preprocessing.extract_text_with_pdfplumber")
    @patch("app.preprocessing.extract_with_ai")
    @patch("app.preprocessing.save_to_excel")
    def test_process_pdf(self, mock_save_to_excel, mock_extract_with_ai, mock_extract_text):
        # Mock the functions
        mock_extract_text.return_value = "Mocked raw text from PDF"
        mock_extract_with_ai.return_value = {
            "policy_number": "201520070124700944100000",
            "customer_name": "AMIT KUMAR SHUKLA",
            "broker_name": "Heute and Morgen Insurance Broker Pvt Ltd",
            "imd_code": "IMD1115515",
            "chassis_number": "MAKDF155KDN007466",
            "engine_number": "L12B33315194",
            "policy_issue_date": "02/12/2024"
        }
        mock_save_to_excel.return_value = None

        pdf_path = "test_pdfs/sample_policy.pdf"
        output_json_path = "output_data/sample_policy.json"
        output_excel_path = "output_data/sample_policy.xlsx"

        process_pdf(pdf_path, output_json_path, output_excel_path)

        self.assertTrue(os.path.exists(output_json_path))
        mock_save_to_excel.assert_called_once()