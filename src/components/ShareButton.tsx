/**
 * ShareButton.tsx — Copy current view URL to clipboard with a brief
 * "Copied!" confirmation toast.
 */

import { useState, useCallback } from "react";

interface Props {
  onCopy: () => Promise<boolean>;
}

export default function ShareButton({ onCopy }: Props) {
  const [copied, setCopied] = useState(false);

  const handleClick = useCallback(async () => {
    const ok = await onCopy();
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    }
  }, [onCopy]);

  return (
    <button
      onClick={handleClick}
      title="Copy shareable link to clipboard"
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                  border transition-all duration-200 ${
        copied
          ? "bg-green-700/30 border-green-500/40 text-green-300"
          : "bg-slate-800 border-white/10 text-slate-300 hover:text-white hover:bg-slate-700"
      }`}
    >
      {copied ? (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          Share view
        </>
      )}
    </button>
  );
}
