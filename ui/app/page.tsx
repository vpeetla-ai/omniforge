"use client";

import { useCallback, useMemo, useRef, useState } from "react";

type RoutingDecision = {
  step: string;
  bucket: string;
  provider: string;
  model_id: string;
  reason: string;
  latency_ms: number;
  cost_usd: number;
  mocked: boolean;
};

type AskResponse = {
  mission_id: string;
  answer: string;
  modalities: string[];
  agents_run: string[];
  tools_run: string[];
  waterfall: RoutingDecision[];
  mode: string;
  total_cost_usd: number;
  total_latency_ms: number;
  budget_halted: boolean;
  mocked: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function HomePage() {
  const [text, setText] = useState("How should a principal architect route models across web research vs deep analysis?");
  const [preset, setPreset] = useState("war_room");
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [voice, setVoice] = useState("");
  const [listening, setListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [ab, setAb] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const onFile = useCallback(async (file: File | null) => {
    if (!file) return;
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
    setImageB64(btoa(binary));
  }, []);

  const startVoice = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setError("Browser speech recognition not available — paste a transcript instead.");
      return;
    }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const t = e.results[0][0].transcript as string;
      setVoice(t);
      setListening(false);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    setListening(true);
    rec.start();
  };

  const ask = async (mode: "routed" | "ab") => {
    setLoading(true);
    setError(null);
    setAb(null);
    try {
      const body = {
        text: text || null,
        image_b64: imageB64,
        voice_transcript: voice || null,
        preset: preset || null,
        mode: "routed",
      };
      const path = mode === "ab" ? "/v1/ask/ab" : "/v1/ask";
      const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      if (mode === "ab") {
        setAb(data);
        setResult(data.routed);
      } else {
        setResult(data);
      }
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const models = useMemo(() => {
    if (!result) return [];
    return Array.from(new Set(result.waterfall.map((w) => w.model_id)));
  }, [result]);

  return (
    <main className="page">
      <link
        href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Sora:wght@400;500;600&display=swap"
        rel="stylesheet"
      />
      <header className="hero">
        <p className="brand">OmniForge</p>
        <h1>Ask anything. Right agents. Right models.</h1>
        <p className="lede">
          Multimodal ask fans out across agents and MCP tools. The Multi-LLM Brain routes each step —
          and the waterfall proves it.
        </p>
        <div className="cta-row">
          <button className="primary" disabled={loading} onClick={() => ask("routed")}>
            {loading ? "Running…" : "Ask"}
          </button>
          <button className="ghost" disabled={loading} onClick={() => ask("ab")}>
            A/B routed vs single
          </button>
          <a className="jump" href="#architecture">Architecture</a>
        </div>
      </header>

      <section className="panel input-panel">
        <h2>Mission</h2>
        <label>
          Preset
          <select value={preset} onChange={(e) => setPreset(e.target.value)}>
            <option value="">Free-form</option>
            <option value="war_room">Competitive War Room</option>
            <option value="incident">Incident from screenshot</option>
            <option value="chart">Explain this chart</option>
          </select>
        </label>
        <label>
          Text
          <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)} />
        </label>
        <div className="row">
          <button type="button" className="ghost" onClick={() => fileRef.current?.click()}>
            {imageB64 ? "Image attached ✓" : "Attach image / screenshot"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => onFile(e.target.files?.[0] || null)}
          />
          <button type="button" className="ghost" onClick={startVoice}>
            {listening ? "Listening…" : "Voice (browser ASR)"}
          </button>
        </div>
        {voice ? <p className="voice">Voice: {voice}</p> : null}
        {error ? <p className="err">{error}</p> : null}
      </section>

      {result ? (
        <>
          <section className="panel">
            <h2>Answer</h2>
            <pre className="answer">{result.answer}</pre>
            <p className="meta">
              {result.total_latency_ms.toFixed(0)} ms · ${result.total_cost_usd.toFixed(4)} ·{" "}
              {result.mocked ? "mock path" : "live providers"} · agents: {result.agents_run.join(", ")}
            </p>
          </section>

          <section className="panel waterfall">
            <h2>Model waterfall</h2>
            <p className="lede-sm">Models used: {models.join(" · ") || "—"}</p>
            <div className="falls">
              {result.waterfall.map((w, i) => (
                <article key={`${w.step}-${i}`} className="fall">
                  <header>
                    <strong>{w.step}</strong>
                    <span className="bucket">{w.bucket}</span>
                  </header>
                  <p className="model">
                    {w.provider} / {w.model_id}
                    {w.mocked ? " (mock)" : ""}
                  </p>
                  <p className="reason">{w.reason}</p>
                  <p className="meta">
                    {w.latency_ms.toFixed(0)} ms · ${w.cost_usd.toFixed(5)}
                  </p>
                </article>
              ))}
            </div>
          </section>
        </>
      ) : null}

      {ab ? (
        <section className="panel">
          <h2>A/B delta</h2>
          <pre className="answer">{JSON.stringify(ab.delta, null, 2)}</pre>
        </section>
      ) : null}

      <section id="architecture" className="panel">
        <h2>Architecture</h2>
        <p className="lede-sm">
          Self-contained monorepo: ingest → planner → parallel agents/MCP → Multi-LLM Brain → synthesizer →
          waterfall. No sibling vpeetla-ai runtime dependencies.
        </p>
        <ul className="status">
          <li>✅ Task-class routing (fast / structured / reasoning / vision)</li>
          <li>✅ Text + image + voice transcript</li>
          <li>✅ In-repo FinOps budget + export gate</li>
          <li>🟡 Live providers when API keys set</li>
        </ul>
      </section>

      <style jsx>{`
        .page {
          max-width: 980px;
          margin: 0 auto;
          padding: 2.5rem 1.25rem 4rem;
        }
        .hero {
          padding: 2.5rem 0 1.5rem;
          border-bottom: 1px solid var(--line);
          margin-bottom: 1.5rem;
        }
        .brand {
          font-family: var(--font-display);
          font-size: clamp(2.4rem, 6vw, 3.6rem);
          font-weight: 700;
          letter-spacing: -0.03em;
          margin: 0 0 0.35rem;
          color: var(--accent);
        }
        h1 {
          font-family: var(--font-display);
          font-size: clamp(1.35rem, 3vw, 1.85rem);
          font-weight: 600;
          margin: 0 0 0.75rem;
          max-width: 18ch;
          line-height: 1.15;
        }
        .lede {
          color: var(--muted);
          max-width: 52ch;
          line-height: 1.55;
          margin: 0 0 1.25rem;
        }
        .lede-sm { color: var(--muted); margin-top: 0; }
        .cta-row { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
        .primary, .ghost, .jump {
          border-radius: 999px;
          padding: 0.7rem 1.15rem;
          border: 1px solid var(--line);
          cursor: pointer;
          text-decoration: none;
        }
        .primary {
          background: linear-gradient(120deg, var(--accent), #2bb8c9);
          color: #041016;
          border: none;
          font-weight: 600;
        }
        .ghost { background: transparent; color: var(--ink); }
        .jump { color: var(--accent2); }
        .panel {
          background: var(--card);
          border: 1px solid var(--line);
          border-radius: 18px;
          padding: 1.15rem 1.2rem;
          margin: 1rem 0;
          backdrop-filter: blur(8px);
        }
        label { display: grid; gap: 0.35rem; margin: 0.75rem 0; color: var(--muted); font-size: 0.9rem; }
        textarea, select {
          width: 100%;
          border-radius: 12px;
          border: 1px solid var(--line);
          background: rgba(0,0,0,0.25);
          color: var(--ink);
          padding: 0.75rem;
        }
        .row { display: flex; flex-wrap: wrap; gap: 0.6rem; }
        .voice { color: var(--accent); }
        .err { color: var(--danger); }
        .answer {
          white-space: pre-wrap;
          background: rgba(0,0,0,0.28);
          padding: 1rem;
          border-radius: 12px;
          line-height: 1.5;
          overflow: auto;
        }
        .meta { color: var(--muted); font-size: 0.85rem; }
        .falls {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 0.75rem;
        }
        .fall {
          border: 1px solid var(--line);
          border-radius: 14px;
          padding: 0.85rem;
          background: rgba(0,0,0,0.2);
          animation: rise 0.5s ease both;
        }
        .fall header { display: flex; justify-content: space-between; gap: 0.5rem; }
        .bucket {
          font-size: 0.75rem;
          color: #041016;
          background: var(--accent2);
          border-radius: 999px;
          padding: 0.15rem 0.5rem;
        }
        .model { margin: 0.4rem 0; font-weight: 600; }
        .reason { color: var(--muted); font-size: 0.82rem; margin: 0; }
        .status { color: var(--muted); line-height: 1.7; }
        @keyframes rise {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: none; }
        }
      `}</style>
    </main>
  );
}
