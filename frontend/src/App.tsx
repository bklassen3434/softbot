import { useEffect, useRef, useState } from "react";

type Pitch = {
  id: number;
  game_date: string;
  pitcher: string;
  batter: string;
  pitch_type: string;
  result: string;
};

const API = import.meta.env.VITE_API_BASE_URL;

export default function App() {

  const preRef = useRef<HTMLPreElement | null>(null);
  // --- Ask DB (LLM) state ---
  const [nlQ, setNlQ] = useState("");
  const [nlAns, setNlAns] = useState<any>(null);
  const [nlErr, setNlErr] = useState("");
  const [nlLoading, setNlLoading] = useState(false);

  // --- Ask Freeform DB (LLM) state ---
  const [freeQ, setFreeQ] = useState("");
  const [freeAns, setFreeAns] = useState<any>(null);
  const [freeErr, setFreeErr] = useState("");
  const [freeLoading, setFreeLoading] = useState(false);

  // --- existing upload/table state ---
  const [file, setFile] = useState<File | null>(null);
  const [uploadMsg, setUploadMsg] = useState<string>("");
  const [pitches, setPitches] = useState<Pitch[]>([]);
  const [loadingPitches, setLoadingPitches] = useState(false);

  useEffect(() => { if (preRef.current) preRef.current.scrollTop = preRef.current.scrollHeight; }, [nlAns]);
  useEffect(() => { refreshPitches(); /* on mount */ }, []);

  // --- existing upload handlers ---
  function onPickFile(e: React.ChangeEvent<HTMLInputElement>) { const f = e.target.files?.[0] ?? null; setFile(f); setUploadMsg(""); }
  async function handleUpload() {
    if (!file) return;
    setUploadMsg("Uploading...");
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(`${API}/pitches/upload-csv`, { method: "POST", body: fd });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setUploadMsg(`Inserted ${data.inserted} rows ✅`); setFile(null); refreshPitches();
    } catch (err: any) {
      setUploadMsg(`Upload failed: ${String(err?.message || err)}. Ensure headers are exactly game_date,pitcher,batter,pitch_type,result`);
    }
  }

  // --- existing table fetch ---
  async function refreshPitches() {
    setLoadingPitches(true);
    try { const res = await fetch(`${API}/pitches?limit=100`); const data = await res.json(); setPitches(data); }
    finally { setLoadingPitches(false); }
  }

  async function askDbLLM() {
  setNlAns(null); setNlErr(""); setNlLoading(true);
  try {
    const res = await fetch(`${API}/sql/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: nlQ }),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    setNlAns(data);
  } catch (e: any) {
    setNlErr(`Error: ${String(e?.message || e)}`);
  } finally {
    setNlLoading(false);
  }
  }


  async function askFreeform() {
    setFreeAns(null); setFreeErr(""); setFreeLoading(true);
    try {
      const res = await fetch(`${API}/sql/freeform/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: freeQ }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setFreeAns(data);
    } catch (e: any) {
      setFreeErr(`Error: ${String(e?.message || e)}`);
    } finally {
      setFreeLoading(false);
    }
    }

  return (
    <main style={{ fontFamily: "Inter, system-ui, sans-serif", padding: 24, maxWidth: 1000, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, marginBottom: 12 }}>Softbot (Beta)</h1>
      <p style={{ color: "#555", marginBottom: 24 }}>Upload your data and ask questions about it!</p>

      {/* --- Ask DB-LLM --- */}
      <section style={card}>
        <h2 style={h2}>Ask LLM!</h2>
        <p style={muted}>Type a natural-language question. The LLM will query the database and answer it!</p>
        <textarea value={nlQ} onChange={(e)=>setNlQ(e.target.value)} rows={3} style={textarea} placeholder='e.g., "What is the whiff rate for Smith?" or "Show recent pitches for Smith"' />
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button onClick={askDbLLM} disabled={nlLoading || !nlQ.trim()} style={primaryBtn}>{nlLoading ? "Thinking..." : "Ask DB"}</button>
        </div>
        {nlErr && <div style={{ color:"#b00020", fontSize:14 }}>{nlErr}</div>}

        {nlAns && (
          <div style={{ fontSize: 14 }}>
            <div style={{ marginBottom: 8 }}>
              <b>Chosen:</b> {nlAns.chosen?.template} &nbsp;
              <b>Params:</b> {JSON.stringify(nlAns.chosen?.params)} &nbsp;
              <span style={{ color:"#666" }}>(source: {nlAns.chosen?.source})</span>
            </div>

            {/* stat result */}
            {nlAns.result?.result && (
              <div>
                <div><b>Pitcher:</b> {nlAns.result.result.pitcher}</div>
                <div><b>Swings:</b> {nlAns.result.result.swings}</div>
                <div><b>Whiffs:</b> {nlAns.result.result.whiffs}</div>
                <div><b>Whiff Rate:</b> {nlAns.result.result.whiff_rate === null ? "—" : (nlAns.result.result.whiff_rate * 100).toFixed(1) + "%"}</div>
              </div>
            )}

            {/* rows result */}
            {Array.isArray(nlAns.result?.rows) && (
              <div style={{ overflowX: "auto", marginTop: 8 }}>
                <table style={table}>
                  <thead>
                    <tr><th style={th}>ID</th><th style={th}>Date</th><th style={th}>Pitcher</th><th style={th}>Batter</th><th style={th}>Type</th><th style={th}>Result</th></tr>
                  </thead>
                  <tbody>
                    {nlAns.result.rows.length === 0 ? (
                      <tr><td colSpan={6} style={{ padding: 12, textAlign: "center", color: "#666" }}>No rows.</td></tr>
                    ) : nlAns.result.rows.map((r:any)=>(
                      <tr key={r.id}>
                        <td style={td}>{r.id}</td><td style={td}>{r.game_date}</td><td style={td}>{r.pitcher}</td>
                        <td style={td}>{r.batter}</td><td style={td}>{r.pitch_type}</td><td style={td}>{r.result}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>



    <section style={card}>
        <h2 style={h2}>Ask DB (LLM writes SQL)</h2>
        <p style={muted}>Model proposes SQL; server validates, rewrites, and executes safely.</p>
        <textarea value={freeQ} onChange={(e)=>setFreeQ(e.target.value)} rows={3} style={textarea} placeholder='e.g., "Show the last 5 pitches for Smith"' />
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button onClick={askFreeform} disabled={freeLoading || !freeQ.trim()} style={primaryBtn}>
            {freeLoading ? "Thinking..." : "Ask (Freeform SQL)"}
          </button>
        </div>
        {freeErr && <div style={{ color:"#b00020", fontSize:14 }}>{freeErr}</div>}
        {freeAns && (
          <div style={{ fontSize: 14 }}>
            <div><b>Proposed SQL:</b> <code>{freeAns.proposed_sql}</code></div>
            <div><b>Safe SQL:</b> <code>{freeAns.safe_sql}</code></div>
            <div style={{ marginTop: 8 }}>
              <b>Rows:</b>
              <div style={{ overflowX: "auto", marginTop: 6 }}>
                <table style={table}>
                  <thead>
                    <tr><th style={th}>ID</th><th style={th}>Date</th><th style={th}>Pitcher</th><th style={th}>Batter</th><th style={th}>Type</th><th style={th}>Result</th></tr>
                  </thead>
                  <tbody>
                    {Array.isArray(freeAns.rows) && freeAns.rows.length > 0 ? freeAns.rows.map((r:any)=>(
                      <tr key={r.id}>
                        <td style={td}>{r.id}</td><td style={td}>{r.game_date}</td><td style={td}>{r.pitcher}</td>
                        <td style={td}>{r.batter}</td><td style={td}>{r.pitch_type}</td><td style={td}>{r.result}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan={6} style={{ padding: 12, textAlign: "center", color: "#666" }}>No rows.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </section>





      {/* --- Upload CSV --- */}
      <section style={card}>
        <h2 style={h2}>Upload CSV</h2>
        <p style={muted}>Headers: <code>game_date,pitcher,batter,pitch_type,result</code></p>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
          <input type="file" accept=".csv" onChange={onPickFile} />
          <button onClick={handleUpload} disabled={!file} style={primaryBtn}>Upload</button>
          {file && <span style={{ fontSize: 12, color: "#444" }}>Selected: {file.name}</span>}
        </div>
        {uploadMsg && <div style={{ fontSize: 14 }}>{uploadMsg}</div>}
      </section>

      {/* --- Recent Pitches --- */}
      <section style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={h2}>Recent Pitches</h2>
          <button onClick={refreshPitches} disabled={loadingPitches} style={secondaryBtn}>{loadingPitches ? "Refreshing..." : "Refresh"}</button>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={table}>
            <thead>
              <tr><th style={th}>ID</th><th style={th}>Date</th><th style={th}>Pitcher</th><th style={th}>Batter</th><th style={th}>Type</th><th style={th}>Result</th></tr>
            </thead>
            <tbody>
              {pitches.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: 12, textAlign: "center", color: "#666" }}>No data yet. Upload a CSV above.</td></tr>
              ) : pitches.map((p) => (
                <tr key={p.id}>
                  <td style={td}>{p.id}</td><td style={td}>{p.game_date}</td><td style={td}>{p.pitcher}</td>
                  <td style={td}>{p.batter}</td><td style={td}>{p.pitch_type}</td><td style={td}>{p.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>


    </main>
  );
}

/* --- styles --- */
const card: React.CSSProperties = { border: "1px solid #eee", borderRadius: 12, padding: 16, marginBottom: 16, boxShadow: "0 1px 2px rgba(0,0,0,0.04)", background: "#fff" };
const h2: React.CSSProperties = { fontSize: 20, marginBottom: 8 };
const label: React.CSSProperties = { fontWeight: 600, display: "block", marginBottom: 8 };
const muted: React.CSSProperties = { color: "#666", marginBottom: 8 };
const textarea: React.CSSProperties = { width: "100%", padding: 12, border: "1px solid #ddd", borderRadius: 8, resize: "vertical", fontSize: 14, marginBottom: 12 };
const input: React.CSSProperties = { padding: "10px 12px", border: "1px solid #ddd", borderRadius: 8, fontSize: 14 };
const primaryBtn: React.CSSProperties = { padding: "10px 14px", borderRadius: 8, border: "1px solid #222", background: "#222", color: "#fff", cursor: "pointer" };
const secondaryBtn: React.CSSProperties = { padding: "10px 14px", borderRadius: 8, border: "1px solid #999", background: "#fff", color: "#222", cursor: "pointer" };
const outputPre: React.CSSProperties = { whiteSpace: "pre-wrap", wordBreak: "break-word", background: "#f7f7f7", border: "1px solid #eee", borderRadius: 8, padding: 12, minHeight: 160, maxHeight: 300, overflow: "auto", fontSize: 14 };
const table: React.CSSProperties = { borderCollapse: "separate", borderSpacing: 0, width: "100%", fontSize: 14 };
const th: React.CSSProperties = { textAlign: "left", padding: "10px 8px", borderBottom: "1px solid #eee", background: "#fafafa", position: "sticky", top: 0 };
const td: React.CSSProperties = { padding: "10px 8px", borderBottom: "1px solid #f1f1f1" };
