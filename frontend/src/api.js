const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export function normalizeSearchInput(value) {
  return String(value ?? "").trim().replace(/\s+/g, " ");
}

function buildQueryString(params) {
  const queryParts = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    queryParts.set(key, String(value));
  });

  const queryString = queryParts.toString();
  return queryString ? `?${queryString}` : "";
}

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

export async function fetchHistory({ page = 1, pageSize = 5, search = "", sortBy = "created_at", sortDirection = "desc", signal } = {}) {
  const queryString = buildQueryString({
    page,
    page_size: pageSize,
    search: normalizeSearchInput(search),
    sort_by: sortBy,
    sort_direction: sortDirection,
  });

  const response = await fetch(`${API_URL}/documents${queryString}`, { signal });
  if (!response.ok) {
    throw new Error("Failed to load history");
  }
  return response.json();
}


// Fetch a single document by its ID
export async function fetchDocument(documentId) {
  const response = await fetch(`${API_URL}/documents/${documentId}`);
  if (!response.ok) {
    throw new Error("Failed to load document");
  }
  return response.json();
}


// Send the corrected data to the backend to be approved
export async function approveDocument(documentId, updatedData) {
  const response = await fetch(`${API_URL}/documents/${documentId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updatedData),
  });

  if (!response.ok) {
    throw new Error("Failed to approve document");
  }
  return response.json();
}