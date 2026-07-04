import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHistory } from "../api";

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
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-800">Command Center</h1>
        <Link to="/upload" className="bg-blue-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-blue-700 transition shadow-sm">
          + New Invoice
        </Link>
      </div>

      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-bold text-gray-500 uppercase tracking-wider">Total Processed</p>
          <p className="text-4xl font-black text-gray-800 mt-2">{totalInvoices}</p>
        </div>
        
        <div className="p-6 rounded-xl border border-yellow-200 shadow-sm bg-yellow-50">
          <p className="text-sm font-bold text-yellow-700 uppercase tracking-wider">Needs Review</p>
          <p className="text-4xl font-black text-yellow-600 mt-2">{pendingReview}</p>
        </div>

        <div className="p-6 rounded-xl border border-green-200 shadow-sm bg-green-50">
          <p className="text-sm font-bold text-green-700 uppercase tracking-wider">Value Approved</p>
          <p className="text-4xl font-black text-green-600 mt-2">
            ${totalApprovedValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
          </p>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-4 bg-gray-50 border-b border-gray-200 font-bold text-gray-600 text-sm grid grid-cols-4">
          <div>Vendor</div>
          <div>Date</div>
          <div>Amount</div>
          <div>Status</div>
        </div>
        
        {history.length === 0 && (
          <div className="p-8 text-center text-gray-500">No invoices processed yet.</div>
        )}

        {history.map((doc) => (
          <Link 
            to={`/review/${doc.id}`} 
            key={doc.id}
            className="grid grid-cols-4 p-4 border-b border-gray-100 hover:bg-blue-50 items-center transition text-sm"
          >
            <div className="font-bold text-gray-800">{doc.extracted.vendor || "Unknown Vendor"}</div>
            <div className="text-gray-500">{new Date(doc.created_at).toLocaleDateString()}</div>
            <div className="font-medium text-gray-700">${(doc.extracted.total_amount || 0).toFixed(2)}</div>
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
  );
}