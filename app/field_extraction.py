import openai
import json
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_with_ai(raw_text):
    """
    Extract structured data using OpenAI API.
    This function uses context and variations to ensure accurate field mapping.
    """
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
        "OD_PREMIUM": "string",
        "TP_ONLY_PREMIUM": "string",
        "NET_PREMIUM": "string",
        "TOTAL_PREMIUM": "string",
        "POLICY_ISSUE_DAY": "string",
        "UGST": "string",
        "CGST": "string"
    }}
    Use the following mapping rules:
    - Variations for `OD_PREMIUM`: {od_variations}
    - Variations for `TP_ONLY_PREMIUM`: {tp_variations}
    - Variations for `NET_PREMIUM`: {net_variations}
    - Variations for `TOTAL_PREMIUM`: {total_variations}
    - Variations for `POLICY_ISSUE_DAY`: {policy_issue_variations}
    - Variations for `UGST`: {ugst_variations}
    - Variations for `CGST`: {cgst_variations}
    - Ensure `OD_PREMIUM` = "Total Own Damage Premium (A)" + "Total Add-On Premium (C)".
    - Ensure `NET_PREMIUM` = `OD_PREMIUM` + `TP_ONLY_PREMIUM`.
    - Ensure `RENEWAL_DATE` = `OD_EXPIRE_DATE`.
    - Map `REN_ROLL_NEW_USED` to "New" or "Old" based on context.
    For missing fields, return "N/A".
    Here is the extracted text:
    {raw_text}
    """
    try:
        # Define variations for key fields
        variations = {
            "od_variations": "Total Own Damage Premium (A), Own Damage Premium, Damage Premium, Total OD Premium – A, Net Own Damage Premium(a), OD Total (Rounded Off)",
            "tp_variations": "Total Liability Premium (B), Total Liability Premium, Third Party Premium, Liability Premium, Liability Premium(b), Total Premium Payable, Total Act Premium, Total Act Premium-B, TP Total (Rounded Off)",
            "net_variations": "Net Premium (A+B+C), Net Policy Premium, Total Net Premium, Net Premium (A+B), Net Premium, Total Premium (A+B+C+A1), Total Premium(Net Premium)(A+B), Total Premium (Net Premium) (A+B), Package premium (A+B), Total Package Premium(A+B), Gross Premium",
            "total_variations": "Policy Premium, Total Premium, Premium Amount, Total (Rounded Off), Total Policy Premium, Total, Total Amount, Final Premium, Net Payable, Final Premium",
            "policy_issue_variations": "Date of Issue, Receipt Date, Policy Issued On",
            "ugst_variations": "SGST @9 %, UGST @9 %",
            "cgst_variations": "CGST @9 %, Central GST @9 %",
        }

        # Format the prompt
        prompt = prompt_template.format(raw_text=raw_text, **variations)

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Parse the response
        response_content = response["choices"][0]["message"]["content"].strip()
        data = json.loads(response_content)
        print("Debug: Extracted structured data:", data)
        return data

    except Exception as e:
        print(f"Error in extract_with_ai: {e}")
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
        "Total Premium (Net Premium) (A+B)": "NET_PREMIUM",
        "Package premium (A+B)": "NET_PREMIUM",
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

        # POLICY_ISSUE_DAY Variations
        "Date of Issue": "POLICY_ISSUE_DAY",
        "Receipt Date": "POLICY_ISSUE_DAY",
        "Policy Issued On": "POLICY_ISSUE_DAY",

        # Tax Variations
        "SGST @9 %": "UGST",
        "UGST @9 %": "UGST",
        "CGST @9 %": "CGST",
        "Central GST @9 %": "CGST",
    }

    for key, new_key in field_mapping.items():
        if key in data:
            data[new_key] = data.pop(key)
    return data