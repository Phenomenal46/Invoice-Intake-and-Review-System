from app.schemas.document import ExtractedFields, ValidationResult

# This is a list of strings. These names MUST match the fields in our ExtractedFields model.
REQUIRED_FIELDS = ["vendor", "invoice_number", "invoice_date", "total_amount"]


def validate_fields(fields: ExtractedFields) -> ValidationResult:
    """
    Checks if any of our important fields are empty or missing.
    """
    errors: list[str] = []

    # We loop through each 'required' name...
    for field_name in REQUIRED_FIELDS:
        # 'getattr' is a Python trick to get the value of a variable using its name as a string.
        # It's like asking: "Hey 'fields' object, give me the value inside your 'vendor' variable."
        value = getattr(fields, field_name)
        
        if value in (None, ""):
            errors.append(f"Missing required field: {field_name}")

    # We return a ValidationResult. 'is_valid' is True only if there are 0 errors.
    return ValidationResult(
        is_valid=len(errors) == 0, 
        errors=errors
    )
