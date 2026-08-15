import { useEffect, useRef, useState } from "react";
import * as pdfjsLib from "pdfjs-dist";
import pdfWorker from "pdfjs-dist/build/pdf.worker.min.mjs?url";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

export default function PdfViewer({ fileUrl }) {
  const containerRef = useRef(null);
  const renderTaskRef = useRef(null);

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
          if (cancelled) return;

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

          const renderTask = page.render({
            canvasContext: context,
            viewport,
          });

          renderTaskRef.current = renderTask;

          try {
            await renderTask.promise;
          } finally {
            if (renderTaskRef.current === renderTask) {
              renderTaskRef.current = null;
            }
          }
        }

        if (!cancelled) {
          setLoading(false);
        }
      } catch (err) {
        if (cancelled) return;

        // PDF.js can reject when a render is cancelled during navigation.
        if (err?.name === "RenderingCancelledException") {
          return;
        }

        console.error("PDF rendering failed:", err);
        setError("Unable to preview this PDF.");
        setLoading(false);
      }
    }

    renderPdf();

    return () => {
      cancelled = true;

      // Cancel the currently active page render first.
      if (renderTaskRef.current) {
        try {
          renderTaskRef.current.cancel();
        } catch (err) {
          console.debug("PDF render cancellation:", err);
        }

        renderTaskRef.current = null;
      }

      // Destroy the loading task safely.
      if (loadingTask) {
        loadingTask.destroy().catch(() => {});
      }
    };
  }, [fileUrl]);

  return (
    <div className="relative h-full w-full overflow-hidden">
      <div
        ref={containerRef}
        className="h-full w-full overflow-auto bg-slate-100 p-4"
      />

      {loading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white">
          <span className="text-gray-500">Loading PDF...</span>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-white">
          <span className="text-red-500">{error}</span>
        </div>
      )}
    </div>
  );
}