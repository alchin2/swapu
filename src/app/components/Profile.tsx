import { useState, useEffect } from "react";
import { Edit, Bot, User as UserIcon, Tag, Check, X } from "lucide-react";
import { authFetch, getUser } from "../auth";

const ALL_CATEGORIES = [
  'textbooks', 'iclicker', 'lab_supplies', 'dining_dollars',
  'electronics', 'dorm_essentials', 'clothing', 'trading_cards',
  'games', 'instruments', 'art_supplies', 'sports_equipment',
  'transport', 'tickets', 'other'
];

const CATEGORY_LABELS: Record<string, string> = {
  textbooks: "Textbooks", iclicker: "iClicker", lab_supplies: "Lab Supplies",
  dining_dollars: "Dining Dollars", electronics: "Electronics",
  dorm_essentials: "Dorm Essentials", clothing: "Clothing",
  trading_cards: "Trading Cards", games: "Games", instruments: "Instruments",
  art_supplies: "Art Supplies", sports_equipment: "Sports Equipment",
  transport: "Transport", tickets: "Tickets", other: "Other",
};

export function Profile() {
  const [userId, setUserId] = useState<string | null>(() => {
    const u = getUser();
    return u?.id ?? null;
  });
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [agentMode, setAgentMode] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("agent_trading_mode") !== "manual";
    }
    return true;
  });
  const [wantedCategories, setWantedCategories] = useState<string[]>([]);
  const [catSaving, setCatSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editCashAmt, setEditCashAmt] = useState("");
  const [editCashPct, setEditCashPct] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all([
      authFetch(`/users/${userId}`).then((res) => { if (!res.ok) throw new Error("Failed to fetch user"); return res.json(); }),
      authFetch(`/users/${userId}/categories`).then((res) => res.ok ? res.json() : []),
    ])
      .then(([userData, cats]) => { setUser(userData); setWantedCategories(cats); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  useEffect(() => {
    const onAuthChange = () => {
      const u = getUser();
      setUserId(u?.id ?? null);
    };

    window.addEventListener("auth_changed", onAuthChange);
    return () => window.removeEventListener("auth_changed", onAuthChange);
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!userId || !user) return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }} className="mb-8">Profile</h1>
      <div className="text-center py-16 text-[#6B6B6B]">No user found. Please log in.</div>
    </div>
  );

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          Profile
        </h1>
      </div>
      <div className="bg-white rounded-xl p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center text-3xl text-gray-500">
            {user.name ? user.name[0] : "?"}
          </div>
          <div className="flex-1">
            {editing ? (
              <input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="text-xl font-semibold border border-[#E5E5E5] rounded-lg px-3 py-1 w-full max-w-xs"
                placeholder="Name"
              />
            ) : (
              <>
                <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>
                  {user.name}
                </h2>
                <div className="text-[#6B6B6B]">{user.email}</div>
              </>
            )}
          </div>
          {editing ? (
            <div className="flex gap-2">
              <button
                disabled={editSaving}
                onClick={async () => {
                  setEditSaving(true);
                  try {
                    const body: any = {};
                    if (editName.trim() && editName.trim() !== user.name) body.name = editName.trim();
                    const amt = editCashAmt === "" ? null : parseFloat(editCashAmt);
                    const pct = editCashPct === "" ? null : parseFloat(editCashPct);
                    if (amt !== (user.max_cash_amt ?? null)) body.max_cash_amt = amt;
                    if (pct !== (user.max_cash_pct ?? null)) body.max_cash_pct = pct;
                    if (Object.keys(body).length > 0) {
                      const res = await authFetch(`/users/${userId}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                      });
                      if (!res.ok) throw new Error("Failed to update profile");
                      const updated = await res.json();
                      setUser(updated);
                    }
                    setEditing(false);
                  } catch (e: any) {
                    setError(e.message);
                  } finally {
                    setEditSaving(false);
                  }
                }}
                className="flex items-center gap-1 px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#433a9e] transition-colors disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                Save
              </button>
              <button
                onClick={() => setEditing(false)}
                className="flex items-center gap-1 px-4 py-2 border border-[#E5E5E5] rounded-lg hover:bg-[#F3F4F6] transition-colors"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => {
                setEditName(user.name || "");
                setEditCashAmt(user.max_cash_amt != null ? String(user.max_cash_amt) : "");
                setEditCashPct(user.max_cash_pct != null ? String(user.max_cash_pct) : "");
                setEditing(true);
              }}
              className="flex items-center gap-2 px-4 py-2 border border-[#E5E5E5] rounded-lg hover:bg-[#F3F4F6] transition-colors"
            >
              <Edit className="w-4 h-4" />
              Edit
            </button>
          )}
        </div>
        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-[#E5E5E5]">
          <div>
            <p className="text-[#6B6B6B] text-sm mb-1">Max Cash Amount</p>
            {editing ? (
              <input
                type="number"
                value={editCashAmt}
                onChange={(e) => setEditCashAmt(e.target.value)}
                className="text-xl font-semibold border border-[#E5E5E5] rounded-lg px-3 py-1 w-full max-w-[160px]"
                placeholder="0"
                min={0}
              />
            ) : (
              <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>{user.max_cash_amt ?? "-"}</p>
            )}
          </div>
          <div>
            <p className="text-[#6B6B6B] text-sm mb-1">Max Cash %</p>
            {editing ? (
              <input
                type="number"
                value={editCashPct}
                onChange={(e) => setEditCashPct(e.target.value)}
                className="text-xl font-semibold border border-[#E5E5E5] rounded-lg px-3 py-1 w-full max-w-[160px]"
                placeholder="0"
                min={0}
                max={100}
              />
            ) : (
              <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>{user.max_cash_pct ?? "-"}</p>
            )}
          </div>
        </div>
      </div>

      {/* Trading Mode Toggle */}
      <div className="bg-white rounded-xl p-8 mt-6">
        <h2 className="font-semibold text-lg mb-4">Trading Mode</h2>
        <div className="flex items-center gap-4">
          <button
            onClick={() => { setAgentMode(true); localStorage.setItem("agent_trading_mode", "agent"); window.dispatchEvent(new Event("agent_mode_changed")); }}
            className={`flex-1 flex items-center justify-center gap-3 py-4 rounded-lg border-2 transition-colors ${
              agentMode
                ? "border-[#534AB7] bg-[#534AB7]/5 text-[#534AB7]"
                : "border-[#E5E5E5] text-[#6B6B6B] hover:border-[#534AB7]/30"
            }`}
          >
            <Bot className="w-6 h-6" />
            <div className="text-left">
              <p className="font-semibold">Agent Trading</p>
              <p className="text-sm opacity-70">AI finds and negotiates deals for you</p>
            </div>
          </button>
          <button
            onClick={() => { setAgentMode(false); localStorage.setItem("agent_trading_mode", "manual"); window.dispatchEvent(new Event("agent_mode_changed")); }}
            className={`flex-1 flex items-center justify-center gap-3 py-4 rounded-lg border-2 transition-colors ${
              !agentMode
                ? "border-[#534AB7] bg-[#534AB7]/5 text-[#534AB7]"
                : "border-[#E5E5E5] text-[#6B6B6B] hover:border-[#534AB7]/30"
            }`}
          >
            <UserIcon className="w-6 h-6" />
            <div className="text-left">
              <p className="font-semibold">Manual Trading</p>
              <p className="text-sm opacity-70">Browse and propose trades yourself</p>
            </div>
          </button>
        </div>
      </div>

      {/* Category Preferences */}
      <div className="bg-white rounded-xl p-8 mt-6">
        <div className="flex items-center gap-3 mb-2">
          <Tag className="w-5 h-5 text-[#534AB7]" />
          <h2 className="font-semibold text-lg">What do you want?</h2>
        </div>
        <p className="text-sm text-[#6B6B6B] mb-4">Select the categories you're looking to receive in trades. The agent uses this to find matches.</p>
        <div className="flex flex-wrap gap-2">
          {ALL_CATEGORIES.map((cat) => {
            const isSelected = wantedCategories.includes(cat);
            return (
              <button
                key={cat}
                disabled={catSaving}
                onClick={() => {
                  const next = isSelected
                    ? wantedCategories.filter((c) => c !== cat)
                    : [...wantedCategories, cat];
                  setWantedCategories(next);
                  setCatSaving(true);
                  authFetch(`/users/${userId}/categories`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ categories: next.length > 0 ? next : ["other"] }),
                  })
                    .catch(() => setWantedCategories(wantedCategories))
                    .finally(() => setCatSaving(false));
                }}
                className={`px-4 py-2 rounded-full text-sm transition-colors ${
                  isSelected
                    ? "bg-[#534AB7] text-white"
                    : "bg-[#F3F4F6] text-[#1A1A1A] hover:bg-[#E5E5E5]"
                } disabled:opacity-50`}
              >
                {CATEGORY_LABELS[cat] || cat}
              </button>
            );
          })}
        </div>
        {wantedCategories.length === 0 && (
          <p className="text-sm text-[#E24B4A] mt-3">Select at least one category so the agent can find trades for you.</p>
        )}
      </div>
    </div>
  );
}
