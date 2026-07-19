import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { fetchDocument, approveDocument } from "../api";
import toast from "react-hot-toast";
import { formatDateDisplay, formatRupeeAmount } from "../utils/formatters";

export default function Review() {
  // 1. useParams looks at the URL (e.g., /review/12345) and grabs the '12345'
  const { id } = useParams();
  const navigate = useNavigate();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);

  // 2. We use 'formData' to hold the AI's extracted data so the user can edit it
  const [formData, setFormData] = useState({
    vendor: "",
    invoice_number: "",
    invoice_date: "",
    total_amount: ""
  });

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
    }
  };


  return (
    <div className="h-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 flex flex-col gap-4 min-h-0">
      {/* Header Area */}
      <div className="flex justify-between items-center gap-4 shrink-0">
        <div>
          <Link to="/" className="text-blue-500 hover:underline mb-2 inline-block">&larr; Back to Dashboard</Link>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-800">Review Invoice</h1>
        </div>
        <span className={`px-4 py-2 rounded-full font-bold ${doc.workflow_status === "Approved" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
          }`}>
          {doc.workflow_status}
        </span>
      </div>

      {/* Split Screen Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 flex-1 min-h-0">

        {/* LEFT SIDE: The Document Viewer */}
        <div className="bg-white p-3 sm:p-4 rounded-2xl shadow-sm border border-gray-200 min-h-0 flex items-center justify-center overflow-hidden">
          {doc.metadata?.file_url ? (
            <img
              src={doc.metadata.file_url}
              alt="Uploaded Invoice"
              className="max-w-full max-h-full object-contain rounded-lg shadow-sm"
            />
          ) : (
            <p className="text-gray-400">No image available (Text only upload)</p>
          )}
        </div>

        {/* RIGHT SIDE: The Data Form */}
        <div className="bg-white p-4 sm:p-5 rounded-2xl shadow-sm border border-gray-200 flex flex-col min-h-0">
          <h2 className="text-lg sm:text-xl font-bold text-gray-800 mb-4 shrink-0">Extracted Data</h2>

          <form className="space-y-3 flex-1 min-h-0 overflow-hidden">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Vendor Name</label>
              <input
                type="text"
                name="vendor"
                value={formData.vendor}
                onChange={handleChange}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Invoice Number</label>
              <input
                type="text"
                name="invoice_number"
                value={formData.invoice_number}
                onChange={handleChange}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Date (dd/mm/yyyy)</label>
              <input
                type="text"
                name="invoice_date"
                value={formData.invoice_date}
                onChange={handleChange}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Total Amount (₹)</label>
              <input
                type="number"
                name="total_amount"
                value={formData.total_amount}
                onChange={handleChange}
                className="w-full p-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            {/* Action Buttons */}
            <div className="pt-3 mt-3 border-t border-gray-100 flex gap-4 shrink-0">
              <button
                type="button"
                className="flex-1 bg-green-600 text-white font-bold py-2.5 rounded-lg hover:bg-green-700 transition"
                onClick={handleApprove}
              >
                Approve & Save
              </button>
            </div>
          </form>

          {/* AI Insights Panel */}
          <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100 shrink-0">
            <h3 className="text-sm font-bold text-blue-800 mb-2">✨ AI Insights</h3>
            <p className="text-sm text-blue-700 mb-2"><strong>Summary:</strong> {doc.llm.summary}</p>
            <p className="text-sm text-blue-700 mb-2"><strong>Classification:</strong> {doc.llm.classification || "Unknown"}</p>
            <p className="text-sm text-blue-700 mb-2"><strong>Invoice Date:</strong> {formatDateDisplay(formData.invoice_date)}</p>
            <p className="text-sm text-blue-700"><strong>Total Amount:</strong> {formatRupeeAmount(formData.total_amount)}</p>
            <p className="text-sm text-blue-700 mt-2"><strong>Confidence:</strong> {(doc.llm.confidence * 100).toFixed(0)}%</p>
          </div>
        </div>

      </div>
    </div>
  );
}