import re

# We import ExtractedFields to ensure our function returns the correct shape of data.
from app.schemas.document import ExtractedFields


def extract_fields(text: str) -> ExtractedFields:
    """
    This function uses 'Regular Expressions' (regex) to find specific patterns in text.
    It's like a super-powered ctrl+f (find).
    """
    
    # 1. Look for the vendor (company name). We search for 'vendor' followed by a colon or dash.
    vendor_match = re.search(r"vendor\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    
    # 2. Look for the invoice number.
    invoice_match = re.search(r"invoice\s*#?\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    
    # 3. Look for the date in formats like 2024-01-01 or 01/01/2024.
    date_match = re.search(r"date\s*[:\-]\s*([0-9\-\/]+)", text, re.IGNORECASE)
    
    # 4. Look for the total amount ($1,234.56).
    total_match = re.search(r"total\s*[:\-]\s*([$0-9,\.]+)", text, re.IGNORECASE)

    # We need to turn the 'total' string into a real floating-point number (float) for math.
    total_amount = None
    if total_match:
        # We remove symbols like '$' and ',' because Python's float() function only likes numbers and dots.
        cleaned = total_match.group(1).replace("$", "").replace(",", "")
        try:
            total_amount = float(cleaned)
        except ValueError:
            # If the text wasn't actually a number, we just set it to None.
            total_amount = None

    # We create and return a new instance (object) of ExtractedFields.
    return ExtractedFields(
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        invoice_number=invoice_match.group(1).strip() if invoice_match else None,
        invoice_date=date_match.group(1).strip() if date_match else None,
        total_amount=total_amount,
    )
