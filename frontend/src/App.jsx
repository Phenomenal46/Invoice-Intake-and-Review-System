import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Review from "./pages/Review";

export default function App() {

  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col overflow-hidden bg-slate-50 text-slate-900">
        {/* A fixed-height shell keeps the whole app inside one viewport, so the pages do not need vertical scrolling. */}
        <nav className="shrink-0 border-b border-slate-200 bg-white/90 backdrop-blur px-4 py-3 shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center gap-4 sm:gap-6">
            <div className="flex items-center gap-4">
              <Link to="/" className="font-semibold text-slate-700 transition hover:text-blue-700">Dashboard</Link>
              <Link to="/upload" className="font-semibold text-slate-700 transition hover:text-blue-700">Upload</Link>
            </div>
          </div>
        </nav>

        {/* The Routes live inside a single flex area so each page can fit the visible screen height. */}
        <main className="flex-1 min-h-0 overflow-hidden bg-slate-50 text-slate-700">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<Upload />} />
            {/* :id is a dynamic parameter. It allows URLs like /review/123 */}
            <Route path="/review/:id" element={<Review />} />
          </Routes>
        </main>
      </div>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 2800,
          style: {
            borderRadius: "12px",
            background: "#0f172a",
            color: "#f8fafc",
          },
        }}
      />
    </BrowserRouter>
  );
}