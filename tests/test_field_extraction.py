import unittest
from unittest.mock import patch
import json
from app.field_extraction import extract_with_ai


class TestFieldExtraction(unittest.TestCase):

    @patch("app.field_extraction.openai.ChatCompletion.create")
    def test_extract_with_ai(self, mock_openai):
        # Mock API response
        mock_openai.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "policy_number": "201520070124700944100000",
                            "customer_name": "AMIT KUMAR SHUKLA",
                            "broker_name": "Heute and Morgen Insurance Broker Pvt Ltd",
                            "imd_code": "IMD1115515",
                            "chassis_number": "MAKDF155KDN007466",
                            "engine_number": "L12B33315194",
                            "policy_issue_date": "02/12/2024",
                            "year": "2024",
                            "month": "12",
                            "date": "02",
                            "insurance_company_name": "Liberty General Insurance Limited",
                            "fuel_type": "Petrol",
                            "location": "Lucknow",
                            "vehicle_make": "HONDA",
                            "vehicle_model": "AMAZE 1.2 S MT I-VTEC",
                            "risk_start_date": "04/12/2024",
                            "od_expire_date": "03/12/2025",
                            "renewal_date": "03/12/2025",
                            "total_premium": "4090.00"
                        })
                    }
                }
            ]
        }

        # Call function with mock data
        raw_text = "Sample raw text for policy extraction"
        extracted_data = extract_with_ai(raw_text)

        # Debug: Print extracted data
        print("Debug: Extracted structured data:", extracted_data)

        # Assertions
        self.assertIn("policy_number", extracted_data)
        self.assertEqual(extracted_data["policy_number"], "201520070124700944100000")
        self.assertEqual(extracted_data["customer_name"], "AMIT KUMAR SHUKLA")
        self.assertEqual(extracted_data["total_premium"], "4090.00")

    @patch("app.field_extraction.openai.ChatCompletion.create")
    def test_error_handling(self, mock_openai):
        # Mock API error response
        mock_openai.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"error": "Invalid request"}'
                    }
                }
            ]
        }

        # Call function with mock data
        raw_text = "Sample raw text for policy extraction"
        extracted_data = extract_with_ai(raw_text)

        # Debug: Print extracted data
        print("Debug: Extracted structured data with error:", extracted_data)

        # Assertions
        self.assertIn("error", extracted_data)


if __name__ == "__main__":
    unittest.main()