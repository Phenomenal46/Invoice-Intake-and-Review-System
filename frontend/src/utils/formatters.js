export function formatDateDisplay(value) {
  if (!value) return "-";

  // Problem: API dates arrive as ISO strings, but the UI needs one human format everywhere.
  // Fix: parse once here and always render dd/mm/yyyy so the dashboard and review page stay consistent.
  if (typeof value === "string" && /^\d{2}\/\d{2}\/\d{4}$/.test(value.trim())) {
    return value.trim();
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("en-GB").format(parsedDate);
}

export function formatRupeeAmount(value) {
  const numericValue = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(numericValue);
}