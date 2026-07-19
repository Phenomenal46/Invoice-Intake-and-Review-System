import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHistory } from "../api";
import { formatDateDisplay, formatRupeeAmount } from "../utils/formatters";

export default function Dashboard() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory().then((data) => setHistory(data.items || []));
  }, []);

  // Calculate some basic business metrics using standard JavaScript
  const totalInvoices = history.length;
  const pendingReview = history.filter(doc => doc.workflow_status === "Needs Review").length;
  
  // Add up all the money from approved invoices
  const totalApprovedValue = history
    .filter(doc => doc.workflow_status === "Approved")
    .reduce((sum, doc) => sum + (doc.extracted.total_amount || 0), 0);

  return (
    <div className="h-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 flex flex-col gap-4 min-h-0">
      <div className="flex justify-between items-start gap-4 shrink-0">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.24em] text-slate-500">Document workflow</p>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 mt-1">Command Center</h1>
        </div>
        <Link to="/upload" className="bg-blue-600 text-white px-4 sm:px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition shadow-sm whitespace-nowrap">
          + New Invoice
        </Link>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-bold text-gray-500 uppercase tracking-wider">Total Processed</p>
          <p className="text-3xl font-black text-gray-800 mt-2">{totalInvoices}</p>
        </div>
        
        <div className="p-4 sm:p-5 rounded-xl border border-yellow-200 shadow-sm bg-yellow-50">
          <p className="text-sm font-bold text-yellow-700 uppercase tracking-wider">Needs Review</p>
          <p className="text-3xl font-black text-yellow-600 mt-2">{pendingReview}</p>
        </div>

        <div className="p-4 sm:p-5 rounded-xl border border-green-200 shadow-sm bg-green-50">
          <p className="text-sm font-bold text-green-700 uppercase tracking-wider">Value Approved</p>
          <p className="text-3xl font-black text-green-600 mt-2">
            {formatRupeeAmount(totalApprovedValue)}
          </p>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col flex-1 min-h-0">
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 font-bold text-gray-600 text-sm grid grid-cols-4 gap-3 shrink-0">
          <div>Vendor</div>
          <div>Date</div>
          <div>Amount</div>
          <div>Status</div>
        </div>
        
        {history.length === 0 && (
          <div className="p-6 text-center text-gray-500 flex-1 flex items-center justify-center">No invoices processed yet.</div>
        )}

        <div className="overflow-hidden flex-1 min-h-0">
        {history.map((doc) => (
          <Link 
            to={`/review/${doc.id}`} 
            key={doc.id}
            className="grid grid-cols-4 gap-3 px-4 py-3 border-b border-gray-100 hover:bg-blue-50 items-center transition text-sm"
          >
            <div className="font-bold text-gray-800">{doc.extracted.vendor || "Unknown Vendor"}</div>
            <div className="text-gray-500">{formatDateDisplay(doc.created_at)}</div>
            <div className="font-medium text-gray-700">{formatRupeeAmount(doc.extracted.total_amount)}</div>
            <div>
              <span className={`px-3 py-1 text-xs font-bold rounded-full ${
                doc.workflow_status === "Approved" ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"
              }`}>
                {doc.workflow_status}
              </span>
            </div>
          </Link>
        ))}
        </div>
      </div>
    </div>
  );
}