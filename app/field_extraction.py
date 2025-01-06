import openai
import json
import os
from .utils import clean_numeric_field


openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_with_ai(raw_text):
    """Extract structured data using OpenAI API."""
    prompt_template = """
    Extract the following structured data as JSON from the text:
    {{
        "S_No": "string",
        "YEAR": "string",
        "MONTH": "string",
        "DATE": "string",
        "INSURANCE_COMPANY_NAME": "string",
        "Broker_Name": "string",
        "IMD_CODE": "string",
        "LOB": "string",
        "PACKAGE_LIABILITY": "string",
        "FUEL_TYPE": "string",
        "REN_ROLL_NEW_USED": "string",
        "CUSTOMER_NAME": "string",
        "MOB_NO": "string",
        "LOCATION": "string",
        "REG_NUMBER": "string",
        "VEHICLE_MAKE": "string",
        "VEHICLE_MODEL": "string",
        "CC_GVW": "string",
        "BIKE_SCOOTER": "string",
        "YEAR_OF_MANUFACTURE": "string",
        "ENGINE_NUMBER": "string",
        "CHASIS_NUMBER": "string",
        "POLICY_NO": "string",
        "IDV_SUM_INSURED": "string",
        "NCB": "string",
        "RISK_START_DATE": "string",
        "OD_EXPIRE_DATE": "string",
        "RENEWAL_DATE": "string",
        "Total Own Damage Premium (A)": "string",
        "Total Add-On Premium (C)": "string",
        "Total Liability Premium (B)": "string",
        "Net Premium (A+B+C)": "string",
        "TOTAL_PREMIUM": "string",
        "POLICY_ISSUE_DAY": "string"
    }}
    For any field that is not found in the text, return "N/A". Use context to map variations in field names accurately. For example:
    - "Agent License Code" should map to "IMD_CODE".
    - "Total Liability Premium (B)" should map to "TP_ONLY_PREMIUM".
    - "Net Premium (A+B+C)" should map to "NET_PREMIUM".
    - "Total Own Damage Premium (A)" and "Total Add-On Premium (C)" should sum up to "OD_PREMIUM".
    Here is the extracted text:
    {raw_text}
    """
    try:
        # Prepare the prompt
        prompt = prompt_template.format(raw_text=raw_text)

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Extract the content from the API response
        response_content = response["choices"][0]["message"]["content"].strip()

        # Parse the JSON response
        try:
            data = json.loads(response_content)
            print("Debug: Extracted structured data:", data)  # Debugging
            return data
        except json.JSONDecodeError as e:
            print(f"Debug: JSON decode error: {e}")
            return {"error": "Invalid JSON in API response", "raw_response": response_content}

    except Exception as e:
        print(f"Debug: Error encountered: {e}")
        return {"error": str(e)}


def map_field_variations(data):
    """
    Map field name variations to standardized keys.
    Example: "Agent License Code" -> "IMD_CODE".
    """
    field_mapping = {
        "Agent License Code": "IMD_CODE",
        "Total Liability Premium (B)": "TP_ONLY_PREMIUM",
        "Net Premium (A+B+C)": "NET_PREMIUM",
        "Total Own Damage Premium (A)": "OD_PREMIUM_A",
        "Total Add-On Premium (C)": "OD_PREMIUM_C"
    }

    # Map known variations
    for key, new_key in field_mapping.items():
        if key in data:
            data[new_key] = data.pop(key)

    return data


def preprocess_extracted_data(raw_data):
    """
    Preprocess the raw extracted data to handle calculated fields
    like OD_PREMIUM and ensure consistency.
    """
    try:
        # Map field variations
        raw_data = map_field_variations(raw_data)

        # Handle OD Premium (sum of A and C)
        od_a = clean_numeric_field(raw_data.get("OD_PREMIUM_A", 0))
        od_c = clean_numeric_field(raw_data.get("OD_PREMIUM_C", 0))
        raw_data["OD_PREMIUM"] = od_a + od_c

        # Ensure other fields are numeric
        raw_data["TOTAL_PREMIUM"] = clean_numeric_field(raw_data.get("TOTAL_PREMIUM", 0))
        raw_data["TP_ONLY_PREMIUM"] = clean_numeric_field(raw_data.get("TP_ONLY_PREMIUM", 0))
        raw_data["NET_PREMIUM"] = clean_numeric_field(raw_data.get("NET_PREMIUM", 0))

        return raw_data
    except Exception as e:
        print(f"Error preprocessing data: {e}")
        return raw_data