import React, { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import { AlertCircle } from "lucide-react";

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  themeVariables: {
    darkMode: true,
    background: "#0a0a0f",
    primaryColor: "#121218",
    primaryTextColor: "#00fff9",
    primaryBorderColor: "#00fff9",
    lineColor: "#00fff9",
    textColor: "#e2e8f0",
  },
  securityLevel: "loose",
});

interface MermaidProps {
  chart: string;
}

const Mermaid: React.FC<MermaidProps> = ({ chart }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    const renderChart = async () => {
      if (!ref.current || !chart) return;

      try {
        setRenderError(false);
        ref.current.innerHTML = "";

        // コードのクリーニング
        const cleanCode = chart
          .replace(/```mermaid/g, "")
          .replace(/```/g, "")
          .trim();

        const id = `mermaid-render-${Math.random().toString(36).substring(2, 9)}`;
        // mermaid.render は構文が不正だと例外を投げるため、ここでキャッチされる
        const { svg } = await mermaid.render(id, cleanCode);

        if (ref.current) {
          ref.current.innerHTML = svg;
        }
      } catch (error) {
        console.error("Mermaid Render Error:", error);
        setRenderError(true);
      }
    };

    renderChart();
  }, [chart]);

  return (
    <div className="relative w-full">
      {renderError && (
        <div className="bg-red-950/30 border border-red-500/50 p-4 rounded-lg text-red-200 mb-4 font-mono">
          <div className="flex items-center gap-2 mb-2 font-bold text-red-400">
            <AlertCircle size={20} /> SYNTAX ERROR DETECTED
          </div>
          <p className="text-[10px] mb-2 text-red-300/70">
            AIが生成した構文に誤りがあります。生データを確認してください：
          </p>
          <pre className="bg-black/50 p-2 text-[10px] overflow-auto max-h-40 border border-red-900/30">
            {chart}
          </pre>
        </div>
      )}
      <div
        className="uroboros-render-area bg-[#0a0a0f] p-4 rounded-lg border border-cyan-900/50 overflow-auto flex justify-center"
        ref={ref}
      />
    </div>
  );
};

export default Mermaid;
