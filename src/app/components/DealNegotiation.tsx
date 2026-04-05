import { useState } from "react";
import { useParams, Link } from "react-router";
import { ArrowLeft, Send, ChevronDown, ChevronUp } from "lucide-react";

export function DealNegotiation() {
  const { id } = useParams();
  const [message, setMessage] = useState("");
  const [agentLogExpanded, setAgentLogExpanded] = useState(true);

  // Mock data
  const deal = {
    id,
    yourItem: {
      name: "iClicker 2",
      image: "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=200",
    },
    theirItem: {
      name: "Calculus Textbook",
      image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200",
    },
    cashDifference: 5,
    status: "negotiating",
  };

  const humanMessages = [
    { sender: "them", name: "Sarah Chen", message: "Hi! Thanks for the offer.", time: "2:30 PM" },
    { sender: "you", name: "You", message: "No problem! Would you be okay with the $5 difference?", time: "2:32 PM" },
    { sender: "them", name: "Sarah Chen", message: "Could we meet in the middle at $3?", time: "2:35 PM" },
  ];

  const agentMessages = [
    { agent: "A", message: "Analyzing trade proposal: iClicker 2 (est. $40) ↔ Calculus Textbook (est. $45)", reasoning: "Initial value difference: $5" },
    { agent: "B", message: "Counter-proposal detected: User suggests $3 cash difference", reasoning: "Evaluating against owner preferences..." },
    { agent: "A", message: "Owner's limit: 20% of value ($8). $3 is within acceptable range.", reasoning: "Recommending acceptance" },
  ];

  const statusColors = {
    pending: "bg-[#6B6B6B] text-white",
    negotiating: "bg-[#534AB7] text-white",
    accepted: "bg-[#1D9E75] text-white",
    confirmed: "bg-[#1D9E75] text-white",
    declined: "bg-[#E24B4A] text-white",
  };

  const handleSend = () => {
    if (message.trim()) {
      alert(`Sent: ${message}`);
      setMessage("");
    }
  };

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      {/* Back Button */}
      <Link
        to="/profile"
        className="inline-flex items-center gap-2 text-[#6B6B6B] hover:text-[#1A1A1A] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Profile
      </Link>

      <h1 className="mb-8" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
        Trade Negotiation
      </h1>

      {/* Three-column layout */}
      <div className="grid grid-cols-[320px_1fr_320px] gap-6">
        {/* Left: Deal Summary */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6">
            {/* Items */}
            <div className="flex items-center gap-3 mb-4">
              <img
                src={deal.yourItem.image}
                alt={deal.yourItem.name}
                className="w-20 h-20 object-cover rounded-lg"
              />
              <div className="text-[#534AB7] text-2xl">→</div>
              <img
                src={deal.theirItem.image}
                alt={deal.theirItem.name}
                className="w-20 h-20 object-cover rounded-lg"
              />
            </div>

            {/* Names */}
            <div className="space-y-2 mb-4">
              <p className="text-sm text-[#6B6B6B]">You offer: <span className="text-[#1A1A1A]">{deal.yourItem.name}</span></p>
              <p className="text-sm text-[#6B6B6B]">You receive: <span className="text-[#1A1A1A]">{deal.theirItem.name}</span></p>
            </div>

            {/* Cash Difference */}
            <div className="p-4 bg-[#F9F9F9] rounded-lg mb-4">
              <p className="text-[#6B6B6B] text-sm mb-1">Cash difference</p>
              <p className="text-[#534AB7]" style={{ fontSize: '20px', fontWeight: 600 }}>
                You pay ${deal.cashDifference.toFixed(2)}
              </p>
            </div>

            {/* Status */}
            <span
              className={`inline-block px-4 py-2 rounded-full ${
                statusColors[deal.status as keyof typeof statusColors]
              }`}
              style={{ borderRadius: "20px" }}
            >
              {deal.status.charAt(0).toUpperCase() + deal.status.slice(1)}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button className="w-full py-3 bg-[#1D9E75] text-white rounded-lg hover:bg-[#178D69] transition-colors">
              Accept
            </button>
            <button className="w-full py-3 bg-white text-[#1A1A1A] border border-[#E5E5E5] rounded-lg hover:bg-[#F3F4F6] transition-colors">
              Counter
            </button>
            <button className="w-full py-3 bg-white text-[#E24B4A] border border-[#E24B4A] rounded-lg hover:bg-[#FEE] transition-colors">
              Decline
            </button>
          </div>
        </div>

        {/* Center: Human Chat */}
        <div className="bg-white rounded-xl flex flex-col h-[600px]">
          {/* Header */}
          <div className="p-6 border-b border-[#E5E5E5]">
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
              Chat with Sarah Chen
            </h2>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {humanMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.sender === "you" ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[70%] ${msg.sender === "you" ? "items-end" : "items-start"}`}>
                  <p className="text-xs text-[#6B6B6B] mb-1">
                    {msg.name} · {msg.time}
                  </p>
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      msg.sender === "you"
                        ? "bg-[#534AB7] text-white"
                        : "bg-[#F3F4F6] text-[#1A1A1A]"
                    }`}
                  >
                    {msg.message}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#E5E5E5]">
            <div className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
              />
              <button
                onClick={handleSend}
                className="px-4 py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right: Agent Negotiation Log */}
        <div className="bg-[#F3F4F6] rounded-xl overflow-hidden h-[600px] flex flex-col">
          {/* Header */}
          <button
            onClick={() => setAgentLogExpanded(!agentLogExpanded)}
            className="p-4 border-b border-[#E5E5E5] flex items-center justify-between hover:bg-[#E5E5E5] transition-colors"
          >
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A', fontFamily: 'monospace' }}>
              Agent Negotiation Log
            </h3>
            {agentLogExpanded ? (
              <ChevronUp className="w-5 h-5 text-[#6B6B6B]" />
            ) : (
              <ChevronDown className="w-5 h-5 text-[#6B6B6B]" />
            )}
          </button>

          {/* Log Content */}
          {agentLogExpanded && (
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {agentMessages.map((msg, idx) => (
                <div key={idx} className="bg-white rounded-lg p-4 border border-[#E5E5E5]">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="px-2 py-1 bg-[#534AB7] text-white text-xs rounded"
                      style={{ fontFamily: 'monospace' }}
                    >
                      Agent {msg.agent}
                    </span>
                  </div>
                  <p className="text-sm text-[#1A1A1A] mb-2" style={{ fontFamily: 'monospace' }}>
                    {msg.message}
                  </p>
                  <p className="text-xs text-[#6B6B6B]" style={{ fontFamily: 'monospace' }}>
                    → {msg.reasoning}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
