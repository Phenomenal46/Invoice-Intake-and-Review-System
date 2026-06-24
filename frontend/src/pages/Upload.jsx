import React, { useState } from 'react';
import { submitDocument } from '../api';

export default function UploadInvoice() {
  const [file, setFile] = useState(null);
  const [textInvoice, setTextInvoice] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    const res = await submitDocument({ text: textInvoice, file });
    console.log(res);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center px-4">
      <div className="w-full max-w-2xl bg-white shadow-xl rounded-2xl p-8 border border-slate-200">

        <h2 className="text-3xl font-bold text-center text-slate-800 mb-8">
          Invoice Intake
        </h2>

        <form onSubmit={handleUpload} className="space-y-6">

          {/* File Input */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Upload Invoice File
            </label>

            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-600
                         file:mr-4 file:py-2 file:px-4
                         file:rounded-lg file:border-0
                         file:bg-blue-600 file:text-white
                         file:font-medium
                         hover:file:bg-blue-700
                         cursor-pointer"
            />

            {file && (
              <p className="mt-3 text-green-600 text-sm font-medium">
                ✓ Selected: {file.name}
              </p>
            )}
          </div>

          {/* Divider */}
          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-slate-300"></div>
            <span className="text-slate-500 text-sm font-medium">OR</span>
            <div className="h-px flex-1 bg-slate-300"></div>
          </div>

          {/* Text Input */}
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Paste Invoice Text / Data
            </label>

            <textarea
              rows="8"
              placeholder="Paste raw invoice text here..."
              value={textInvoice}
              onChange={(e) => setTextInvoice(e.target.value)}
              className="w-full rounded-xl border border-slate-300
                         px-4 py-3 text-slate-700
                         focus:outline-none
                         focus:ring-2 focus:ring-blue-500
                         focus:border-blue-500
                         resize-none"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700
                       text-white font-semibold
                       py-3 rounded-xl
                       transition-all duration-200
                       shadow-md hover:shadow-lg"
          >
            Submit Invoice
          </button>

        </form>
      </div>
    </div>
  );
}