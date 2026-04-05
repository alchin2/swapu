import { Link, useNavigate } from "react-router";
import { useState, useEffect, useCallback } from "react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Bot, Zap, Loader2 } from "lucide-react";
import { authFetch } from "../auth";

interface Item {
  id: string;
  owner_id: string;
  name: string;
  condition: string;
  image_urls: string[];
  category: string;
  price: number;
  confidence_score: number | null;
}

const FALLBACK_IMAGE = "https://via.placeholder.com/400?text=No+Image";

export function MyItems() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_user_id");
    }
    return null;
  });
  const [myItems, setMyItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [autoDealLoading, setAutoDealLoading] = useState(false);
  const [autoDealResult, setAutoDealResult] = useState<any>(null);
  const [agentMode, setAgentMode] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("agent_trading_mode") !== "manual";
    }
    return true;
  });

  useEffect(() => {
    const onStorage = () => {
      setAgentMode(localStorage.getItem("agent_trading_mode") !== "manual");
    };
    window.addEventListener("storage", onStorage);
    // Also listen for same-tab changes via a custom event
    window.addEventListener("agent_mode_changed", onStorage);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("agent_mode_changed", onStorage);
    };
  }, []);

  const fetchMyItems = useCallback(() => {
    if (!userId) return Promise.resolve();
    return authFetch("/items/")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch items");
        return res.json();
      })
      .then((data) => setMyItems(data.filter((item: Item) => item.owner_id === userId)));
  }, [userId]);

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      setMyItems([]);
      return;
    }
    setLoading(true);
    fetchMyItems()
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId, fetchMyItems]);

  // Poll every 3s while any item is still being priced by the agent
  useEffect(() => {
    const hasPending = myItems.some((item) => item.confidence_score === null);
    if (!hasPending || !userId) return;
    const interval = setInterval(() => {
      fetchMyItems().catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [myItems, userId, fetchMyItems]);

  useEffect(() => {
    const onGuestChange = () => {
      setUserId(localStorage.getItem("guest_user_id"));
    };

    window.addEventListener("guest_user_changed", onGuestChange);
    return () => window.removeEventListener("guest_user_changed", onGuestChange);
  }, []);

  const conditionColors = {
    good: "bg-[#1D9E75] text-white",
    fair: "bg-[#EF9F27] text-white",
    poor: "bg-[#E24B4A] text-white",
  };

  const handleReprice = (itemId: string) => {
    authFetch(`/items/${itemId}/reprice`, { method: "POST" })
      .then((res) => {
        if (!res.ok) throw new Error("Failed to re-price");
        // Set confidence_score to null locally to show spinner
        setMyItems((prev) =>
          prev.map((it) => it.id === itemId ? { ...it, confidence_score: null } : it)
        );
      })
      .catch((err) => setError(err.message));
  };

  const handleAutoDeal = () => {
    if (!userId) return;
    setAutoDealLoading(true);
    setAutoDealResult(null);
    setError("");
    authFetch(`/match/${userId}/auto-deal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then((res) => {
        if (!res.ok) return res.json().then((e) => { throw new Error(e.detail || "Auto deal failed"); });
        return res.json();
      })
      .then((data) => {
        // Navigate to the deal page immediately; negotiation runs in background
        if (data.deal?.id) {
          navigate(`/deal/${data.deal.id}`);
        } else {
          setAutoDealResult(data);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setAutoDealLoading(false));
  };

  if (loading) return <div>Loading...</div>;
  if (!userId) return <div className="text-center py-16 text-[#6B6B6B]">Please select a guest account to view your items.</div>;

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          My Items
        </h1>
        <div className="flex gap-3">
          {agentMode && (
            <button
              onClick={handleAutoDeal}
              disabled={autoDealLoading || myItems.length === 0}
              className="flex items-center gap-2 px-6 py-3 bg-[#1D9E75] text-white rounded-lg hover:bg-[#178A64] transition-colors disabled:opacity-50"
            >
              <Bot className="w-5 h-5" />
              {autoDealLoading ? "Finding Deal..." : "Auto Deal"}
            </button>
          )}
          <Link
            to="/list"
            className="px-6 py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
          >
            List New Item
          </Link>
        </div>
      </div>

      {error && <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">{error}</div>}

      {/* Auto Deal Result Banner */}
      {autoDealResult && (
        <div className="mb-8 bg-[#1D9E75]/10 border border-[#1D9E75] rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <Zap className="w-6 h-6 text-[#1D9E75]" />
            <h3 className="font-semibold text-lg text-[#1D9E75]">Agent Found a Deal!</h3>
          </div>
          <p className="text-[#1A1A1A] mb-2">
            Status: <b>{autoDealResult.deal?.status}</b> · Cash Difference: <b>${autoDealResult.deal?.cash_difference?.toFixed(2)}</b>
          </p>
          {autoDealResult.next_actions && (
            <p className="text-sm text-[#6B6B6B] mb-3">{autoDealResult.next_actions.join(" · ")}</p>
          )}
          <button
            onClick={() => navigate(`/deal/${autoDealResult.deal?.id}`)}
            className="px-6 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
          >
            View Negotiation
          </button>
        </div>
      )}

      <div className="grid grid-cols-4 gap-6">
        {myItems.map((item) => {
          const isPricing = item.confidence_score === null;
          const failedPricing = item.confidence_score === 0;
          return (
          <div key={item.id} className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
            <Link to={`/item/${item.id}`}>
              <div className="aspect-square overflow-hidden cursor-pointer">
                <ImageWithFallback
                  src={item.image_urls[0] || FALLBACK_IMAGE}
                  alt={item.name}
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                />
              </div>
            </Link>
            <div className="p-4">
              <h3 className="mb-1" style={{ fontSize: '16px', fontWeight: 500, color: '#1A1A1A' }}>
                {item.name}
              </h3>
              <div className="flex items-center gap-2 mb-2">
                {isPricing ? (
                  <span className="flex items-center gap-1 text-sm text-[#534AB7]">
                    <Loader2 className="w-3 h-3 animate-spin" /> Pricing...
                  </span>
                ) : (
                  <>
                    <span className="font-semibold text-[#1A1A1A]">${item.price.toFixed(2)}</span>
                    <span className="text-xs text-[#6B6B6B]">{item.category}</span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block px-3 py-1 text-sm rounded-full ${
                    conditionColors[item.condition as keyof typeof conditionColors]
                  }`}
                  style={{ borderRadius: "20px" }}
                >
                  {item.condition}
                </span>
                {failedPricing && (
                  <button
                    onClick={(e) => { e.preventDefault(); handleReprice(item.id); }}
                    className="text-xs px-2 py-1 bg-[#534AB7] text-white rounded-md hover:bg-[#453CA0] transition-colors"
                  >
                    Re-price
                  </button>
                )}
              </div>
            </div>
          </div>
          );
        })}
      </div>
    </div>
  );
}
