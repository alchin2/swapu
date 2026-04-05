import { Link } from "react-router";
import { useState, useEffect } from "react";

interface Deal {
  id: string;
  user1_item_id: string;
  user2_item_id: string;
  cash_difference: number;
  payer_id: string | null;
  status: string;
  created_at: string;
}

export function MyDeals() {
  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_user_id");
    }
    return null;
  });
  const [activeDeals, setActiveDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      setActiveDeals([]);
      return;
    }
    setLoading(true);
    fetch(`/deals/user/${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch deals");
        return res.json();
      })
      .then((data) => setActiveDeals(data))
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

  const statusColors = {
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
        {activeDeals.map((deal) => (
          <Link
            key={deal.id}
            to={`/deal/${deal.id}`}
            className="block bg-white rounded-xl p-6 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="mb-2"><b>Deal ID:</b> {deal.id}</div>
                <div><b>Status:</b> {deal.status}</div>
                <div><b>Cash Difference:</b> ${deal.cash_difference}</div>
                <div><b>Created:</b> {new Date(deal.created_at).toLocaleString()}</div>
              </div>
              <span
                className={`px-4 py-2 rounded-full ${
                  statusColors[deal.status as keyof typeof statusColors]
                }`}
                style={{ borderRadius: "20px" }}
              >
                {deal.status.charAt(0).toUpperCase() + deal.status.slice(1)}
              </span>
            </div>
          </Link>
        ))}
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
