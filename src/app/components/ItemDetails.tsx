import { useParams, Link } from "react-router";
import { ArrowLeft, Loader2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { authFetch } from "../auth";

const FALLBACK_IMAGE = "https://via.placeholder.com/800x600?text=No+Image";

export function ItemDetails() {
  const { id } = useParams();
  const [item, setItem] = useState<any>(null);
  const [owner, setOwner] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchItem = useCallback(() => {
    return authFetch(`/items/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch item");
        return res.json();
      })
      .then((data) => {
        setItem(data);
        return data;
      });
  }, [id]);

  useEffect(() => {
    setLoading(true);
    fetchItem()
      .then((data) => {
        if (data.owner_id) {
          authFetch(`/users/${data.owner_id}`)
            .then((res) => {
              if (!res.ok) throw new Error("Failed to fetch owner");
              return res.json();
            })
            .then((userData) => setOwner(userData))
            .catch(() => setOwner(null))
            .finally(() => setLoading(false));
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id, fetchItem]);

  // Poll while item is still being priced
  useEffect(() => {
    if (!item) return;
    if (item.confidence_score !== null) return;
    const interval = setInterval(() => {
      fetchItem().catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [item, fetchItem]);

  const conditionColors = {
    good: "bg-[#1D9E75] text-white",
    fair: "bg-[#EF9F27] text-white",
    poor: "bg-[#E24B4A] text-white",
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!item) return <div>No item found.</div>;

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      {/* Back Button */}
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-[#6B6B6B] hover:text-[#1A1A1A] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Feed
      </Link>

      {/* Two-column layout */}
      <div className="grid grid-cols-[55%_45%] gap-8">
        {/* Left: Image */}
        <div>
          <div className="bg-white rounded-xl overflow-hidden mb-4">
            <ImageWithFallback
              src={item.image_urls?.[0] || FALLBACK_IMAGE}
              alt={item.name}
              className="w-full aspect-[4/3] object-cover"
            />
          </div>
        </div>

        {/* Right: Details */}
        <div className="space-y-6">
          {/* Item Name & Condition */}
          <div>
            <h1 className="mb-3" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
              {item.name}
            </h1>
            <span
              className={`inline-block px-4 py-2 rounded-full ${
                conditionColors[item.condition as keyof typeof conditionColors]
              }`}
              style={{ borderRadius: "20px" }}
            >
              {item.condition}
            </span>
          </div>

          {/* Show category and price if available */}
          <div className="bg-white rounded-xl p-6">
            {item.confidence_score === null ? (
              <div className="flex items-center gap-2 text-[#534AB7]">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Agent is finding the best price and category...</span>
              </div>
            ) : (
              <>
                <div className="mb-2"><b>Category:</b> {item.category}</div>
                <div className="mb-2"><b>Price:</b> ${Number(item.price).toFixed(2)}</div>
                {item.confidence_score === 0 && (
                  <p className="text-sm text-[#EF9F27]">Pricing agent couldn't determine an accurate price. You can re-price from My Items.</p>
                )}
              </>
            )}
          </div>

          {/* Owner Info */}
          {owner && (
            <div className="bg-white rounded-xl p-6">
              <div className="mb-2"><b>Owner:</b> {owner.name} ({owner.email})</div>
              {owner.looking_for_categories && owner.looking_for_categories.length > 0 && (
                <div>
                  <b>Looking for categories:</b>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {owner.looking_for_categories.map((cat: string) => (
                      <span key={cat} className="px-3 py-1 bg-[#F3F4F6] rounded-full text-[#1A1A1A]">
                        {cat}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Propose Trade Button */}
          <Link
            to={`/propose/${id}`}
            className="block w-full py-4 bg-[#534AB7] text-white text-center rounded-lg hover:bg-[#453CA0] transition-colors"
            style={{ fontSize: '18px', fontWeight: 600 }}
          >
            Propose Trade
          </Link>
        </div>
      </div>
    </div>
  );
}
