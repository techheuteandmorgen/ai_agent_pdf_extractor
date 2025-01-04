import os
import pdfplumber
import pandas as pd
from .field_extraction import extract_with_ai


def extract_text_with_pdfplumber(pdf_path):
    """Extract raw text from a PDF using pdfplumber."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages])
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def calculate_commission_and_net(data, commission_rate=0.4):
    """Calculate commission and net premium."""
    try:
        total_premium = float(data.get("TOTAL_PREMIUM", 0) or 0)
        commission = total_premium * commission_rate
        net_premium = total_premium - commission

        # Debugging output for verification
        print(f"DEBUG: Total Premium: {total_premium}, Commission: {commission}, Net Premium: {net_premium}")

        return commission, net_premium
    except Exception as e:
        print(f"ERROR calculating commission and net premium: {e}")
        return 0, 0


def clean_numeric_field(value):
    """Remove currency symbols, commas, and whitespace from a numeric field."""
    try:
        if isinstance(value, str):
            return float(value.replace('₹', '').replace(',', '').strip())
        return float(value)
    except ValueError:
        return 0.0  # Default to 0.0 if conversion fails

def process_pdf(pdf_path, user_id=None):
    """Process a PDF and extract structured data."""
    try:
        # Extract text from PDF
        raw_text = extract_text_with_pdfplumber(pdf_path)
        print(f"Debug: Extracted raw text from {pdf_path}.")

        # Extract structured data using AI
        structured_data = extract_with_ai(raw_text)
        print(f"Debug: Extracted structured data from {pdf_path}:\n{structured_data}")

        # Sanitize numeric fields
        if structured_data:
            structured_data["TOTAL_PREMIUM"] = clean_numeric_field(structured_data.get("TOTAL_PREMIUM", 0))
            structured_data["OD_PREMIUM"] = clean_numeric_field(structured_data.get("OD_PREMIUM", 0))
            structured_data["TP_ONLY_PREMIUM"] = clean_numeric_field(structured_data.get("TP_ONLY_PREMIUM", 0))
            structured_data["NET_PREMIUM"] = clean_numeric_field(structured_data.get("NET_PREMIUM", 0))
            structured_data["IDV_SUM_INSURED"] = clean_numeric_field(structured_data.get("IDV_SUM_INSURED", 0))

        return structured_data
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None


def save_data_to_excel(data, output_path):
    """Save data to an Excel file, appending it if the file already exists."""
    try:
        # Convert data to a DataFrame
        df = pd.DataFrame(data)

        # Append data if the file already exists
        if os.path.exists(output_path):
            existing_df = pd.read_excel(output_path)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
        else:
            updated_df = df

        # Save the updated DataFrame to an Excel file
        updated_df.to_excel(output_path, index=False)
        print(f"Data successfully exported to {output_path}")
    except Exception as e:
        print(f"Error saving to Excel: {e}")


def bulk_process_to_excel(input_folder, consolidated_excel_path, user_id):
    """Process multiple PDFs and consolidate data into an Excel file."""
    try:
        field_order = [
            "S_No", "YEAR", "MONTH", "DATE", "INSURANCE_COMPANY_NAME", "Broker_Name", "IMD_CODE",
            "LOB", "PACKAGE_LIABILITY", "FUEL_TYPE", "REN_ROLL_NEW_USED", "CUSTOMER_NAME", "MOB_NO",
            "LOCATION", "REG_NUMBER", "VEHICLE_MAKE", "VEHICLE_MODEL", "CC_GVW", "BIKE_SCOOTER",
            "YEAR_OF_MANUFACTURE", "ENGINE_NUMBER", "CHASIS_NUMBER", "POLICY_NO", "IDV_SUM_INSURED",
            "NCB", "RISK_START_DATE", "OD_EXPIRE_DATE", "RENEWAL_DATE", "OD_PREMIUM", "TP_ONLY_PREMIUM",
            "NET_PREMIUM", "TOTAL_PREMIUM", "COMMISSION", "CHEQUE_NUMBER", "BANK_NAME", "POLICY_ISSUE_DAY",
            "source_file"
        ]

        all_data = []

        for idx, file_name in enumerate(os.listdir(input_folder), start=1):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(input_folder, file_name)
                print(f"Processing {file_name}...")

                # Pass user_id to process_pdf
                structured_data = process_pdf(pdf_path, user_id)
                if structured_data:
                    structured_data["S_No"] = idx
                    structured_data["source_file"] = file_name

                    # Calculate commission and net premium
                    commission, net_premium = calculate_commission_and_net(structured_data)
                    structured_data["COMMISSION"] = commission
                    structured_data["NET_PREMIUM"] = net_premium

                    all_data.append(structured_data)

        if all_data:
            save_data_to_excel(all_data, consolidated_excel_path)
        else:
            print("No valid data extracted from PDFs.")
    except Exception as e:
        print(f"ERROR in bulk processing to Excel: {e}")