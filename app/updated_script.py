import pdfplumber
import json
import os
from openai import OpenAIError
from openai import ChatCompletion


PROMPT_TEMPLATE = """
You are an AI specialized in extracting structured data from text.
The text below is extracted from an insurance policy PDF. Return a JSON with the following structure:
{
  "policy_number": "Extracted Policy Number",
  "customer_name": "Extracted Customer Name",
  "customer_address": "Extracted Customer Address",
  "agent_name": "Extracted Agent Name",
  "agent_code": "Extracted Agent Code",
  "agent_contact": "Extracted Agent Contact",
  "chassis_number": "Extracted Chassis Number",
  "engine_number": "Extracted Engine Number",
  "policy_issue_date": "Extracted Policy Issue Date",
  "vehicle_registration_number": "Extracted Vehicle Registration Number",
  "vehicle_make_model": "Extracted Vehicle Make and Model",
  "policy_premium": "Extracted Policy Premium",
  "period_of_insurance": "Extracted Period of Insurance"
}
Only return valid JSON. Here is the extracted text:
{raw_text}
"""


def extract_text_with_pdfplumber(pdf_path):
    """Extract raw text from a PDF using pdfplumber."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text

# Step 2: Extract Fields with AI
def extract_with_ai(raw_text):
    """Extract structured data from raw text using OpenAI's GPT model."""
    prompt = PROMPT_TEMPLATE.format(raw_text=raw_text)

    try:
        response = ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        ai_content = response.choices[0].message.content.strip()
        data = json.loads(ai_content)
        return data
    except OpenAIError as e:
        return {"error": str(e)}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from AI."}

# Step 3: Process PDF End-to-End
def process_pdf(pdf_path, output_folder="output_data"):
    """Process a PDF, extract text, send to AI, and save structured JSON output."""
    os.makedirs(output_folder, exist_ok=True)

    # Extract raw text
    raw_text = extract_text_with_pdfplumber(pdf_path)

    # Extract structured data
    extracted_data = extract_with_ai(raw_text)

    # Save to JSON
    output_file = os.path.join(output_folder, f"{os.path.basename(pdf_path)}.json")
    with open(output_file, "w") as f:
        json.dump(extracted_data, f, indent=4)

    print(f"Processed {pdf_path} and saved to {output_file}")

# Main for Testing
if __name__ == "__main__":
    sample_pdf_path = "test_pdfs/sample_policy.pdf"
    output_directory = "output_data"

    try:
        process_pdf(sample_pdf_path, output_directory)
    except Exception as e:
        print(f"Error processing PDF: {e}")
