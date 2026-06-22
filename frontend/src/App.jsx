import { useEffect, useState } from "react";
import { fetchAudit, fetchHistory, submitDocument } from "./api";

import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Review from "./pages/Review";

const emptyResult = {
  document: null,
};

export default function App() {
  return (
    <BrowserRouter>
      {/* This is a simple Navigation Bar that will show on every page */}
      <nav className="bg-white shadow-sm p-4 flex gap-6 border-b border-gray-200">
        <Link to="/" className="text-blue-600 font-semibold hover:text-blue-800">Dashboard</Link>
        <Link to="/upload" className="text-blue-600 font-semibold hover:text-blue-800">Upload</Link>
      </nav>

      {/* The Routes determine which page component to show based on the URL */}
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          {/* :id is a dynamic parameter. It allows URLs like /review/123 */}
          <Route path="/review/:id" element={<Review />} /> 
        </Routes>
      </div>
    </BrowserRouter>
  );
}