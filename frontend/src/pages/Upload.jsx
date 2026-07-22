import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { submitDocument } from '../api';

export default function UploadInvoice() {
  const [file, setFile] = useState(null);
  const [textInvoice, setTextInvoice] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Problem: a fast double-click could send two POST requests and trigger Gemini twice.
      // Fix: freeze the button immediately, then await one submission promise and route using the returned document id.
      const response = await toast.promise(submitDocument({ text: textInvoice, file }), {
        loading: 'Processing...',
        success: 'Document processed successfully.',
        error: (error) => error?.message || 'Submission failed.',
      });

      const documentId = response?.document?.id;
      if (documentId) {
        navigate(`/review/${documentId}`);
      }
    } catch {
      // The toast already explains the failure, so we stop here and let the user retry safely.
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-full bg-slate-100 flex items-center justify-center px-4 py-4">
      <div className="w-full max-w-2xl max-h-full bg-white shadow-xl rounded-2xl p-6 border border-slate-200 overflow-hidden">

        <h2 className="text-2xl sm:text-3xl font-bold text-center text-slate-800 mb-6">
          Invoice Intake
        </h2>

        <form onSubmit={handleUpload} className="space-y-5" aria-busy={isSubmitting}>

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
            disabled={isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 hover:cursor-pointer disabled:cursor-not-allowed disabled:bg-blue-400
                       text-white font-semibold
                       py-3 rounded-xl
                       transition-all duration-200
                       shadow-md hover:shadow-lg"
          >
            {isSubmitting ? 'Processing...' : 'Submit Invoice'}
          </button>

        </form>
      </div>
    </div>
  );
}