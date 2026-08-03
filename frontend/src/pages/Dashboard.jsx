import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchHistory, normalizeSearchInput } from "../api";
import { formatDateDisplay, formatRupeeAmount } from "../utils/formatters";

function getDisplayTitle(documentRecord) {
  // Problem: older text-only documents may not have a file name, so the dashboard needs a safe label.
  // Fix: prefer the stored title, then the file name, and finally a text-entry fallback with the save date.
  const fallbackTitle = "Raw Text Entry";
  const storedTitle = documentRecord?.metadata?.title;

  if (typeof storedTitle === "string" && storedTitle.startsWith("Raw Text Entry")) {
    return fallbackTitle;
  }

  return storedTitle || documentRecord?.metadata?.filename || fallbackTitle;
}

export default function Dashboard() {
  const [history, setHistory] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);
  const [totalPages, setTotalPages] = useState(0);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchDraft, setSearchDraft] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    // Problem: firing a network request on every keystroke makes the UI noisy and wastes calls.
    // Fix: wait briefly before promoting the search box text into the real server query.
    const normalizedSearch = normalizeSearchInput(searchDraft);

    if (normalizedSearch === searchQuery) {
      return;
    }

    const debounceId = window.setTimeout(() => {
      setPage(1);
      setSearchQuery(normalizedSearch);
    }, 300);

    return () => window.clearTimeout(debounceId);
  }, [searchDraft, searchQuery]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDocuments() {
      setLoading(true);
      setErrorMessage("");

      try {
        const response = await fetchHistory({
          page,
          pageSize,
          search: searchQuery,
          signal: controller.signal,
        });

        setHistory(response.items || []);
        setTotalPages(response.total_pages || 0);
        setTotalItems(response.total_items || 0);
        setPage(response.page || 1);
      } catch (error) {
        if (error.name !== "AbortError") {
          setErrorMessage("Failed to load documents. Please try again.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadDocuments();

    return () => controller.abort();
  }, [page, pageSize, searchQuery]);

  const pendingReview = history.filter(doc => doc.workflow_status === "Needs Review").length;
  
  // Add up all the money from approved invoices
  const totalApprovedValue = history
    .filter(doc => doc.workflow_status === "Approved")
    .reduce((sum, doc) => sum + (doc.extracted.total_amount || 0), 0);

  const totalPagesLabel = totalPages === 0 ? 0 : page;

  return (
    <div className="h-auto max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6 flex flex-col gap-4 min-h-0">
      {/* Analytics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-gray-200 shadow-sm">
          <p className="text-sm font-bold text-gray-500 uppercase tracking-wider">Total Processed</p>
          <p className="text-3xl font-black text-gray-800 mt-2">{totalItems}</p>
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

      {/* The controls row sits above the table so the primary actions are easy to find. */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between shrink-0">
        <div className="flex flex-1 items-center gap-3 min-w-0">
          <label className="sr-only" htmlFor="dashboard-search">
            Search invoices
          </label>
          <input
            id="dashboard-search"
            type="search"
            value={searchDraft}
            onChange={(event) => setSearchDraft(event.target.value)}
            placeholder="Search by title, filename, or vendor"
            className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400  focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <Link
          to="/upload"
          className="inline-flex shrink-0 items-center justify-center rounded-lg bg-blue-600 px-4 sm:px-6 py-3 font-bold text-white shadow-sm transition hover:bg-blue-700"
        >
          + New Invoice
        </Link>
      </div>

      {/* Recent Documents Table */}
      <div className="flex flex-1 min-h-0 flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="flex-1 min-h-0 overflow-x-auto overflow-y-auto">
          <table className="min-w-full table-fixed border-collapse">
            <thead className="sticky top-0 z-10 bg-white">
              <tr className="border-b border-gray-200 text-left text-sm font-medium text-gray-500">
                <th scope="col" className="px-4 py-4">Document</th>
                <th scope="col" className="px-4 py-4">Date</th>
                <th scope="col" className="px-4 py-4">Amount</th>
                <th scope="col" className="px-4 py-4">Status</th>
              </tr>
            </thead>

            <tbody>
              {loading && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
                    Loading documents...
                  </td>
                </tr>
              )}

              {!loading && errorMessage && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-red-600">
                    {errorMessage}
                  </td>
                </tr>
              )}

              {!loading && !errorMessage && history.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
                    No invoices processed yet.
                  </td>
                </tr>
              )}

              {!loading && !errorMessage && history.length > 0 && history.map((doc) => {
                const isApproved = doc.workflow_status === "Approved";
                const statusBadgeClasses = isApproved
                  ? "bg-green-100 text-green-700"
                  : "bg-yellow-100 text-yellow-700";

                const documentTitle = getDisplayTitle(doc);
                const vendorName = doc.extracted.vendor || "Vendor unknown";
                const formattedDate = formatDateDisplay(doc.created_at);
                const formattedAmount = formatRupeeAmount(doc.extracted.total_amount);

                return (
                  <tr key={doc.id} className="h-14 border-b border-gray-100 transition-colors duration-200 hover:bg-gray-100">
                    <td className="px-4 py-3 align-middle">
                      <Link to={`/review/${doc.id}`} className="block min-w-0">
                        <div className="truncate font-semibold text-gray-900" title={documentTitle}>
                          {documentTitle}
                        </div>
                        <div className="truncate text-xs text-gray-500" title={vendorName}>
                          {vendorName}
                        </div>
                      </Link>
                    </td>
                    <td className="px-4 py-3 align-middle text-sm text-gray-600">
                      <span className="block truncate" title={formattedDate}>{formattedDate}</span>
                    </td>
                    <td className="px-4 py-3 align-middle text-sm font-medium text-gray-800">
                      <span className="block truncate" title={formattedAmount}>{formattedAmount}</span>
                    </td>
                    <td className="px-4 py-3 align-middle">
                      <span className={`inline-flex min-w-24 items-center justify-center rounded-full px-3 py-1 text-xs font-semibold ${statusBadgeClasses}`}>
                        {doc.workflow_status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination keeps the table readable without changing the server-side paging behavior. */}
        <div className="flex w-full items-center justify-end gap-3 border-t border-gray-200 bg-white px-4 py-4 text-sm text-slate-600">
          <div className="flex flex-wrap items-center justify-end gap-3 sm:flex-nowrap">
            <label className="flex items-center gap-2 mr-5 whitespace-nowrap">
              <span>Rows per page</span>
              <select
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
                className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800 outline-none"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
              </select>
            </label>

            <span className="whitespace-nowrap font-semibold text-slate-700">
              Page {totalPagesLabel} of {totalPages}
            </span>

            <button
              type="button"
              onClick={() => setPage(1)}
              disabled={!page || page <= 1}
              aria-label="First page"
              title="First page"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-2xl font-semibold text-slate-800 transition-colors duration-150 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              &laquo;
            </button>
            <button
              type="button"
              onClick={() => setPage((currentPage) => Math.max(currentPage - 1, 1))}
              disabled={!page || page <= 1}
              aria-label="Previous page"
              title="Previous page"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-2xl font-semibold text-slate-800 transition-colors duration-150 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              &lsaquo;
            </button>
            <button
              type="button"
              onClick={() => setPage((currentPage) => Math.min(currentPage + 1, totalPages || 1))}
              disabled={!totalPages || page >= totalPages}
              aria-label="Next page"
              title="Next page"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-2xl font-semibold text-slate-800 transition-colors duration-150 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              &rsaquo;
            </button>
            <button
              type="button"
              onClick={() => setPage(totalPages || 1)}
              disabled={!totalPages || page >= totalPages}
              aria-label="Last page"
              title="Last page"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-300 bg-white text-2xl font-semibold text-slate-800 transition-colors duration-150 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              &raquo;
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}