import { useState, useEffect } from "react";
import axios from "axios";
import Mermaid from "./components/Mermaid";
import {
  Search,
  Loader2,
  Cpu,
  Terminal,
  Sparkles,
  AlertTriangle,
  History,
  Trash2,
} from "lucide-react";
import { Lock } from "lucide-react";

// 型定義の整理
interface SearchResult {
  id?: string;
  query: string;
  summary: string;
  mermaid: string;
  annotation: string;
}

interface HistoryItem extends SearchResult {
  id: string;
  timestamp: string;
}

// 環境変数の取得（存在しない場合のガード）
const API_URL = import.meta.env.VITE_API_URL || "";

function App() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [inputPassword, setInputPassword] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // --- API通信 ---
  const apiClient = axios.create({
    baseURL: API_URL.replace(/\/$/, ""),
    headers: {
      "Content-Type": "application/json",
      "X-Ouroboros-Key": inputPassword,
    },
  });

  // 履歴の取得
  const fetchHistory = async () => {
    if (!isAuthenticated) return;
    try {
      const response = await apiClient.get<HistoryItem[]>("/history");
      setHistory(response.data);
    } catch (err) {
      console.error("History fetch error:", err);
      setError("履歴の取得に失敗しました。");
    }
  };

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

  // 認証状態が変わったら履歴を取得
  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated]);

  const handleIndexSearch = async () => {
    if (!query || !API_URL) return;
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.post(`/generate-from-index`, {
        query,
        genre: "RAG",
      });

      // handleIndexSearch 内
      const fullText = response.data.mermaid;

      // 「注釈」というキーワードで二つに割る
      const [rawChartArea, rawNote] = fullText.split(
        /注釈[:：]|\*\*注釈[:：]\*\*/,
      );

      setResult({
        ...response.data,
        mermaid: rawChartArea || "",
        annotation: rawNote ? `注釈: ${rawNote.trim()}` : "",
      });

      // 成功したら履歴を再取得
      fetchHistory();
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

  // 履歴アイテムを選択
  const handleSelectHistory = (item: HistoryItem) => {
    setQuery(item.query);
    const [rawChartArea, rawNote] = item.mermaid.split(
      /注釈[:：]|\*\*注釈[:：]\*\*/,
    );
    setResult({
      ...item,
      mermaid: rawChartArea || "",
      annotation: rawNote ? `注釈: ${rawNote.trim()}` : "",
    });
  };

  // 履歴アイテムを削除
  const handleDeleteHistory = async (itemId: string) => {
    try {
      await apiClient.delete(`/history/${itemId}`);
      // UIから削除
      setHistory(history.filter((item) => item.id !== itemId));
    } catch (err) {
      console.error("Delete error:", err);
      setError("履歴の削除に失敗しました。");
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

          {/* New: 履歴セクション */}
          <section className="bg-cyber-dark border border-cyan-900/30 rounded-2xl p-6 shadow-neon">
            <h2 className="text-xs uppercase tracking-[0.2em] text-neon-cyan mb-4 font-bold flex items-center gap-2">
              <History size={16} /> Query History
            </h2>
            <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
              {history.length > 0 ? (
                history.map((item) => (
                  <div
                    key={item.id}
                    className="group bg-cyber-black/50 hover:bg-neon-cyan/10 border border-transparent hover:border-neon-cyan/20 p-3 rounded-lg cursor-pointer transition-all"
                  >
                    <div className="flex justify-between items-start">
                      <p
                        className="text-xs text-slate-300 group-hover:text-neon-cyan flex-1"
                        onClick={() => handleSelectHistory(item)}
                      >
                        {item.query}
                      </p>
                      <button
                        onClick={() => handleDeleteHistory(item.id)}
                        className="text-slate-700 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity ml-2"
                        title="Delete this history item"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-600 italic">No history yet.</p>
              )}
            </div>
          </section>

          {/* ログエリア */}
          <section className="bg-cyber-dark border border-slate-800 rounded-2xl p-4 text-[10px] font-mono text-cyan-500/40 space-y-1">
            <p>&gt; Index 'ouroboros_index' connected</p>
            <p>&gt; 90 chunks available for retrieval</p>
            <p>&gt; Vector space ready </p>
            <p>&gt; Auth Token: {inputPassword ? "READY" : "WAITING"}</p>
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

                {/* Mermaid図のレンダリング */}
                <Mermaid chart={result.mermaid} />

                {/* --- 出典注釈を表示 --- */}
                {result.annotation && (
                  <div className="mt-8 pt-4 border-t border-slate-800 text-[10px] text-slate-500 flex items-center gap-2 italic">
                    <Terminal size={12} className="text-cyan-900" />
                    {result.annotation}
                  </div>
                )}
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
