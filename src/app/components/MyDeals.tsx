import { Link } from "react-router";
import { useState, useEffect } from "react";
import { ArrowRightLeft } from "lucide-react";
import { authFetch } from "../auth";

interface Deal {
  id: string;
  user1_id: string;
  user2_id: string;
  user1_item_id: string;
  user2_item_id: string;
  cash_difference: number;
  payer_id: string | null;
  status: string;
  created_at: string;
}

interface ItemInfo {
  id: string;
  name: string;
  category: string;
}

export function MyDeals() {
  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_user_id");
    }
    return null;
  });
  const [activeDeals, setActiveDeals] = useState<Deal[]>([]);
  const [itemNames, setItemNames] = useState<Record<string, ItemInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      setActiveDeals([]);
      return;
    }
    setLoading(true);
    authFetch(`/deals/user/${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch deals");
        return res.json();
      })
      .then((deals) => {
        setActiveDeals(deals);
        // Fetch item names for all deals
        const itemIds = new Set<string>();
        deals.forEach((d: Deal) => { itemIds.add(d.user1_item_id); itemIds.add(d.user2_item_id); });
        const fetches = Array.from(itemIds).map((id) =>
          authFetch(`/items/${id}`).then((r) => r.ok ? r.json() : null).catch(() => null)
        );
        return Promise.all(fetches).then((items) => {
          const map: Record<string, ItemInfo> = {};
          items.forEach((item) => { if (item) map[item.id] = item; });
          setItemNames(map);
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  useEffect(() => {
    const onGuestChange = () => {
      setUserId(localStorage.getItem("guest_user_id"));
    };

    window.addEventListener("guest_user_changed", onGuestChange);
    return () => window.removeEventListener("guest_user_changed", onGuestChange);
  }, []);

  const statusColors: Record<string, string> = {
    pending: "bg-[#6B6B6B] text-white",
    negotiating: "bg-[#534AB7] text-white",
    accepted: "bg-[#1D9E75] text-white",
    confirmed: "bg-[#1D9E75] text-white",
    declined: "bg-[#E24B4A] text-white",
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!userId) return <div className="text-center py-16 text-[#6B6B6B]">Please select a guest account to view your deals.</div>;

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <h1 className="mb-8" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
        My Deals
      </h1>
      <div className="space-y-4">
        {activeDeals.map((deal) => {
          const isUser1 = deal.user1_id === userId;
          const myItemId = isUser1 ? deal.user1_item_id : deal.user2_item_id;
          const theirItemId = isUser1 ? deal.user2_item_id : deal.user1_item_id;
          const myItem = itemNames[myItemId];
          const theirItem = itemNames[theirItemId];

          return (
            <Link
              key={deal.id}
              to={`/deal/${deal.id}`}
              className="block bg-white rounded-xl p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className="flex items-center gap-3 flex-1">
                    <div>
                      <p className="text-xs text-[#6B6B6B]">You offer</p>
                      <p className="font-semibold">{myItem?.name ?? "Loading..."}</p>
                      {myItem && <p className="text-xs text-[#6B6B6B]">{myItem.category}</p>}
                    </div>
                    <ArrowRightLeft className="w-5 h-5 text-[#534AB7] flex-shrink-0" />
                    <div>
                      <p className="text-xs text-[#6B6B6B]">You receive</p>
                      <p className="font-semibold">{theirItem?.name ?? "Loading..."}</p>
                      {theirItem && <p className="text-xs text-[#6B6B6B]">{theirItem.category}</p>}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-[#534AB7] font-bold">${deal.cash_difference?.toFixed(2)}</p>
                    <p className="text-xs text-[#6B6B6B]">{new Date(deal.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <span
                  className={`ml-4 px-4 py-2 rounded-full flex-shrink-0 ${statusColors[deal.status] || "bg-gray-200"}`}
                  style={{ borderRadius: "20px" }}
                >
                  {deal.status.charAt(0).toUpperCase() + deal.status.slice(1)}
                </span>
              </div>
            </Link>
          );
        })}
      </div>
      {activeDeals.length === 0 && (
        <div className="text-center py-16">
          <p className="text-[#6B6B6B] mb-6">You don't have any active deals yet.</p>
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
          >
            Browse Items
          </Link>
        </div>
      )}
    </div>
  );
}
