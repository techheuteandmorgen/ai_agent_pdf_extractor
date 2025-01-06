import os
import pdfplumber
import pandas as pd
from .field_extraction import extract_with_ai, map_field_variations
from .utils import clean_numeric_field


def extract_text_with_pdfplumber(pdf_path):
    """Extract raw text from a PDF using pdfplumber."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages])
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def calculate_od_premium(data):
    """Calculate OD Premium as the sum of A and C sections."""
    od_a = clean_numeric_field(data.get("Total Own Damage Premium (A)", 0))
    od_c = clean_numeric_field(data.get("Total Add-On Premium (C)", 0))
    return od_a + od_c


def process_pdf(pdf_path, user_id=None):
    """Process a PDF and extract structured data."""
    try:
        # Extract raw text from the PDF
        raw_text = extract_text_with_pdfplumber(pdf_path)
        print(f"Debug: Extracted raw text from {pdf_path}.")

        # Use AI to extract structured data
        structured_data = extract_with_ai(raw_text)
        print(f"Debug: Extracted structured data from {pdf_path}:\n{structured_data}")

        # Validate and process numeric fields
        if structured_data:
            # Extract raw premiums
            od_a = clean_numeric_field(structured_data.get("Total Own Damage Premium (A)", 0))
            od_c = clean_numeric_field(structured_data.get("Total Add-On Premium (C)", 0))
            tp_b = clean_numeric_field(structured_data.get("Total Liability Premium (B)", 0))
            net_premium = clean_numeric_field(structured_data.get("Net Premium (A+B+C)", 0))
            total_premium = clean_numeric_field(structured_data.get("TOTAL_PREMIUM", 0))

            # Calculate OD Premium as A + C
            structured_data["OD_PREMIUM"] = od_a + od_c

            # TP Premium is directly extracted from B
            structured_data["TP_ONLY_PREMIUM"] = tp_b

            # Validate Net Premium (A+B+C)
            structured_data["NET_PREMIUM"] = net_premium

            # Total Premium validation
            calculated_total = structured_data["OD_PREMIUM"] + structured_data["TP_ONLY_PREMIUM"]
            if abs(calculated_total - total_premium) > 1e-2:
                print(f"Warning: Total Premium mismatch! Calculated: {calculated_total}, Extracted: {total_premium}")

            structured_data["TOTAL_PREMIUM"] = total_premium

        return structured_data

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None


def save_data_to_excel(data, output_path):
    """Save data to an Excel file, appending it if the file already exists."""
    try:
        # Convert data to a DataFrame
        df = pd.DataFrame(data)

        # Remove unwanted columns and intermediate fields
        df.drop(columns=["COMMISSION", "CHEQUE_NUMBER", "BANK_NAME", "Total Own Damage Premium (A)", "Total Add-On Premium (C)"], inplace=True, errors="ignore")

        # Desired column order
        desired_order = [
            "S_No", "YEAR", "MONTH", "DATE", "INSURANCE_COMPANY_NAME", "Broker_Name", "IMD_CODE",
            "LOB", "PACKAGE_LIABILITY", "FUEL_TYPE", "REN_ROLL_NEW_USED", "CUSTOMER_NAME", "MOB_NO",
            "LOCATION", "REG_NUMBER", "VEHICLE_MAKE", "VEHICLE_MODEL", "CC_GVW", "BIKE_SCOOTER",
            "YEAR_OF_MANUFACTURE", "ENGINE_NUMBER", "CHASIS_NUMBER", "POLICY_NO", "IDV_SUM_INSURED",
            "NCB", "RISK_START_DATE", "OD_EXPIRE_DATE", "RENEWAL_DATE",
            "OD_PREMIUM", "TP_ONLY_PREMIUM", "NET_PREMIUM", "TOTAL_PREMIUM",
            "POLICY_ISSUE_DAY", "source_file"
        ]

        # Reorder columns
        df = df.reindex(columns=desired_order, fill_value="N/A")

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
            "NET_PREMIUM", "TOTAL_PREMIUM", "source_file"
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

                    all_data.append(structured_data)

        if all_data:
            save_data_to_excel(all_data, consolidated_excel_path)
        else:
            print("No valid data extracted from PDFs.")
    except Exception as e:
        print(f"ERROR in bulk processing to Excel: {e}")