import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, Link } from "react-router";
import { ArrowLeft, Bot, UserIcon, Send, CheckCircle, XCircle, RefreshCw, ArrowRight, ArrowDown, DollarSign, Zap, TrendingDown, TrendingUp, Handshake, ShieldX } from "lucide-react";
import { authFetch } from "../auth";

interface ParsedMove {
  action: string;
  cash_difference: number;
  payer_id: string;
  reasoning: string;
  message: string;
}

interface NegLog {
  id: string;
  agent: string;
  content: string;
  step: number;
}

interface Message {
  id: string;
  sender_id: string;
  sender_name: string;
  content: string;
  created_at: string;
}

function parseLogContent(content: string): ParsedMove | null {
  try {
    const parsed = JSON.parse(content);
    if (parsed.action) return parsed;
  } catch {
    // Legacy format: "Action: $X paid by ... | reasoning"
    const match = content.match(/^(\w+):\s*\$([0-9.]+)\s*paid by\s*(\S+)\.\.\.\s*\|\s*(.+)/);
    if (match) {
      return {
        action: match[1].toLowerCase(),
        cash_difference: parseFloat(match[2]),
        payer_id: match[3],
        reasoning: match[4],
        message: match[4],
      };
    }
  }
  return null;
}

const ACTION_CONFIG: Record<string, { color: string; bg: string; border: string; icon: any; label: string }> = {
  offer: { color: "text-blue-700", bg: "bg-blue-50", border: "border-blue-200", icon: Zap, label: "Opening Offer" },
  counter: { color: "text-amber-700", bg: "bg-amber-50", border: "border-amber-200", icon: RefreshCw, label: "Counter" },
  accept: { color: "text-emerald-700", bg: "bg-emerald-50", border: "border-emerald-200", icon: Handshake, label: "Accepted" },
  reject: { color: "text-red-700", bg: "bg-red-50", border: "border-red-200", icon: ShieldX, label: "Rejected" },
};

export function DealNegotiation() {
  const { id } = useParams();
  const [deal, setDeal] = useState<any>(null);
  const [item1, setItem1] = useState<any>(null);
  const [item2, setItem2] = useState<any>(null);
  const [negLogs, setNegLogs] = useState<NegLog[]>([]);
  const [chatroom, setChatroom] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState("");
  const [error, setError] = useState("");
  const [counterCash, setCounterCash] = useState("");
  const [showCounter, setShowCounter] = useState(false);
  const [msgInput, setMsgInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const userId = typeof window !== "undefined" ? localStorage.getItem("guest_user_id") : null;

  const fetchDeal = () => {
    return authFetch(`/deals/${id}`)
      .then((res) => { if (!res.ok) throw new Error("Failed to fetch deal"); return res.json(); })
      .then((data) => {
        setDeal(data);
        // Fetch items
        Promise.all([
          authFetch(`/items/${data.user1_item_id}`).then(r => r.ok ? r.json() : null),
          authFetch(`/items/${data.user2_item_id}`).then(r => r.ok ? r.json() : null),
        ]).then(([i1, i2]) => { setItem1(i1); setItem2(i2); });
        return data;
      });
  };

  const fetchNegLogs = () => {
    return authFetch(`/negotiate/${id}/logs`)
      .then((res) => res.ok ? res.json() : [])
      .then((data) => setNegLogs(data))
      .catch(() => setNegLogs([]));
  };

  const fetchChatroom = () => {
    if (!userId) return Promise.resolve();
    return authFetch(`/chatrooms/user/${userId}`)
      .then((res) => res.ok ? res.json() : [])
      .then((rooms) => {
        const room = rooms.find((r: any) => r.deal_id === id);
        if (room) {
          setChatroom(room);
          return authFetch(`/chatrooms/${room.id}/messages`)
            .then((res) => res.ok ? res.json() : [])
            .then((msgs) => setMessages(msgs));
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchDeal(), fetchNegLogs(), fetchChatroom()])
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  // Poll for updates every 2 seconds while deal is pending/negotiating
  useEffect(() => {
    if (!deal || (deal.status !== "pending" && deal.status !== "negotiating")) return;
    const interval = setInterval(() => {
      fetchDeal().catch(() => {});
      fetchNegLogs();
      fetchChatroom();
    }, 2000);
    return () => clearInterval(interval);
  }, [id, deal?.status, chatroom?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, negLogs]);

  const handleConfirm = () => {
    setActionLoading("confirm");
    authFetch(`/negotiate/${id}/confirm`, { method: "POST" })
      .then((res) => { if (!res.ok) throw new Error("Failed to confirm"); return res.json(); })
      .then(() => { fetchDeal(); fetchNegLogs(); fetchChatroom(); })
      .catch((err) => setError(err.message))
      .finally(() => setActionLoading(""));
  };

  const handleDecline = () => {
    setActionLoading("decline");
    authFetch(`/negotiate/${id}/decline`, { method: "POST" })
      .then((res) => { if (!res.ok) throw new Error("Failed to decline"); return res.json(); })
      .then(() => { fetchDeal(); fetchNegLogs(); fetchChatroom(); })
      .catch((err) => setError(err.message))
      .finally(() => setActionLoading(""));
  };

  const handleCounter = () => {
    if (!counterCash || !userId) return;
    setActionLoading("counter");
    authFetch(`/negotiate/${id}/counter`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cash_difference: parseFloat(counterCash), payer_id: userId }),
    })
      .then((res) => { if (!res.ok) throw new Error("Failed to counter"); return res.json(); })
      .then(() => { setShowCounter(false); setCounterCash(""); fetchDeal(); fetchNegLogs(); fetchChatroom(); })
      .catch((err) => setError(err.message))
      .finally(() => setActionLoading(""));
  };

  const handleSendMessage = () => {
    if (!msgInput.trim() || !chatroom || !userId) return;
    authFetch(`/chatrooms/${chatroom.id}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender_id: userId, content: msgInput }),
    })
      .then((res) => { if (!res.ok) throw new Error("Failed to send"); return res.json(); })
      .then((msg) => { setMessages((prev) => [...prev, msg]); setMsgInput(""); })
      .catch((err) => setError(err.message));
  };

  const statusColors: Record<string, string> = {
    pending: "bg-[#6B6B6B] text-white",
    negotiating: "bg-[#534AB7] text-white",
    accepted: "bg-[#1D9E75] text-white",
    confirmed: "bg-[#1D9E75] text-white",
    declined: "bg-[#E24B4A] text-white",
  };

  // Parse structured log data
  const parsedLogs = useMemo(() =>
    negLogs.map((log) => ({ ...log, parsed: parseLogContent(log.content) })),
    [negLogs]
  );

  // Build offer history for the tracker
  const offerHistory = useMemo(() =>
    parsedLogs.filter(l => l.parsed).map(l => ({
      step: l.step,
      agent: l.agent,
      amount: l.parsed!.cash_difference,
      action: l.parsed!.action,
      payer: l.parsed!.payer_id,
    })),
    [parsedLogs]
  );

  // Determine which agent is "left" vs "right" from the deal
  const agent1Label = deal ? `agent_${deal.user1_id.slice(0, 8)}` : "";
  const agent2Label = deal ? `agent_${deal.user2_id.slice(0, 8)}` : "";

  if (loading) return <div className="p-8">Loading...</div>;
  if (error) return <div className="p-8 text-red-500">{error}</div>;
  if (!deal) return <div className="p-8">No deal found.</div>;

  const isNegotiating = deal.status === "negotiating";
  const isMyDeal = userId && (deal.user1_id === userId || deal.user2_id === userId);
  const maxOffer = Math.max(...offerHistory.map(o => o.amount), 1);

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <Link
        to="/my-deals"
        className="inline-flex items-center gap-2 text-[#6B6B6B] hover:text-[#1A1A1A] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to My Deals
      </Link>

      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          Trade Negotiation
        </h1>
        <span className={`px-4 py-2 rounded-full text-sm font-medium ${statusColors[deal.status] || "bg-gray-200"}`}>
          {deal.status.charAt(0).toUpperCase() + deal.status.slice(1)}
        </span>
      </div>

      {/* Deal Summary — Two items with VS */}
      <div className="relative grid grid-cols-[1fr,auto,1fr] gap-4 mb-8 items-stretch">
        <div className="bg-white rounded-xl p-6 border-2 border-[#E5E5E5]">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-blue-600" />
            </div>
            <span className="text-xs font-mono text-[#6B6B6B]">Agent 1</span>
          </div>
          <h3 className="font-semibold text-lg mb-1">{item1?.name ?? "Loading..."}</h3>
          {item1 && (
            <div className="flex items-center gap-3 mt-2">
              <span className="text-2xl font-bold text-[#1A1A1A]">${item1.price}</span>
              <span className="text-sm text-[#6B6B6B] px-2 py-0.5 bg-[#F3F4F6] rounded">{item1.condition}</span>
            </div>
          )}
        </div>

        <div className="flex items-center justify-center">
          <div className="w-14 h-14 rounded-full bg-[#534AB7] flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-sm">VS</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border-2 border-[#E5E5E5]">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <Bot className="w-4 h-4 text-purple-600" />
            </div>
            <span className="text-xs font-mono text-[#6B6B6B]">Agent 2</span>
          </div>
          <h3 className="font-semibold text-lg mb-1">{item2?.name ?? "Loading..."}</h3>
          {item2 && (
            <div className="flex items-center gap-3 mt-2">
              <span className="text-2xl font-bold text-[#1A1A1A]">${item2.price}</span>
              <span className="text-sm text-[#6B6B6B] px-2 py-0.5 bg-[#F3F4F6] rounded">{item2.condition}</span>
            </div>
          )}
        </div>
      </div>

      {/* Cash Difference Banner */}
      <div className="bg-gradient-to-r from-[#534AB7] to-[#7C6DD8] rounded-xl p-5 mb-8 flex items-center justify-between text-white">
        <div className="flex items-center gap-3">
          <DollarSign className="w-6 h-6 opacity-80" />
          <span className="text-white/80 font-medium">Current Cash Difference</span>
        </div>
        <span className="text-3xl font-bold">${deal.cash_difference?.toFixed(2) ?? "0.00"}</span>
      </div>

      {/* Offer Tracker — Visual bar chart of offers */}
      {offerHistory.length > 1 && (
        <div className="bg-white rounded-xl p-6 mb-8 border border-[#E5E5E5]">
          <div className="flex items-center gap-2 mb-4">
            <TrendingDown className="w-5 h-5 text-[#534AB7]" />
            <h2 className="font-semibold">Offer History</h2>
            <span className="text-xs text-[#6B6B6B] ml-auto">{offerHistory.length} rounds</span>
          </div>
          <div className="space-y-2">
            {offerHistory.map((offer, i) => {
              const isLeft = offer.agent === agent1Label;
              const cfg = ACTION_CONFIG[offer.action] || ACTION_CONFIG.counter;
              const width = Math.max(15, (offer.amount / maxOffer) * 100);
              return (
                <div key={i} className={`flex items-center gap-3 ${isLeft ? "" : "flex-row-reverse"}`}>
                  <span className={`text-xs font-mono w-6 text-center ${isLeft ? "text-blue-600" : "text-purple-600"}`}>
                    R{offer.step}
                  </span>
                  <div className={`flex items-center gap-2 ${isLeft ? "" : "flex-row-reverse"}`} style={{ width: '100%' }}>
                    <div
                      className={`h-8 rounded-lg ${cfg.bg} ${cfg.border} border flex items-center ${isLeft ? "pr-3 pl-2" : "pl-3 pr-2"} transition-all duration-500`}
                      style={{ width: `${width}%`, minWidth: 'fit-content' }}
                    >
                      <cfg.icon className={`w-3.5 h-3.5 ${cfg.color} flex-shrink-0`} />
                      <span className={`text-sm font-bold ml-2 ${cfg.color}`}>
                        ${offer.amount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Agent Negotiation Chat — Transaction Style */}
      <div className="bg-white rounded-xl overflow-hidden mb-8 border border-[#E5E5E5]">
        <div className="p-4 border-b border-[#E5E5E5] bg-[#FAFAFA] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#534AB7]" />
            <h2 className="font-semibold">Live Negotiation</h2>
          </div>
          {deal.status === "pending" && (
            <span className="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              Agents negotiating...
            </span>
          )}
        </div>
        <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto bg-[#FAFAFA]">
          {parsedLogs.length === 0 && messages.length === 0 && (
            <p className="text-[#6B6B6B] text-center py-12">No negotiation activity yet.</p>
          )}
          {parsedLogs.map((log, idx) => {
            const move = log.parsed;
            const isLeft = log.agent === agent1Label;
            const cfg = move ? (ACTION_CONFIG[move.action] || ACTION_CONFIG.counter) : ACTION_CONFIG.counter;
            const ActionIcon = cfg.icon;

            return (
              <div key={log.id || idx} className={`flex ${isLeft ? "justify-start" : "justify-end"}`}>
                <div className={`max-w-[75%] ${isLeft ? "" : ""}`}>
                  {/* Agent badge */}
                  <div className={`flex items-center gap-2 mb-1.5 ${isLeft ? "" : "justify-end"}`}>
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${isLeft ? "bg-blue-100" : "bg-purple-100"}`}>
                      <Bot className={`w-3 h-3 ${isLeft ? "text-blue-600" : "text-purple-600"}`} />
                    </div>
                    <span className={`text-xs font-medium ${isLeft ? "text-blue-600" : "text-purple-600"}`}>
                      {isLeft ? "Agent 1" : "Agent 2"}
                    </span>
                    <span className="text-xs text-[#6B6B6B]">Round {log.step}</span>
                  </div>

                  {/* Message bubble */}
                  <div className={`rounded-2xl overflow-hidden border ${cfg.border} ${isLeft ? "rounded-tl-sm" : "rounded-tr-sm"}`}>
                    {/* Action header */}
                    <div className={`${cfg.bg} px-4 py-2.5 flex items-center justify-between gap-4`}>
                      <div className="flex items-center gap-2">
                        <ActionIcon className={`w-4 h-4 ${cfg.color}`} />
                        <span className={`text-sm font-semibold ${cfg.color}`}>{cfg.label}</span>
                      </div>
                      {move && (
                        <div className="flex items-center gap-1.5">
                          <DollarSign className={`w-4 h-4 ${cfg.color}`} />
                          <span className={`text-lg font-bold ${cfg.color}`}>
                            {move.cash_difference.toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                    {/* Message body */}
                    <div className="bg-white px-4 py-3">
                      {move?.message ? (
                        <p className="text-[#1A1A1A] text-sm leading-relaxed">{move.message}</p>
                      ) : move?.reasoning ? (
                        <p className="text-[#1A1A1A] text-sm leading-relaxed">{move.reasoning}</p>
                      ) : (
                        <p className="text-[#6B6B6B] text-sm italic">{log.content}</p>
                      )}
                      {move?.reasoning && move?.message && (
                        <p className="text-xs text-[#6B6B6B] mt-2 italic">Strategy: {move.reasoning}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Separator between agent logs and user chat */}
          {parsedLogs.length > 0 && messages.length > 0 && (
            <div className="flex items-center gap-4 py-2">
              <div className="flex-1 border-t border-[#E5E5E5]" />
              <span className="text-xs text-[#6B6B6B] font-medium">User Chat</span>
              <div className="flex-1 border-t border-[#E5E5E5]" />
            </div>
          )}

          {messages.map((msg) => {
            const isMe = msg.sender_id === userId;
            return (
              <div key={msg.id} className={`flex gap-3 ${isMe ? "justify-end" : ""}`}>
                {!isMe && (
                  <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center flex-shrink-0">
                    <UserIcon className="w-4 h-4 text-gray-600" />
                  </div>
                )}
                <div className={`rounded-2xl px-4 py-2.5 max-w-[70%] ${isMe ? "bg-[#534AB7] text-white rounded-tr-sm" : "bg-white border border-[#E5E5E5] text-[#1A1A1A] rounded-tl-sm"}`}>
                  {!isMe && <p className="text-xs font-medium mb-1 text-[#6B6B6B]">{msg.sender_name}</p>}
                  <p className="text-sm">{msg.content}</p>
                  <p className={`text-xs mt-1 ${isMe ? "text-white/60" : "text-[#6B6B6B]"}`}>
                    {new Date(msg.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        {chatroom && isMyDeal && deal.status !== "declined" && deal.status !== "accepted" && (
          <div className="p-4 border-t border-[#E5E5E5] bg-white flex gap-2">
            <input
              value={msgInput}
              onChange={(e) => setMsgInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Type a message..."
              className="flex-1 px-4 py-2.5 border border-[#E5E5E5] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#534AB7] bg-[#FAFAFA]"
            />
            <button onClick={handleSendMessage} className="px-4 py-2.5 bg-[#534AB7] text-white rounded-xl hover:bg-[#453CA0] transition-colors">
              <Send className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      {isMyDeal && isNegotiating && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <button
              onClick={handleConfirm}
              disabled={!!actionLoading}
              className="flex-1 flex items-center justify-center gap-2 py-4 bg-[#1D9E75] text-white rounded-xl hover:bg-[#178A64] transition-colors disabled:opacity-50 font-medium"
            >
              <CheckCircle className="w-5 h-5" />
              {actionLoading === "confirm" ? "Confirming..." : "Accept Deal"}
            </button>
            <button
              onClick={handleDecline}
              disabled={!!actionLoading}
              className="flex-1 flex items-center justify-center gap-2 py-4 bg-[#E24B4A] text-white rounded-xl hover:bg-[#C93F3E] transition-colors disabled:opacity-50 font-medium"
            >
              <XCircle className="w-5 h-5" />
              {actionLoading === "decline" ? "Declining..." : "Decline Deal"}
            </button>
            <button
              onClick={() => setShowCounter(!showCounter)}
              disabled={!!actionLoading}
              className="flex-1 flex items-center justify-center gap-2 py-4 bg-[#534AB7] text-white rounded-xl hover:bg-[#453CA0] transition-colors disabled:opacity-50 font-medium"
            >
              <RefreshCw className="w-5 h-5" />
              Counter Offer
            </button>
          </div>

          {showCounter && (
            <div className="bg-white rounded-xl p-6 flex gap-4 items-end border border-[#E5E5E5]">
              <div className="flex-1">
                <label className="text-sm text-[#6B6B6B] mb-1 block">New Cash Difference ($)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={counterCash}
                  onChange={(e) => setCounterCash(e.target.value)}
                  className="w-full px-4 py-3 border border-[#E5E5E5] rounded-xl focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
                  placeholder="e.g. 5.00"
                />
              </div>
              <button
                onClick={handleCounter}
                disabled={!!actionLoading || !counterCash}
                className="px-8 py-3 bg-[#534AB7] text-white rounded-xl hover:bg-[#453CA0] disabled:opacity-50 font-medium"
              >
                {actionLoading === "counter" ? "Sending..." : "Submit Counter"}
              </button>
            </div>
          )}
        </div>
      )}

      {deal.status === "accepted" && (
        <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <Handshake className="w-8 h-8 text-emerald-600" />
          </div>
          <h3 className="text-xl font-bold text-emerald-700">Deal Accepted!</h3>
          <p className="text-emerald-600/70 mt-2">This trade has been confirmed by both parties.</p>
          <p className="text-2xl font-bold text-emerald-700 mt-3">${deal.cash_difference?.toFixed(2)}</p>
        </div>
      )}

      {deal.status === "declined" && (
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <ShieldX className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-xl font-bold text-red-600">Deal Declined</h3>
          <p className="text-red-400 mt-2">The agents could not reach an agreement.</p>
        </div>
      )}
    </div>
  );
}
