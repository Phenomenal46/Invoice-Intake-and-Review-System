import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

export default function PdfViewer({ fileUrl }) {
  const containerRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!fileUrl) {
      setError("No PDF file URL was provided.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    let loadingTask = null;
    let pdf = null;

    async function renderPdf() {
      setLoading(true);
      setError("");

      // Clear any previous pages.
      if (containerRef.current) {
        containerRef.current.innerHTML = "";
      }

      try {
        loadingTask = pdfjsLib.getDocument({
          url: fileUrl,
        });

        pdf = await loadingTask.promise;

        if (cancelled) return;

        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
          const page = await pdf.getPage(pageNumber);

          if (cancelled) return;

          const viewport = page.getViewport({ scale: 1.5 });

          const canvas = document.createElement("canvas");
          const context = canvas.getContext("2d");

          if (!context || !containerRef.current) {
            throw new Error("Unable to create PDF canvas.");
          }

          canvas.width = viewport.width;
          canvas.height = viewport.height;

          canvas.className =
            "block w-full h-auto mb-4 rounded-lg shadow-sm";

          containerRef.current.appendChild(canvas);

          await page.render({
            canvasContext: context,
            viewport,
          }).promise;
        }

        if (!cancelled) {
          setLoading(false);
        }
      } catch (err) {
        if (cancelled) return;

        console.error("PDF rendering failed:", err);
        setError("Unable to preview this PDF.");
        setLoading(false);
      }
    }

    renderPdf();

    return () => {
      cancelled = true;

      if (loadingTask) {
        loadingTask.destroy();
      }

      if (pdf) {
        pdf.destroy();
      }
    };
  }, [fileUrl]);

  return (
    <div className="relative h-full w-full overflow-hidden">
      {/* PDF pages */}
      <div
        ref={containerRef}
        className="h-full w-full overflow-auto bg-slate-100 p-4"
      />

      {/* Loading overlay */}
      {loading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white">
          <span className="text-gray-500">Loading PDF...</span>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white">
          <span className="text-red-500">{error}</span>
        </div>
      )}
    </div>
  );
}