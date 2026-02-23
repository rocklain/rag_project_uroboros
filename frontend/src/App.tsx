import React, { useState } from "react";
import axios from "axios";
import Mermaid from "./components/Mermaid";
// 修正後：Terminal と Share2 を追加
import { Upload, Loader2, Cpu, FileText, Terminal, Share2 } from "lucide-react";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/analyze",
        formData,
      );
      setResult(response.data);
    } catch (error) {
      alert("解析に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cyber-black text-slate-300 font-mono flex flex-col">
      {/* ナビゲーションバー */}
      <nav className="border-b border-cyan-900/30 bg-cyber-dark/80 backdrop-blur-md px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-neon-cyan to-blue-600 rounded-lg flex items-center justify-center shadow-neon">
            <Cpu className="text-cyber-black" size={24} />
          </div>
          <span className="text-2xl font-black tracking-tighter text-white">OUROBOROS <span className="text-neon-cyan">v1.0</span></span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-xs tracking-widest text-cyan-500/50 uppercase">
          <span className="flex items-center gap-1"><Terminal size={14} /> System: Ready</span>
          <span className="flex items-center gap-1"><Share2 size={14} /> Network: AOAI Connected</span>
        </div>
      </nav>

      {/* メインコンテンツ */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1600px] mx-auto w-full">
        
        {/* 左：コントロールパネル */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-cyber-dark border border-cyan-900/30 rounded-2xl p-6 shadow-neon relative">
            <div className="absolute top-0 right-0 p-2 opacity-10"><Cpu size={40} /></div>
            <h2 className="text-xs uppercase tracking-[0.2em] text-neon-cyan mb-6 font-bold flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-neon-cyan rounded-full animate-pulse" />
              Ingestion Module
            </h2>
            
            <label className="group relative flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-slate-800 rounded-xl cursor-pointer hover:border-neon-cyan/50 transition-all bg-cyber-black/50">
              <div className="flex flex-col items-center justify-center py-6">
                <FileText className={`w-12 h-12 mb-4 transition-colors ${file ? "text-neon-cyan" : "text-slate-600"}`} />
                <p className="text-xs text-slate-400 text-center px-4">
                  {file ? <span className="text-white font-bold">{file.name}</span> : "DROP RESEARCH PAPER (PDF)"}
                </p>
              </div>
              <input type="file" className="hidden" onChange={handleFileChange} accept="application/pdf" />
            </label>

            <button
              onClick={handleAnalyze}
              disabled={loading || !file}
              className="mt-6 w-full py-4 bg-neon-cyan text-cyber-black font-black uppercase tracking-widest rounded-xl hover:bg-white transition-all disabled:bg-slate-800 disabled:text-slate-600 shadow-[0_0_20px_rgba(0,255,249,0.3)]"
            >
              {loading ? <Loader2 className="animate-spin mx-auto" size={24} /> : "Initialize Analysis"}
            </button>
          </section>

          {/* ステータスログ風の装飾 */}
          <section className="bg-cyber-dark border border-slate-800 rounded-2xl p-4 text-[10px] font-mono text-cyan-500/40 space-y-1">
            <p>&gt; initializing neural weights...</p>
            <p>&gt; connection to gpt-4o established</p>
            <p>&gt; ready for stream input</p>
          </section>
        </div>

        {/* 右：出力エリア */}
        <div className="lg:col-span-8 bg-cyber-dark border border-cyan-900/20 rounded-2xl p-8 flex flex-col min-h-[600px] overflow-hidden relative">
          <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
            <h2 className="text-xs uppercase tracking-[0.2em] text-neon-cyan font-bold">Blueprint Visualizer</h2>
            {result && <span className="text-[10px] text-slate-500 uppercase">Analysis Engine: GPT-4o-2024-11-20</span>}
          </div>

          <div className="flex-1 relative overflow-auto">
            {result ? (
              <div className="space-y-6">
                <div className="bg-cyber-black p-4 rounded-lg border-l-4 border-neon-cyan text-sm italic text-slate-400">
                  {result.summary}
                </div>
                <Mermaid chart={result.mermaid} />
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center opacity-20">
                <Cpu size={80} className="mb-4 animate-pulse" />
                <p className="tracking-[0.5em] uppercase text-xs">Awaiting data...</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;