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
  agents_run: string[];
  waterfall: RoutingDecision[];
  total_cost_usd: number;
  total_latency_ms: number;
  mocked: boolean;
};

const API = process.env.NEXT_PUBLIC_API_URL || "https://omniforge-api.onrender.com";

const PRESETS = [
  { id: "", label: "Free-form" },
  { id: "war_room", label: "War Room" },
  { id: "incident", label: "Incident" },
  { id: "chart", label: "Chart" },
] as const;

export default function HomePage() {
  const [text, setText] = useState(
    "How should a principal architect route models across web research vs deep analysis?",
  );
  const [preset, setPreset] = useState("war_room");
  const [imageB64, setImageB64] = useState<string | null>(null);
  const [voice, setVoice] = useState("");
  const [listening, setListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [ab, setAb] = useState<Record<string, unknown> | null>(null);
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
    const SR =
      (window as unknown as { SpeechRecognition?: new () => any; webkitSpeechRecognition?: new () => any })
        .SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: new () => any }).webkitSpeechRecognition;
    if (!SR) {
      setError("Browser speech recognition unavailable — paste a transcript instead.");
      return;
    }
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: { results: { 0: { 0: { transcript: string } } } }) => {
      setVoice(e.results[0][0].transcript);
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
        setAb(data.delta ?? data);
        setResult(data.routed);
      } else {
        setResult(data);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
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
      <header className="hero">
        <p className="brand">OmniForge</p>
        <h1>Ask anything. Right agents. Right models.</h1>
        <p className="lede">
          One multimodal ask fans out across agents and tools. The waterfall proves which model ran each
          step.
        </p>
        <div className="cta-row">
          <button className="btn" disabled={loading} onClick={() => ask("routed")}>
            {loading ? "Routing…" : "Ask"}
          </button>
          <button className="btn btn-secondary" disabled={loading} onClick={() => ask("ab")}>
            Compare A/B
          </button>
          <a className="btn-link" href="#proof">
            See proof
          </a>
        </div>
      </header>

      <section className="composer" aria-label="Ask composer">
        <div className="composer-top">
          <div className="presets" role="group" aria-label="Presets">
            {PRESETS.map((p) => (
              <button
                key={p.id || "free"}
                type="button"
                className="chip"
                data-active={preset === p.id}
                onClick={() => setPreset(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <textarea
          className="ask-box"
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask with text — attach a screenshot or use voice if you want."
        />
        <div className="composer-actions">
          <button type="button" className="btn btn-secondary" onClick={() => fileRef.current?.click()}>
            {imageB64 ? "Image attached" : "Add image"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => onFile(e.target.files?.[0] || null)}
          />
          <button type="button" className="btn btn-secondary" onClick={startVoice}>
            {listening ? "Listening…" : "Voice"}
          </button>
          <span className="hint">API · {API.replace("https://", "")}</span>
        </div>
        {voice ? <p className="voice">Voice: {voice}</p> : null}
        {error ? <p className="err">{error}</p> : null}
      </section>

      {result ? (
        <>
          <section className="section" id="proof">
            <h2>Answer</h2>
            <pre className="answer">{result.answer}</pre>
            <p className="meta">
              {result.total_latency_ms.toFixed(0)} ms · ${result.total_cost_usd.toFixed(4)} ·{" "}
              {result.mocked ? "mock fallback" : "live providers"} · {result.agents_run.join(" → ")}
            </p>
          </section>

          <section className="section">
            <h2>Model waterfall</h2>
            <p className="meta">Models used: {models.join(" · ") || "—"}</p>
            <ol className="waterfall">
              {result.waterfall.map((w, i) => (
                <li key={`${w.step}-${i}`} style={{ animationDelay: `${i * 60}ms` }}>
                  <div className="step-name">
                    {w.step} · {w.bucket}
                  </div>
                  <div className="step-model">
                    {w.provider} / {w.model_id}
                    {w.mocked ? " · mock" : ""}
                  </div>
                  <p className="step-reason">{w.reason}</p>
                  <p className="meta">
                    {w.latency_ms.toFixed(0)} ms · ${w.cost_usd.toFixed(5)}
                  </p>
                </li>
              ))}
            </ol>
          </section>
        </>
      ) : null}

      {ab ? (
        <section className="section">
          <h2>A/B delta</h2>
          <pre className="ab">{JSON.stringify(ab, null, 2)}</pre>
        </section>
      ) : null}

      <section className="section arch" id="architecture">
        <h2>Architecture</h2>
        <p>
          Self-contained monorepo: ingest → planner → parallel agents/MCP → Multi-LLM Brain → synthesizer →
          waterfall. No sibling runtime dependencies.
        </p>
        <ul>
          <li>Task-class routing: fast / structured / reasoning / vision</li>
          <li>Text, image, and voice transcript in one ask path</li>
          <li>In-repo FinOps budget + export gate</li>
        </ul>
      </section>
    </main>
  );
}
