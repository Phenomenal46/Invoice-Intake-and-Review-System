import re

from app.schemas.document import ExtractedFields


def extract_fields(text: str) -> ExtractedFields:
    vendor_match = re.search(r"vendor\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    invoice_match = re.search(r"invoice\s*#?\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    date_match = re.search(r"date\s*[:\-]\s*([0-9\-\/]+)", text, re.IGNORECASE)
    total_match = re.search(r"total\s*[:\-]\s*([$0-9,\.]+)", text, re.IGNORECASE)

    total_amount = None
    if total_match:
        cleaned = total_match.group(1).replace("$", "").replace(",", "")
        try:
            total_amount = float(cleaned)
        except ValueError:
            total_amount = None

    return ExtractedFields(
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        invoice_number=invoice_match.group(1).strip() if invoice_match else None,
        invoice_date=date_match.group(1).strip() if date_match else None,
        total_amount=total_amount,
    )
