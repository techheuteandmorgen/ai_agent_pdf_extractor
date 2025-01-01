import re

def refine_extracted_value(key, value):
    """Refine extracted values based on key-specific logic."""
    if key == "Policy Number":
        match = re.search(r'\b\d{10,}\b', value)
        return match.group(0) if match else "Not Found"
    elif key == "Customer Name":
        match = re.search(r'(Insured|Customer Name|Proposer Name)[:\-]?\s*(.*?)(?=\s+(IMD|Policy|Address|Contact|$))', value, re.IGNORECASE | re.DOTALL)
        return match.group(2).strip() if match else "Not Found"
    return value

def normalize_and_map_text(raw_text, key_value_data):
    """Normalize and map text to structured data fields."""
    structured_data = {}

    # Define regex patterns for fields
    fields = {
        "Policy Number": r"(Policy(?:Ref)?(?:\s*No\.?)?|Policy Numer|Policy cum Certificate Number|Policy/Certificate No)\s*[:\-]?\s*(.+?)(?=\s+[A-Za-z]*:|$)",
        "Customer Name": r"(Insured|Customer Name|Proposer Name)\s*[:\-]?\s*(.+?)(?=\s+[A-Za-z]*:|$)",
    }

    # Extract with regex
    for field, pattern in fields.items():
        match = re.search(pattern, raw_text, re.IGNORECASE)
        structured_data[field] = match.group(2).strip() if match else "Not Found"

    # Fallback to key-value mapping
    for field in fields.keys():
        if structured_data.get(field) == "Not Found":
            value = key_value_data.get(field.lower(), "Not Found")
            structured_data[field] = value if value != "Not Found" else "Not Found"

    return structured_data