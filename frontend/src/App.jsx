import { useEffect, useState } from "react";

import { fetchAudit, fetchHistory, submitDocument } from "./api";

const emptyResult = {
  document: null,
};

function App() {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(emptyResult);
  const [history, setHistory] = useState([]);
  const [audit, setAudit] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory() {
    try {
      const data = await fetchHistory();
      setHistory(data.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await submitDocument({ text, file });
      setResult(data);
      await loadHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAudit(documentId) {
    try {
      const data = await fetchAudit(documentId);
      setAudit(data.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>AI Document Workflow</h1>
        <p>Upload a document or paste text to extract fields and get a workflow status.</p>
      </header>

      <section className="card">
        <h2>Submit Document</h2>
        <form onSubmit={handleSubmit} className="form">
          <label>
            Paste text
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Vendor: Acme Inc\nInvoice: INV-123\nDate: 2024-05-01\nTotal: $1200"
            />
          </label>
          <label>
            Or upload file
            <input
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? "Processing..." : "Submit"}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </section>

      <section className="grid">
        <div className="card">
          <h2>Latest Result</h2>
          {result.document ? (
            <div className="stack">
              <div><strong>Status:</strong> {result.document.workflow_status}</div>
              <div><strong>Summary:</strong> {result.document.llm.summary}</div>
              <div><strong>Classification:</strong> {result.document.llm.classification}</div>
              <div><strong>Confidence:</strong> {result.document.llm.confidence}</div>
              <div className="panel">
                <h3>Extracted Fields</h3>
                <pre>{JSON.stringify(result.document.extracted, null, 2)}</pre>
              </div>
              <div className="panel">
                <h3>Validation</h3>
                <pre>{JSON.stringify(result.document.validation, null, 2)}</pre>
              </div>
            </div>
          ) : (
            <p>No submissions yet.</p>
          )}
        </div>

        <div className="card">
          <h2>History</h2>
          <div className="history">
            {history.length === 0 && <p>No history yet.</p>}
            {history.map((doc) => (
              <button
                type="button"
                key={doc.id}
                className="history-item"
                onClick={() => handleAudit(doc.id)}
              >
                <span>{doc.workflow_status}</span>
                <span>{doc.extracted.vendor || "Unknown vendor"}</span>
                <span>{new Date(doc.created_at).toLocaleString()}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="card">
        <h2>Audit Log</h2>
        <div className="audit">
          {audit.length === 0 && <p>Select a history item to view audit events.</p>}
          {audit.map((entry) => (
            <div key={entry.id} className="audit-item">
              <strong>{entry.action}</strong>
              <span>{entry.detail}</span>
              <span>{new Date(entry.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default App;
