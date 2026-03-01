import { useState } from "react";
import axios from "axios";
import Mermaid from "./components/Mermaid";
import {
  Search,
  Loader2,
  Cpu,
  Terminal,
  Sparkles,
  AlertTriangle,
} from "lucide-react";
import { Lock } from "lucide-react";

// 型定義の整理
interface SearchResult {
  summary: string;
  mermaid: string;
}

// 環境変数の取得（存在しない場合のガード）
const API_URL = import.meta.env.VITE_API_URL || "";

function App() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [inputPassword, setInputPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // ログイン処理
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputPassword.length > 0) {
      setIsAuthenticated(true);
      setError(null);
    } else {
      setError("システムキーを入力してください。");
    }
  };

  const handleIndexSearch = async () => {
    if (!query || !API_URL) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${API_URL.replace(/\/$/, "")}/generate-from-index`,
        { query, genre: "RAG" },
        {
          headers: {
            "Content-Type": "application/json",
            "X-Ouroboros-Key": inputPassword,
          },
        },
      );
      setResult(response.data);
    } catch (err: unknown) {
      console.error("Search Error:", err);
      let message = "サーバーとの通信に失敗しました。";

      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          message = "認証エラー: システムキーが正しくありません。";
          setIsAuthenticated(false);
        } else if (err.response?.status === 404) {
          message = "エンドポイントが見つかりません。";
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // 未認証ならログイン画面を表示
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-cyber-black flex items-center justify-center p-6 font-mono">
        <div className="w-full max-w-md bg-cyber-dark border border-cyan-900/30 rounded-2xl p-8 shadow-neon">
          <div className="flex flex-col items-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-neon-cyan to-blue-600 rounded-2xl flex items-center justify-center shadow-neon mb-4">
              <Lock className="text-cyber-black" size={32} />
            </div>
            <h1 className="text-white text-2xl font-black tracking-tighter">
              OUROBOROS AUTH
            </h1>
          </div>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="password"
              value={inputPassword}
              onChange={(e) => setInputPassword(e.target.value)}
              placeholder="ENTER SYSTEM KEY..."
              className="w-full bg-cyber-black border border-slate-800 rounded-xl p-4 text-center text-neon-cyan focus:border-neon-cyan/50 focus:outline-none transition-all"
            />
            <button className="w-full py-4 bg-neon-cyan text-cyber-black font-black uppercase tracking-widest rounded-xl hover:bg-white transition-all shadow-neon">
              UNLOCK SYSTEM
            </button>
            {error && (
              <p className="text-red-400 text-xs text-center mt-2">{error}</p>
            )}
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cyber-black text-slate-300 font-mono flex flex-col">
      {/* ナビゲーションバー */}
      <nav className="border-b border-cyan-900/30 bg-cyber-dark/80 backdrop-blur-md px-6 py-4 flex justify-between items-center sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-neon-cyan to-blue-600 rounded-lg flex items-center justify-center shadow-neon">
            <Cpu className="text-cyber-black" size={24} />
          </div>
          <span className="text-2xl font-black tracking-tighter text-white">
            OUROBOROS <span className="text-neon-cyan">v1.0</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-xs tracking-widest text-cyan-500/50 uppercase">
          <span className="flex items-center gap-1 font-bold text-neon-cyan">
            <Sparkles size={14} /> Mode: RAG Enabled
          </span>
          <span className="flex items-center gap-1">
            <Terminal size={14} /> System: Online
          </span>
        </div>
      </nav>

      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1600px] mx-auto w-full">
        {/* 左：コントロールパネル */}
        <div className="lg:col-span-4 space-y-6">
          <section className="bg-cyber-dark border border-cyan-900/30 rounded-2xl p-6 shadow-neon relative">
            <h2 className="text-xs uppercase tracking-[0.2em] text-neon-cyan mb-6 font-bold flex items-center gap-2">
              <Search size={16} /> Research Query
            </h2>

            <div className="space-y-4">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="例: Graph RAG論文の全体的なアーキテクチャを図解して"
                className="w-full h-32 bg-cyber-black border border-slate-800 rounded-xl p-4 text-sm focus:border-neon-cyan/50 focus:outline-none transition-all resize-none text-white"
              />

              <button
                onClick={handleIndexSearch}
                disabled={loading || !query}
                className="w-full py-4 bg-neon-cyan text-cyber-black font-black uppercase tracking-widest rounded-xl hover:bg-white transition-all disabled:bg-slate-800 disabled:text-slate-600 shadow-neon"
              >
                {loading ? (
                  <Loader2 className="animate-spin mx-auto" size={24} />
                ) : (
                  "Ask Uroboros"
                )}
              </button>

              {/* エラーメッセージ表示エリア */}
              {error && (
                <div className="mt-4 p-3 bg-red-950/20 border border-red-500/50 rounded-lg text-red-400 text-xs flex items-center gap-2">
                  <AlertTriangle size={14} /> {error}
                </div>
              )}
            </div>
          </section>

          {/* ログエリア */}
          <section className="bg-cyber-dark border border-slate-800 rounded-2xl p-4 text-[10px] font-mono text-cyan-500/40 space-y-1">
            <p>&gt; Index 'ouroboros_index' connected</p>
            <p>&gt; 90 chunks available for retrieval</p>
            <p>&gt; Vector space ready </p>
            <p>&gt; Auth Token: {APP_PASSWORD ? "SET" : "MISSING"}</p>
          </section>
        </div>

        {/* 右：出力エリア */}
        <div className="lg:col-span-8 bg-cyber-dark border border-cyan-900/20 rounded-2xl p-8 flex flex-col min-h-[600px] overflow-hidden relative">
          <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
            <h2 className="text-xs uppercase tracking-[0.2em] text-neon-cyan font-bold">
              Blueprint Visualizer
            </h2>
            {result && (
              <button
                onClick={() => setResult(null)}
                className="text-[10px] text-slate-500 hover:text-neon-cyan transition-colors"
              >
                CLEAR OUTPUT
              </button>
            )}
          </div>

          <div className="flex-1 relative overflow-auto">
            {result ? (
              <div className="space-y-6 animate-in fade-in duration-500">
                <div className="bg-cyber-black p-4 rounded-lg border-l-4 border-neon-cyan text-sm italic text-slate-400">
                  {result.summary}
                </div>
                <Mermaid chart={result.mermaid} />
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center opacity-20">
                <Cpu size={80} className="mb-4 animate-pulse" />
                <p className="tracking-[0.5em] uppercase text-xs">
                  Ready for RAG Search
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
