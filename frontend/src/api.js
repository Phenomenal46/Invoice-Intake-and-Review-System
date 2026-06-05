const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function submitDocument({ text, file }) {
  const form = new FormData();
  if (text) form.append("text", text);
  if (file) form.append("file", file);
  if(!text && !file) {
    throw new Error("Please provide text or a file");
  }
  const response = await fetch(`${API_URL}/documents`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Request failed");
  }

  return response.json();
}

export async function fetchHistory() {
  const response = await fetch(`${API_URL}/documents`);
  if (!response.ok) {
    throw new Error("Failed to load history");
  }
  return response.json();
}

export async function fetchAudit(documentId) {
  const response = await fetch(`${API_URL}/documents/${documentId}/audit`);
  if (!response.ok) {
    throw new Error("Failed to load audit log");
  }
  return response.json();
}
