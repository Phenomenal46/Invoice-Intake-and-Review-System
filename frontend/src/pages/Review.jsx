import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { fetchDocument, approveDocument } from "../api";
import toast from "react-hot-toast";
import { formatDateDisplay, formatRupeeAmount } from "../utils/formatters";

function getPreviewKind(fileUrl) {
  if (!fileUrl) return "none";

  try {
    const pathname = new URL(fileUrl).pathname.toLowerCase();
    if (pathname.endsWith(".pdf")) return "pdf";
    if (pathname.match(/\.(png|jpe?g|gif|webp|bmp|svg)$/)) return "image";
    return "other";
  } catch {
    const lowerUrl = String(fileUrl).toLowerCase();
    if (lowerUrl.endsWith(".pdf")) return "pdf";
    if (lowerUrl.match(/\.(png|jpe?g|gif|webp|bmp|svg)$/)) return "image";
    return "other";
  }
}

export default function Review() {
  // 1. useParams looks at the URL (e.g., /review/12345) and grabs the '12345'
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);

  // 2. We use 'formData' to hold the AI's extracted data so the user can edit it
  const [formData, setFormData] = useState({
    vendor: "",
    invoice_number: "",
    invoice_date: "",
    total_amount: ""
  });

  const previewKind = getPreviewKind(doc?.metadata?.file_url);
  const hasRawTextPreview = !doc?.metadata?.file_url && typeof doc?.text === "string" && doc.text.trim().length > 0;

  // 3. useEffect runs automatically when the page loads. It fetches the document.
  useEffect(() => {
    async function loadDoc() {
      try {
        const data = await fetchDocument(id);
        setDoc(data.document);
        // Pre-fill the form with the AI's extracted data!
        setFormData({
          vendor: data.document.extracted.vendor || "",
          invoice_number: data.document.extracted.invoice_number || "",
          invoice_date: data.document.extracted.invoice_date || "",
          total_amount: data.document.extracted.total_amount || ""
        });
      } catch (error) {
        console.error("Error loading document:", error);
      } finally {
        setLoading(false);
      }
    }
    loadDoc();
  }, [id]);

  // 4. This updates our state when the user types in the form
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Loading workspace...</div>;
  if (!doc) return <div className="p-8 text-center text-red-500">Document not found.</div>;


  const handleApprove = async () => {
    if (isApproving) {
      return;
    }

    setIsApproving(true);

    try {
      // Problem: browser alerts interrupt the screen and feel abrupt.
      // Fix: use a toast so the message is visible but the user keeps context.
      await toast.promise(approveDocument(id, formData), {
        loading: "Saving the review...",
        success: "Invoice approved and saved.",
        error: (error) => error?.message || "Error saving document.",
      });
      navigate("/"); // Send the user back to the Dashboard
    } catch (error) {
      // The toast already shows the error, so we stay on the page and let the user fix the data.
    } finally {
      setIsApproving(false);
    }
  };


  return (
    <div className="h-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-4 flex flex-col gap-4 min-h-0">

      {/* Split Screen Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 flex-1 min-h-0">

        {/* LEFT SIDE: The Document Viewer */}
        <div className="bg-white p-3 sm:p-4 rounded-2xl shadow-sm border border-gray-200 min-h-0 flex items-center justify-center overflow-hidden">
          {doc.metadata?.file_url && previewKind === "pdf" && (
            <div className="w-full h-[72vh] min-h-105">
              <iframe
                src={`${doc.metadata.file_url}#toolbar=0&navpanes=0&scrollbar=0`}
                title="Uploaded PDF preview"
                className="w-full h-full rounded-lg border-0"
                allowFullScreen
              />
            </div>
          )}

          {doc.metadata?.file_url && previewKind === "image" && (
            <img
              src={doc.metadata.file_url}
              alt={doc.metadata?.title || "Uploaded Invoice"}
              className="max-w-full max-h-full object-contain rounded-lg shadow-sm"
            />
          )}

          {doc.metadata?.file_url && previewKind === "other" && (
            <div className="text-center text-gray-500 space-y-2">
              <p className="font-semibold">Preview not available for this file type.</p>
              <a className="text-blue-600 hover:underline" href={doc.metadata.file_url} target="_blank" rel="noreferrer">
                Open uploaded file
              </a>
            </div>
          )}

          {hasRawTextPreview && (
            <div className="h-full w-full overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Raw text preview</p>
              <pre className="whitespace-pre-wrap wrap-break-word font-sans">{doc.text}</pre>
            </div>
          )}

          {!doc.metadata?.file_url && !hasRawTextPreview && (
            <p className="text-center text-gray-400">No file or raw text preview is available.</p>
          )}
        </div>

        {/* RIGHT SIDE: The Data Form */}
        <div className="bg-white flex min-h-0 flex-col rounded-2xl border border-gray-200 shadow-sm">
          <div className="shrink-0 border-b border-gray-200 px-4 py-4 sm:px-5">
            <div className="flex justify-between">
              <h2 className="text-lg sm:text-2xl font-bold text-gray-800">Extracted Data</h2>
              <span className={`rounded-full px-4 py-2 font-bold ${doc.workflow_status === "Approved" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"}`}>
                {doc.workflow_status}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              Review the extracted values, then save only after you are confident the fields are correct.
            </p>
          </div>

          <form className="flex min-h-0 flex-1 flex-col">
            <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 sm:px-5 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">Vendor Name</label>
                <input
                  type="text"
                  name="vendor"
                  value={formData.vendor}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">Invoice Number</label>
                <input
                  type="text"
                  name="invoice_number"
                  value={formData.invoice_number}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">Date (dd/mm/yyyy)</label>
                <input
                  type="text"
                  name="invoice_date"
                  value={formData.invoice_date}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-semibold text-gray-700">Total Amount (₹)</label>
                <input
                  type="number"
                  name="total_amount"
                  value={formData.total_amount}
                  onChange={handleChange}
                  className="w-full rounded-lg border border-gray-300 p-2.5 outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <section className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                <h3 className="text-sm font-bold text-blue-800">AI Insights</h3>
                <div className="mt-3 space-y-2 text-sm text-blue-700">
                  <p><strong>Summary:</strong> {doc.llm.summary}</p>
                  <p><strong>Classification:</strong> {doc.llm.classification || "Unknown"}</p>
                  <p><strong>Invoice Date:</strong> {formatDateDisplay(formData.invoice_date)}</p>
                  <p><strong>Total Amount:</strong> {formatRupeeAmount(formData.total_amount)}</p>
                  <p><strong>Confidence:</strong> {(doc.llm.confidence * 100).toFixed(0)}%</p>
                </div>
              </section>
            </div>

            {/* Sticky footer keeps the primary action visible while the form content can still scroll. */}
            <div className="shrink-0 border-t border-gray-200 bg-white/90 p-4 backdrop-blur sm:p-5">
              <button
                type="button"
                disabled={loading || isApproving}
                className="w-full rounded-lg bg-green-600 px-4 py-3 font-bold text-white transition hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-400"
                onClick={handleApprove}
              >
                {isApproving ? "Saving..." : "Approve & Save"}
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}