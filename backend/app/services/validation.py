from app.schemas.document import ExtractedFields, ValidationResult


REQUIRED_FIELDS = ["vendor", "invoice_number", "invoice_date", "total_amount"]


def validate_fields(fields: ExtractedFields) -> ValidationResult:
    errors: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if getattr(fields, field_name) in (None, ""):
            errors.append(f"Missing required field: {field_name}")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
