import os
import pdfplumber
import pandas as pd
from .field_extraction import extract_with_ai


def extract_text_with_pdfplumber(pdf_path):
    """Extract raw text from a PDF using pdfplumber."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def process_pdf(pdf_path):
    """Process a PDF and extract structured data."""
    try:
        # Extract text from PDF
        raw_text = extract_text_with_pdfplumber(pdf_path)
        print(f"Debug: Extracted raw text from {pdf_path}.")

        # Extract structured data using AI
        structured_data = extract_with_ai(raw_text)
        print(f"Debug: Extracted structured data from {pdf_path}:\n{structured_data}")

        return structured_data
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None


def bulk_process_to_excel(input_folder, consolidated_excel_path):
    try:
        all_data = []  # Reset data for every bulk process call

        # Iterate over all PDF files in the temporary folder
        for file_name in os.listdir(input_folder):
            if file_name.endswith(".pdf"):
                pdf_path = os.path.join(input_folder, file_name)
                print(f"Processing {file_name}...")

                # Extract structured data from the PDF
                structured_data = process_pdf(pdf_path)
                if structured_data:
                    structured_data["source_file"] = file_name  # Add source file name for reference
                    all_data.append(structured_data)

        if all_data:
            # Combine extracted data into a DataFrame
            df = pd.DataFrame(all_data)

            # Save extracted data to an Excel file
            absolute_output_path = os.path.abspath(consolidated_excel_path)
            df.to_excel(absolute_output_path, index=False)
            print(f"All data successfully exported to {absolute_output_path}")
        else:
            print("No valid data extracted from PDFs. Please check the input folder.")

    except Exception as e:
        print(f"Error in bulk processing to Excel: {e}")