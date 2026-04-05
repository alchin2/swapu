import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { ArrowLeft, ArrowRightLeft } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { authFetch } from "../auth";

const FALLBACK_IMAGE = "https://via.placeholder.com/800x600?text=No+Image";

type TradeItem = {
  id: string;
  owner_id: string;
  name: string;
  price: number;
  image_urls?: string[];
};

export function ProposeTrade() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [theirItem, setTheirItem] = useState<TradeItem | null>(null);
  const [myItems, setMyItems] = useState<TradeItem[]>([]);
  const [selectedItem, setSelectedItem] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_user_id");
    }
    return null;
  });

  useEffect(() => {
    const onGuestChange = () => {
      setUserId(localStorage.getItem("guest_user_id"));
    };
    window.addEventListener("guest_user_changed", onGuestChange);
    return () => window.removeEventListener("guest_user_changed", onGuestChange);
  }, []);

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setCurrentData();

    function setCurrentData() {
      Promise.all([
        authFetch(`/items/${id}`).then((res) => {
          if (!res.ok) throw new Error("Failed to fetch item");
          return res.json();
        }),
        authFetch("/items/").then((res) => {
          if (!res.ok) throw new Error("Failed to fetch my items");
          return res.json();
        })
      ])
        .then(([itemData, myItemsData]) => {
          setTheirItem(itemData);
          const ownedItems = myItemsData.filter((item: TradeItem) => item.owner_id === userId);
          setMyItems(ownedItems);
          setSelectedItem(ownedItems[0]?.id || "");
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [id, userId]);

  const selectedMyItem = myItems.find((item) => item.id === selectedItem);
  
  // Calculate price differential. Positive means their item is more expensive (we pay them).
  // Negative means our item is more expensive (they pay us).
  const cashDifferenceCalc = theirItem && selectedMyItem ? (theirItem.price - selectedMyItem.price) : 0;
  const payerId = cashDifferenceCalc > 0 && userId ? userId : (theirItem ? theirItem.owner_id : null);
  const cashDifference = Math.abs(cashDifferenceCalc);

  const handleSubmit = () => {
    if (theirItem && selectedMyItem && userId) {
      authFetch("/deals/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user1_id: userId,
          user2_id: theirItem.owner_id,
          user1_item_id: selectedMyItem.id,
          user2_item_id: theirItem.id,
          cash_difference: cashDifference,
          payer_id: cashDifference > 0 ? payerId : null,
          status: "pending"
        }),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to propose trade");
          return res.json();
        })
        .then((data) => navigate(`/deal/${data.id}`))
        .catch((err) => setError(err.message));
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!userId) return (
    <div className="max-w-[1100px] mx-auto px-8 py-8 text-center py-16 text-[#6B6B6B]">
      Please select an account from your Profile first to propose a trade.
    </div>
  );
  if (error) return <div className="text-red-500">{error}</div>;
  if (!theirItem || myItems.length === 0) return <div>No items found. (Ensure you have an item to trade)</div>;

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      {/* Back Button */}
      <Link
        to={`/item/${id}`}
        className="inline-flex items-center gap-2 text-[#6B6B6B] hover:text-[#1A1A1A] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Item
      </Link>

      <h1 className="mb-8" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
        Propose Trade
      </h1>

      {/* Side-by-side panels */}
      <div className="grid grid-cols-[1fr_auto_1fr] gap-8 items-center">
        {/* You Offer */}
        <div className="bg-white rounded-xl p-6">
          <h2 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
            You offer
          </h2>

          {/* Dropdown to select item */}
          <select
            value={selectedItem}
            onChange={(e) => setSelectedItem(e.target.value)}
            className="w-full px-4 py-3 border border-[#E5E5E5] rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
          >
            {myItems.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>

          {/* Selected Item Card */}
          {selectedMyItem && (
            <div className="border border-[#E5E5E5] rounded-xl overflow-hidden">
              <ImageWithFallback
                src={selectedMyItem.image_urls?.[0] || FALLBACK_IMAGE}
                alt={selectedMyItem.name}
                className="w-full aspect-[4/3] object-cover"
              />
              <div className="p-4">
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
                  {selectedMyItem.name}
                </h3>
                <div>Price: ${selectedMyItem.price}</div>
              </div>
            </div>
          )}
        </div>

        {/* Center: Swap Icon + Cash Difference */}
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="w-16 h-16 bg-[#534AB7] rounded-full flex items-center justify-center">
            <ArrowRightLeft className="w-8 h-8 text-white" />
          </div>
          <div className="text-center">
            <div>
              <p className="text-[#6B6B6B] text-sm">Cash difference</p>
              <p className="text-[#534AB7]" style={{ fontSize: '24px', fontWeight: 600 }}>
                ${cashDifference.toFixed(2)}
              </p>
              {cashDifference > 0 && payerId && (
                <p className="text-sm mt-1 text-[#1A1A1A]">
                  <span className="font-bold">
                    {payerId === userId ? "You pay them" : "They pay you"}
                  </span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* You Receive */}
        <div className="bg-white rounded-xl p-6">
          <h2 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
            You receive
          </h2>

          {/* Their Item Card */}
          <div className="border border-[#E5E5E5] rounded-xl overflow-hidden">
            <ImageWithFallback
              src={theirItem.image_urls?.[0] || FALLBACK_IMAGE}
              alt={theirItem.name}
              className="w-full aspect-[4/3] object-cover"
            />
            <div className="p-4">
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
                {theirItem.name}
              </h3>
              <div>Price: ${theirItem.price}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Send Proposal Button */}
      <div className="mt-8 flex justify-center">
        <button
          onClick={handleSubmit}
          className="px-12 py-4 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
          style={{ fontSize: '18px', fontWeight: 600 }}
        >
          Send Proposal
        </button>
      </div>
    </div>
  );
}
