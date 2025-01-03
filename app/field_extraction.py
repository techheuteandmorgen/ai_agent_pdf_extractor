import openai
import json
import os

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
        "OD_PREMIUM": "string",
        "TP_ONLY_PREMIUM": "string",
        "NET_PREMIUM": "string",
        "TOTAL_PREMIUM": "string",
        "CHEQUE_NUMBER": "string",
        "BANK_NAME": "string",
        "POLICY_ISSUE_DAY": "string"
    }}
    If a field is not found in the text, return "N/A". Here is the extracted text:
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