import { useState } from "react";
import { Edit } from "lucide-react";

const CATEGORIES = [
  "Textbooks",
  "iClicker",
  "Dining Dollars",
  "Electronics",
  "Dorm Essentials",
  "Clothing",
  "Trading Cards",
  "Games",
  "Instruments",
  "Art Supplies",
  "Sports Equipment",
  "Transport",
  "Tickets",
  "Other",
];

export function Profile() {
  const [lookingFor, setLookingFor] = useState(["Textbooks", "iClicker", "Dining Dollars"]);
  const [limitType, setLimitType] = useState<"percentage" | "fixed">("percentage");
  const [limitValue, setLimitValue] = useState("20");

  // Mock data
  const user = {
    name: "Alex Johnson",
    university: "State University",
    avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200",
  };

  const toggleCategory = (category: string) => {
    setLookingFor((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <h1 className="mb-8" style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
        Profile & Preferences
      </h1>

      {/* Two-column layout */}
      <div className="grid grid-cols-[50%_50%] gap-8">
        {/* Left Column - User Info */}
        <div className="bg-white rounded-xl p-8">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <img
                src={user.avatar}
                alt={user.name}
                className="w-24 h-24 rounded-full object-cover"
              />
              <div>
                <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>
                  {user.name}
                </h2>
                <p className="text-[#6B6B6B]">{user.university}</p>
              </div>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 border border-[#E5E5E5] rounded-lg hover:bg-[#F3F4F6] transition-colors">
              <Edit className="w-4 h-4" />
              Edit
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 pt-6 border-t border-[#E5E5E5]">
            <div>
              <p className="text-[#6B6B6B] text-sm mb-1">Items Listed</p>
              <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>5</p>
            </div>
            <div>
              <p className="text-[#6B6B6B] text-sm mb-1">Active Deals</p>
              <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>3</p>
            </div>
            <div>
              <p className="text-[#6B6B6B] text-sm mb-1">Completed</p>
              <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>12</p>
            </div>
          </div>
        </div>

        {/* Right Column - I'm Looking For */}
        <div className="bg-white rounded-xl p-8">
          <h3 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
            I'm looking for
          </h3>
          <p className="text-[#6B6B6B] text-sm mb-4">
            Select the categories you're interested in to help match you with relevant trades.
          </p>
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((category) => {
              const isSelected = lookingFor.includes(category);
              return (
                <button
                  key={category}
                  onClick={() => toggleCategory(category)}
                  className={`px-3 py-2 rounded-full text-sm transition-colors ${
                    isSelected
                      ? "bg-[#534AB7] text-white"
                      : "bg-[#F3F4F6] text-[#1A1A1A] hover:bg-[#E5E5E5]"
                  }`}
                  style={{ borderRadius: "20px" }}
                >
                  {category}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Cash Difference Limit - Full Width */}
      <div className="bg-white rounded-xl p-8 mt-8">
        <h3 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
          Cash difference limit
        </h3>
        <p className="text-[#6B6B6B] text-sm mb-6">
          Set the maximum cash difference you're willing to pay or accept in a trade.
        </p>

        <div className="max-w-[600px]">
          {/* Segmented Control */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setLimitType("percentage")}
              className={`flex-1 py-3 rounded-lg transition-colors ${
                limitType === "percentage"
                  ? "bg-[#534AB7] text-white"
                  : "bg-[#F3F4F6] text-[#1A1A1A]"
              }`}
            >
              % of item value
            </button>
            <button
              onClick={() => setLimitType("fixed")}
              className={`flex-1 py-3 rounded-lg transition-colors ${
                limitType === "fixed"
                  ? "bg-[#534AB7] text-white"
                  : "bg-[#F3F4F6] text-[#1A1A1A]"
              }`}
            >
              Fixed amount ($)
            </button>
          </div>

          {/* Input */}
          <div className="relative mb-3">
            {limitType === "fixed" && (
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#6B6B6B]">
                $
              </span>
            )}
            <input
              type="number"
              value={limitValue}
              onChange={(e) => setLimitValue(e.target.value)}
              className={`w-full ${
                limitType === "fixed" ? "pl-8 pr-4" : "px-4"
              } py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]`}
            />
            {limitType === "percentage" && (
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[#6B6B6B]">
                %
              </span>
            )}
          </div>

          {/* Helper Text */}
          <p className="text-sm text-[#6B6B6B]">
            {limitType === "percentage"
              ? `e.g. ${limitValue}% means you'll accept trades where the difference is within ${limitValue}% of your item's value.`
              : `e.g. $${limitValue} means you'll never pay or receive more than $${limitValue} in a trade.`}
          </p>
        </div>
      </div>
    </div>
  );
}
