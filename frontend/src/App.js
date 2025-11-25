import React, { useEffect, useState } from "react";
import "./App.css";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

function App() {
  const [langs, setLangs] = useState([]);
  const [source, setSource] = useState("en");
  const [target, setTarget] = useState("hi");
  const [inputText, setInputText] = useState("");
  const [translation, setTranslation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/languages`)
      .then((r) => r.json())
      .then((data) => {
        setLangs(data.languages || []);
        if (data.languages?.includes("en")) setSource("en");
        if (data.languages?.includes("hi")) setTarget("hi");
      })
      .catch((e) => console.error("Could not load languages", e));
  }, []);

  const doTranslate = async () => {
    setError("");
    setTranslation("");
    if (!inputText.trim()) {
      setError("Enter some text to translate.");
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source, target, text: inputText }),
      });
      const data = await resp.json();
      if (data.translation) setTranslation(data.translation);
      else setError(data.error || "Unexpected response from server");
    } catch (err) {
      setError("Network or server error: " + String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h1>Multi-Language Translator</h1>

      <div className="lang-select">
        <label>From:</label>
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          {langs.map((l) => (
            <option key={l} value={l}>{l.toUpperCase()}</option>
          ))}
        </select>

        <label>To:</label>
        <select value={target} onChange={(e) => setTarget(e.target.value)}>
          {langs.map((l) => (
            <option key={l} value={l}>{l.toUpperCase()}</option>
          ))}
        </select>

        <button onClick={() => { const s = source; setSource(target); setTarget(s); }}>⇄</button>
      </div>

      <textarea
        rows={6}
        placeholder="Type text to translate..."
        value={inputText}
        onChange={(e) => setInputText(e.target.value)}
      />

      <button onClick={doTranslate} disabled={loading}>
        {loading ? "Translating..." : "Translate"}
      </button>

      {error && <div className="error">{error}</div>}

      {translation && (
        <div>
          <h3>Translation</h3>
          <div className="translation-box">{translation}</div>
          <button
            className="copy-btn"
            onClick={() => navigator.clipboard?.writeText(translation)}
          >
            Copy to Clipboard
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
