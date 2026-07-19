from datetime import datetime


_KNOWN_DATE_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
)


def normalize_date_to_ddmmyyyy(raw_date: str | None) -> str | None:
    if raw_date is None:
        return None

    cleaned_date = raw_date.strip()
    if not cleaned_date:
        return cleaned_date

    # Problem: Gemini and manual edits can send the same date in different styles.
    # Fix: normalize once here so the backend stores and returns one stable format.
    for date_format in _KNOWN_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned_date, date_format).strftime("%d/%m/%Y")
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(cleaned_date.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return cleaned_date