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
    - Ensure that `RENEWAL_DATE` matches `OD_EXPIRE_DATE`.
    - Ensure that `RISK_START_DATE` corresponds to `START_DATE`.
    - Ensure that `REN_ROLL_NEW_USED` is standardized to "New" or "Old" based on the vehicle's registration status.
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
    This function ensures consistent field names across extracted data.
    """
    field_mapping = {
        # IMD_CODE Variations
        "Agent License Code": "IMD_CODE",
        "IMD Code": "IMD_CODE",
        "Broker License Code": "IMD_CODE",
        "Partner Code": "IMD_CODE",
        "Agency Code": "IMD_CODE",
        "Broker Code": "IMD_CODE",
        "Code": "IMD_CODE",
        "Sales Channel Code": "IMD_CODE",
        "Intermediary Code": "IMD_CODE",

        # OD_PREMIUM Variations
        "Total Own Damage Premium (A)": "OD_PREMIUM",
        "Own Damage Premium": "OD_PREMIUM",
        "Damage Premium": "OD_PREMIUM",
        "Total OD Premium – A": "OD_PREMIUM",
        "Net Own Damage Premium(a)": "OD_PREMIUM",
        "OD Total (Rounded Off)": "OD_PREMIUM",

        # TP_ONLY_PREMIUM Variations
        "Total Liability Premium (B)": "TP_ONLY_PREMIUM",
        "Total Liability Premium": "TP_ONLY_PREMIUM",
        "Third Party Premium": "TP_ONLY_PREMIUM",
        "Liability Premium": "TP_ONLY_PREMIUM",
        "Liability Premium(b)": "TP_ONLY_PREMIUM",
        "Total Premium Payable": "TP_ONLY_PREMIUM",
        "Total Act Premium": "TP_ONLY_PREMIUM",
        "Total Act Premium-B": "TP_ONLY_PREMIUM",
        "TP Total (Rounded Off)": "TP_ONLY_PREMIUM",

        # NET_PREMIUM Variations
        "Net Premium (A+B+C)": "NET_PREMIUM",
        "Net Policy Premium": "NET_PREMIUM",
        "Total Net Premium": "NET_PREMIUM",
        "Net Premium (A+B)": "NET_PREMIUM",
        "Net Premium": "NET_PREMIUM",
        "Total Premium (A+B+C+A1)": "NET_PREMIUM",
        "Total Premium(Net Premium)(A+B)": "NET_PREMIUM",
        "Total Premium": "NET_PREMIUM",
        "Premium": "NET_PREMIUM",
        "Total Package Premium(A+B)": "NET_PREMIUM",
        "Gross Premium": "NET_PREMIUM",

        # TOTAL_PREMIUM Variations
        "Policy Premium": "TOTAL_PREMIUM",
        "Total Premium": "TOTAL_PREMIUM",
        "Premium Amount": "TOTAL_PREMIUM",
        "Total (Rounded Off)": "TOTAL_PREMIUM",
        "Total Policy Premium": "TOTAL_PREMIUM",
        "Total": "TOTAL_PREMIUM",
        "Total Amount": "TOTAL_PREMIUM",
        "Final Premium": "TOTAL_PREMIUM",
        "Net Payable": "TOTAL_PREMIUM",

        # Broker Name Variations
        "Agent Name": "Broker_Name",
        "Partner Name": "Broker_Name",
        "Agency Name": "Broker_Name",
        "Agent/Intermediary Name": "Broker_Name",
        "Intermediary Name": "Broker_Name",
        "Broker Name": "Broker_Name",
        "Channel": "Broker_Name",

        # Policy_Issue_Date Variations
        "Date of Issue": "POLICY_ISSUE_DAY",
    }

    # Map known variations
    for key, new_key in field_mapping.items():
        if key in data:
            data[new_key] = data.pop(key)

    return data


def preprocess_extracted_data(raw_data):
    """
    Preprocess the raw extracted data to handle calculated fields
    like OD_PREMIUM, TP_ONLY_PREMIUM, and NET_PREMIUM.
    """
    try:
        # Map field variations
        raw_data = map_field_variations(raw_data)

        # Handle OD Premium (sum of A and C)
        od_a = clean_numeric_field(raw_data.get("OD_PREMIUM_A", 0))
        od_c = clean_numeric_field(raw_data.get("OD_PREMIUM_C", 0))
        raw_data["OD_PREMIUM"] = od_a + od_c

        # Ensure TP Premium is numeric
        tp_premium = clean_numeric_field(raw_data.get("TP_ONLY_PREMIUM", 0))

        # Recalculate Net Premium if missing or zero
        net_premium = clean_numeric_field(raw_data.get("NET_PREMIUM", 0))
        if net_premium == 0:  # Recalculate only if zero
            net_premium = raw_data["OD_PREMIUM"] + tp_premium
        raw_data["NET_PREMIUM"] = net_premium

        # Ensure Total Premium is numeric
        raw_data["TOTAL_PREMIUM"] = clean_numeric_field(raw_data.get("TOTAL_PREMIUM", 0))

        # Ensure RENEWAL_DATE matches OD_EXPIRE_DATE
        raw_data["RENEWAL_DATE"] = raw_data.get("OD_EXPIRE_DATE", "N/A")

        # Ensure RISK_START_DATE is standardized
        raw_data["RISK_START_DATE"] = raw_data.get("START_DATE", raw_data.get("RISK_START_DATE", "N/A"))

        # Standardize REN_ROLL_NEW_USED to "New" or "Old"
        reg_type = raw_data.get("REN_ROLL_NEW_USED", "").strip().lower()
        if "new" in reg_type:
            raw_data["REN_ROLL_NEW_USED"] = "New"
        elif "old" in reg_type or "used" in reg_type:
            raw_data["REN_ROLL_NEW_USED"] = "Old"
        else:
            raw_data["REN_ROLL_NEW_USED"] = "Unknown"

        return raw_data
    except Exception as e:
        print(f"Error preprocessing data: {e}")
        return raw_data