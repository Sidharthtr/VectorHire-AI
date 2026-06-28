"use client";
/**
 * Career-Coach chat panel — streaming Q&A scoped to one saved analysis.
 *
 * What it does:
 * - On mount, loads prior messages for analysisId via api.getMessages
 * - On send, appends an optimistic user message + a streaming assistant placeholder
 * - Calls api.streamChat to feed token chunks into the assistant bubble; supports abort
 *
 * Upstream (who imports this OR which URL renders it): app/(app)/analysis/[id]/page.tsx
 * Downstream (what this imports): @/lib/api, @/types ChatMessage, lucide-react icons
 */
// useEffect/useRef/useState — load history, autoscroll to bottom, hold abort controller, manage messages
import { useEffect, useRef, useState } from "react";
// lucide-react icons — Send button, Sparkles for assistant bubble + header, UserIcon for user bubble
import { Send, Sparkles, User as UserIcon } from "lucide-react";
// api — getMessages (load chat history) and streamChat (push user msg + stream assistant reply)
import { api } from "@/lib/api";
// ChatMessage — server-side message shape returned by GET /messages, mapped to LocalMessage
import type { ChatMessage } from "@/types";

type LocalMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
};

function toLocal(m: ChatMessage): LocalMessage {
  return { id: m.id, role: m.role, content: m.content };
}

export default function ChatPanel({ analysisId }: { analysisId: string }) {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setLoadingHistory(true);
    api.getMessages(analysisId)
      .then((msgs) => setMessages(msgs.map(toLocal)))
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Failed to load chat"),
      )
      .finally(() => setLoadingHistory(false));
  }, [analysisId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const send = async () => {
    const content = input.trim();
    if (!content || busy) return;
    setError(null);
    setInput("");

    const userId = `local-${Date.now()}-u`;
    const assistantId = `local-${Date.now()}-a`;
    setMessages((prev) => [
      ...prev,
      { id: userId, role: "user", content },
      { id: assistantId, role: "assistant", content: "", streaming: true },
    ]);
    setBusy(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      await api.streamChat(
        analysisId,
        content,
        (chunk) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + chunk } : m,
            ),
          );
        },
        ctrl.signal,
      );
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, streaming: false } : m)),
      );
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setError(err instanceof Error ? err.message : "Chat failed");
      setMessages((prev) => prev.filter((m) => m.id !== assistantId));
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 flex flex-col h-[600px]">
      <div className="px-5 py-3 border-b border-gray-200 flex items-center gap-2">
        <Sparkles size={16} className="text-brand-600" />
        <h2 className="font-bold text-gray-900">Ask your Career Coach</h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {loadingHistory ? (
          <p className="text-sm text-gray-400">Loading conversation…</p>
        ) : messages.length === 0 ? (
          <div className="text-sm text-gray-500 space-y-3">
            <p>
              Ask follow-up questions about your matched jobs, skill gaps, or
              improvement roadmap. Try:
            </p>
            <ul className="space-y-1.5 text-gray-600">
              <li>• &ldquo;Which of these jobs is the easiest to land?&rdquo;</li>
              <li>• &ldquo;What should I learn first to close my skill gap?&rdquo;</li>
              <li>• &ldquo;How do I tailor my resume for the top match?&rdquo;</li>
            </ul>
          </div>
        ) : (
          messages.map((m) => (
            <div key={m.id} className="flex gap-3">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                  m.role === "user"
                    ? "bg-gray-100 text-gray-600"
                    : "bg-brand-50 text-brand-600"
                }`}
              >
                {m.role === "user" ? <UserIcon size={14} /> : <Sparkles size={14} />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-500 mb-1">
                  {m.role === "user" ? "You" : "Career Coach"}
                </p>
                <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {m.content}
                  {m.streaming && (
                    <span className="inline-block w-1.5 h-4 bg-brand-600 ml-0.5 align-text-bottom animate-pulse" />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {error && (
        <div className="px-5 py-2 text-sm text-red-600 bg-red-50 border-t border-red-100">
          {error}
        </div>
      )}

      <div className="border-t border-gray-200 p-3">
        <div className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask anything about your matches…"
            rows={1}
            disabled={busy}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 max-h-32"
          />
          <button
            onClick={send}
            disabled={busy || !input.trim()}
            className="bg-brand-600 hover:bg-brand-700 disabled:bg-gray-300 text-white p-2.5 rounded-lg transition-colors"
            title="Send"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-1.5 px-1">
          Enter to send · Shift+Enter for newline
        </p>
      </div>
    </div>
  );
}
