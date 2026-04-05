import { useState } from "react";
import { Link } from "react-router";
import { Search } from "lucide-react";
import Masonry from "react-responsive-masonry";

// Mock data
const mockItems = [
  { id: "1", name: "Calculus Textbook", condition: "Good", category: "textbooks", image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400" },
  { id: "2", name: "iClicker 2", condition: "Fair", category: "electronics", image: "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400" },
  { id: "3", name: "Mini Fridge", condition: "Good", category: "dorm essentials", image: "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400" },
  { id: "4", name: "Concert Tickets", condition: "Good", category: "tickets", image: "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?w=400" },
  { id: "5", name: "Nintendo Switch", condition: "Good", category: "games", image: "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e?w=400" },
  { id: "6", name: "Desk Lamp", condition: "Fair", category: "dorm essentials", image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400" },
  { id: "7", name: "Organic Chemistry Notes", condition: "Good", category: "textbooks", image: "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400" },
  { id: "8", name: "Bike Lock", condition: "Good", category: "transport", image: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400" },
];

const categories = [
  "All",
  "Textbooks",
  "Electronics",
  "Dorm Essentials",
  "Tickets",
  "Games",
  "Transport",
  "Clothing",
];

export function Feed() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  const conditionColors = {
    Good: "bg-[#1D9E75] text-white",
    Fair: "bg-[#EF9F27] text-white",
    Poor: "bg-[#E24B4A] text-white",
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
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
                selectedCategory === category
                  ? "bg-[#534AB7] text-white"
                  : "bg-white text-[#1A1A1A] border border-[#E5E5E5] hover:border-[#534AB7]"
              }`}
              style={{ borderRadius: "20px" }}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Masonry Grid */}
      <Masonry columnsCount={4} gutter="24px">
        {mockItems.map((item) => (
          <Link key={item.id} to={`/item/${item.id}`}>
            <div className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
              <div className="aspect-[4/3] overflow-hidden">
                <img
                  src={item.image}
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
    </div>
  );
}
