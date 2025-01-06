def clean_numeric_field(value):
    """Remove currency symbols, commas, and whitespace from a numeric field."""
    try:
        if isinstance(value, str):
            return float(value.replace('₹', '').replace(',', '').strip())
        return float(value)
    except ValueError:
        return 0.0  