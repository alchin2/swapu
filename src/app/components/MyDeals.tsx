import { Link } from "react-router";

export function MyDeals() {
  // Mock data
  const activeDeals = [
    {
      id: "1",
      yourItem: { name: "iClicker 2", image: "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=200" },
      theirItem: { name: "Calculus Textbook", image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200" },
      otherUser: "Sarah Chen",
      cashDifference: 5,
      direction: "pay",
      status: "negotiating",
      lastUpdate: "2 hours ago",
    },
    {
      id: "2",
      yourItem: { name: "Desk Lamp", image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=200" },
      theirItem: { name: "Bike Lock", image: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=200" },
      otherUser: "Mike Rodriguez",
      cashDifference: 3,
      direction: "receive",
      status: "pending",
      lastUpdate: "1 day ago",
    },
    {
      id: "3",
      yourItem: { name: "Mini Fridge", image: "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=200" },
      theirItem: { name: "Concert Tickets", image: "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?w=200" },
      otherUser: "Emily Zhang",
      cashDifference: 0,
      direction: "even",
      status: "accepted",
      lastUpdate: "3 hours ago",
    },
  ];

  const statusColors = {
    pending: "bg-[#6B6B6B] text-white",
    negotiating: "bg-[#534AB7] text-white",
    accepted: "bg-[#1D9E75] text-white",
    confirmed: "bg-[#1D9E75] text-white",
    declined: "bg-[#E24B4A] text-white",
  };

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
              {/* Deal Summary */}
              <div className="flex items-center gap-6 flex-1">
                {/* Items */}
                <div className="flex items-center gap-4">
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

                {/* Details */}
                <div className="flex-1">
                  <h3 className="mb-1" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
                    Trade with {deal.otherUser}
                  </h3>
                  <p className="text-[#6B6B6B] text-sm mb-2">
                    {deal.yourItem.name} ↔ {deal.theirItem.name}
                  </p>
                  <div className="flex items-center gap-3">
                    {deal.direction === "even" ? (
                      <span className="text-sm text-[#1A1A1A]">Even trade</span>
                    ) : (
                      <span className={`text-sm ${deal.direction === "receive" ? "text-[#1D9E75]" : "text-[#534AB7]"}`}>
                        {deal.direction === "receive" ? "They pay you" : "You pay"} ${deal.cashDifference.toFixed(2)}
                      </span>
                    )}
                    <span className="text-[#6B6B6B] text-sm">· {deal.lastUpdate}</span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
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
