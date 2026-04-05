import { useState, useEffect } from "react";
import { Link } from "react-router";
import { Search } from "lucide-react";
import Masonry from "react-responsive-masonry";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { authFetch } from "../auth";

const FALLBACK_IMAGE = "https://via.placeholder.com/400?text=No+Image";

type FeedItem = {
  id: string;
  name: string;
  category: string;
  condition: string;
  image_urls?: string[];
};

const CATEGORY_MAP: Record<string, string> = {
  All: "All",
  textbooks: "Textbooks",
  iclicker: "iClicker",
  lab_supplies: "Lab Supplies",
  dining_dollars: "Dining Dollars",
  electronics: "Electronics",
  dorm_essentials: "Dorm Essentials",
  clothing: "Clothing",
  trading_cards: "Trading Cards",
  games: "Games",
  instruments: "Instruments",
  art_supplies: "Art Supplies",
  sports_equipment: "Sports Equipment",
  transport: "Transport",
  tickets: "Tickets",
  other: "Other",
};

const categories = Object.keys(CATEGORY_MAP);

export function Feed() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    authFetch("/items/")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch items");
        return res.json();
      })
      .then((data) => setItems(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filteredItems = items.filter((item) => {
    const matchesCategory =
      selectedCategory === "All" ||
      (item.category && item.category.toLowerCase() === selectedCategory.toLowerCase());
    const matchesSearch =
      item.name && item.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const conditionColors = {
    good: "bg-[#1D9E75] text-white",
    fair: "bg-[#EF9F27] text-white",
    poor: "bg-[#E24B4A] text-white",
  };

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      {/* Search and Filters */}
      <div className="mb-8 space-y-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B6B6B]" />
          <input
            type="text"
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-white border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
          />
        </div>
        {/* Category Pills */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {categories.map((catKey) => (
            <button
              key={catKey}
              onClick={() => setSelectedCategory(catKey)}
              className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
                selectedCategory === catKey
                  ? "bg-[#534AB7] text-white"
                  : "bg-white text-[#1A1A1A] border border-[#E5E5E5] hover:border-[#534AB7]"
              }`}
              style={{ borderRadius: "20px" }}
            >
              {CATEGORY_MAP[catKey]}
            </button>
          ))}
        </div>
      </div>
      {/* Masonry Grid */}
      {loading ? (
        <div>Loading...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : (
        <Masonry columnsCount={4} gutter="24px">
          {filteredItems.map((item) => (
            <Link key={item.id} to={`/item/${item.id}`}>
              <div className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
                <div className="aspect-[4/3] overflow-hidden">
                  <ImageWithFallback
                    src={item.image_urls?.[0] || FALLBACK_IMAGE}
                    alt={item.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="p-4">
                  <h3 className="mb-2" style={{ fontSize: '16px', fontWeight: 500, color: '#1A1A1A' }}>
                    {item.name}
                  </h3>
                  <span
                    className={`inline-block px-3 py-1 text-sm rounded-full ${
                      conditionColors[item.condition as keyof typeof conditionColors]
                    }`}
                    style={{ borderRadius: "20px" }}
                  >
                    {item.condition}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </Masonry>
      )}
    </div>
  );
}
