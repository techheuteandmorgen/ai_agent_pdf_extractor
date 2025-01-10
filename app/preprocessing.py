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


def validate_and_calculate_premiums(data):
    """
    Validate and calculate premiums:
    - Ensure OD_PREMIUM and TP_ONLY_PREMIUM are correctly extracted and validated.
    - Recalculate NET_PREMIUM only if it is missing or clearly incorrect.
    - Ensure TOTAL_PREMIUM maps to Final Premium.
    """
    try:
        # Extract premiums
        od_premium = clean_numeric_field(data.get("OD_PREMIUM", 0))
        tp_premium = clean_numeric_field(data.get("TP_ONLY_PREMIUM", 0))
        net_premium = clean_numeric_field(data.get("NET_PREMIUM", 0))
        total_premium = clean_numeric_field(data.get("TOTAL_PREMIUM", 0))

        # Recalculate NET_PREMIUM if it is missing or incorrect
        calculated_net = od_premium + tp_premium
        if net_premium == 0 or abs(calculated_net - net_premium) > 1e-2:
            print(f"Warning: Recalculating NET_PREMIUM. Extracted: {net_premium}, Calculated: {calculated_net}")
            data["NET_PREMIUM"] = calculated_net

        # Ensure TOTAL_PREMIUM maps correctly to Final Premium
        if total_premium == 0 or abs(total_premium - data["NET_PREMIUM"]) > 1e-2:
            print(f"Warning: Recalculating TOTAL_PREMIUM. Extracted: {total_premium}, Using: {data['NET_PREMIUM']}")
            data["TOTAL_PREMIUM"] = data["NET_PREMIUM"]

    except Exception as e:
        print(f"Error validating and calculating premiums: {e}")

    return data

def validate_and_calculate_package_liability(data):
    """
    Validate and populate the PACKAGE_LIABILITY field based on OD_PREMIUM.
    """
    try:
        od_premium = clean_numeric_field(data.get("OD_PREMIUM", 0))

        if od_premium == 0:
            data["PACKAGE_LIABILITY"] = "Liability Only Policy"
        else:
            data["PACKAGE_LIABILITY"] = "Package Policy"

    except Exception as e:
        print(f"Error validating PACKAGE_LIABILITY: {e}")
        data["PACKAGE_LIABILITY"] = "N/A"  # Fallback if there's an error

    return data

def validate_and_standardize_dates(data):
    """
    Validate and standardize date fields:
    - Ensure `RENEWAL_DATE` matches `OD_EXPIRE_DATE`.
    - Extract and standardize `POLICY_ISSUE_DATE`.
    """
    try:
        # Match RENEWAL_DATE to OD_EXPIRE_DATE
        data["RENEWAL_DATE"] = data.get("OD_EXPIRE_DATE", "N/A")

        # Standardize POLICY_ISSUE_DATE
        issue_date_variations = ["Date of issue", "Policy Issued On", "Receipt Date"]
        for variation in issue_date_variations:
            if variation in data and data.get(variation):
                data["POLICY_ISSUE_DATE"] = data.pop(variation)
                break

    except Exception as e:
        print(f"Error standardizing dates: {e}")

    return data


def standardize_vehicle_registration(data):
    """
    Standardize `REN_ROLL_NEW_USED` based on the registration type.
    """
    try:
        value = data.get("REN_ROLL_NEW_USED", "").strip().lower()

        # Simplify the value based on logical mapping
        if "new" in value:
            data["REN_ROLL_NEW_USED"] = "New"
        elif "old" in value or "used" in value:
            data["REN_ROLL_NEW_USED"] = "Old"
        else:
            data["REN_ROLL_NEW_USED"] = "Unknown"

    except Exception as e:
        print(f"Error standardizing vehicle registration: {e}")

    return data


def process_pdf(pdf_path, user_id=None):
    """Process a PDF and extract structured data."""
    try:
        # Extract raw text from the PDF
        raw_text = extract_text_with_pdfplumber(pdf_path)

        # Extract structured data
        structured_data = extract_with_ai(raw_text)

        # Map field variations
        structured_data = map_field_variations(structured_data)

        # Validate and calculate premiums
        structured_data = validate_and_calculate_premiums(structured_data)

        # Validate and calculate package/liability
        structured_data = validate_and_calculate_package_liability(structured_data)

        # Debugging: Print final structured data before saving
        print(f"Final structured data for {os.path.basename(pdf_path)}:\n{structured_data}")

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
        df.drop(columns=["OD_PREMIUM_A", "OD_PREMIUM_C"], inplace=True, errors="ignore")

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