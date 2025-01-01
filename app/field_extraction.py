import openai
import json
import os

openai.api_key = os.getenv("OPENAI_API_KEY")


def extract_with_ai(raw_text):
    """Extract structured data using OpenAI API."""
    prompt_template = """
    Extract the following structured data as JSON from the text:
    {{
        "policy_number": "string",
        "customer_name": "string",
        "broker_name": "string",
        "imd_code": "string",
        "chassis_number": "string",
        "engine_number": "string",
        "policy_issue_date": "string",
        "year": "string",
        "month": "string",
        "date": "string",
        "insurance_company_name": "string",
        "fuel_type": "string",
        "location": "string",
        "vehicle_make": "string",
        "vehicle_model": "string",
        "risk_start_date": "string",
        "od_expire_date": "string",
        "renewal_date": "string",
        "total_premium": "string"
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