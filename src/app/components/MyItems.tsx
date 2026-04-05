import { Link } from "react-router";

export function MyItems() {
  // Mock data
  const myItems = [
    { id: "1", name: "iClicker 2", condition: "Fair", image: "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400" },
    { id: "2", name: "Mini Fridge", condition: "Good", image: "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400" },
    { id: "3", name: "Desk Lamp", condition: "Fair", image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400" },
    { id: "4", name: "Organic Chemistry Notes", condition: "Good", image: "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400" },
    { id: "5", name: "Bike Lock", condition: "Good", image: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400" },
  ];

  const conditionColors = {
    Good: "bg-[#1D9E75] text-white",
    Fair: "bg-[#EF9F27] text-white",
    Poor: "bg-[#E24B4A] text-white",
  };

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          My Items
        </h1>
        <Link
          to="/list"
          className="px-6 py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
        >
          List New Item
        </Link>
      </div>

      <div className="grid grid-cols-4 gap-6">
        {myItems.map((item) => (
          <Link key={item.id} to={`/item/${item.id}`}>
            <div className="bg-white rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer">
              <div className="aspect-square overflow-hidden">
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
      </div>
    </div>
  );
}
