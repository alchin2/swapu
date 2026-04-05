import { useParams, Link } from "react-router";
import { ArrowLeft } from "lucide-react";

export function ItemDetails() {
  const { id } = useParams();

  // Mock data
  const item = {
    id,
    name: "Calculus Textbook",
    condition: "Good",
    owner: {
      name: "Sarah Chen",
      university: "State University",
      avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100",
    },
    mainImage: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800",
    thumbnails: [
      "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200",
      "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=200",
      "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=200",
    ],
    lookingFor: ["iClicker", "Dining Dollars", "Mini Fridge", "Bike Lock"],
  };

  const conditionColors = {
    Good: "bg-[#1D9E75] text-white",
    Fair: "bg-[#EF9F27] text-white",
    Poor: "bg-[#E24B4A] text-white",
  };

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
        {/* Left: Images */}
        <div>
          <div className="bg-white rounded-xl overflow-hidden mb-4">
            <img
              src={item.mainImage}
              alt={item.name}
              className="w-full aspect-[4/3] object-cover"
            />
          </div>
          <div className="flex gap-4">
            {item.thumbnails.map((thumb, idx) => (
              <button
                key={idx}
                className="flex-1 bg-white rounded-lg overflow-hidden hover:opacity-75 transition-opacity"
              >
                <img
                  src={thumb}
                  alt={`Thumbnail ${idx + 1}`}
                  className="w-full aspect-square object-cover"
                />
              </button>
            ))}
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

          {/* Owner Info */}
          <div className="bg-white rounded-xl p-6">
            <div className="flex items-center gap-4">
              <img
                src={item.owner.avatar}
                alt={item.owner.name}
                className="w-16 h-16 rounded-full object-cover"
              />
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
                  {item.owner.name}
                </h3>
                <p className="text-[#6B6B6B]">{item.owner.university}</p>
              </div>
            </div>
          </div>

          {/* Looking For */}
          <div className="bg-white rounded-xl p-6">
            <h3 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
              I'm looking for
            </h3>
            <div className="flex flex-wrap gap-2">
              {item.lookingFor.map((tag) => (
                <span
                  key={tag}
                  className="px-4 py-2 bg-[#F3F4F6] text-[#1A1A1A] rounded-full"
                  style={{ borderRadius: "20px" }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

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
