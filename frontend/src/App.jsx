import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Review from "./pages/Review";

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col bg-slate-50 overflow-hidden">
        {/* A fixed-height shell keeps the whole app inside one viewport, so the pages do not need vertical scrolling. */}
        <nav className="shrink-0 bg-white/90 backdrop-blur border-b border-slate-200 px-4 py-3 flex gap-4 sm:gap-6 shadow-sm">
          <Link to="/" className="text-slate-700 font-semibold hover:text-blue-700 transition">Dashboard</Link>
          <Link to="/upload" className="text-slate-700 font-semibold hover:text-blue-700 transition">Upload</Link>
        </nav>

        {/* The Routes live inside a single flex area so each page can fit the visible screen height. */}
        <main className="flex-1 min-h-0 overflow-hidden">
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