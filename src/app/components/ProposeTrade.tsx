import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router";
import { ArrowLeft, ArrowRightLeft, AlertCircle } from "lucide-react";

export function ProposeTrade() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState("1");

  // Mock data
  const theirItem = {
    id,
    name: "Calculus Textbook",
    image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
    estimatedValue: 45,
  };

  const myItems = [
    { id: "1", name: "iClicker 2", image: "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400", estimatedValue: 40 },
    { id: "2", name: "Mini Fridge", image: "https://images.unsplash.com/photo-1584568694244-14fbdf83bd30?w=400", estimatedValue: 65 },
    { id: "3", name: "Desk Lamp", image: "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400", estimatedValue: 20 },
  ];

  const selectedMyItem = myItems.find((item) => item.id === selectedItem)!;
  const cashDifference = theirItem.estimatedValue - selectedMyItem.estimatedValue;
  const exceedsLimit = Math.abs(cashDifference) > 10; // Mock limit

  const handleSubmit = () => {
    if (!exceedsLimit) {
      alert("Trade proposal sent!");
      navigate("/profile");
    }
  };

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

      {/* Warning Banner */}
      {exceedsLimit && (
        <div className="mb-6 p-4 bg-[#FEF3C7] border border-[#EF9F27] rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-[#EF9F27] flex-shrink-0 mt-0.5" />
          <div>
            <p style={{ fontWeight: 600, color: '#1A1A1A' }}>
              This trade exceeds your cash difference limit.
            </p>
            <p className="text-sm text-[#6B6B6B] mt-1">
              You can still send the proposal, but you may want to adjust your preferences or choose a different item.
            </p>
          </div>
        </div>
      )}

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
          <div className="border border-[#E5E5E5] rounded-xl overflow-hidden">
            <img
              src={selectedMyItem.image}
              alt={selectedMyItem.name}
              className="w-full aspect-[4/3] object-cover"
            />
            <div className="p-4">
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
                {selectedMyItem.name}
              </h3>
            </div>
          </div>
        </div>

        {/* Center: Swap Icon + Cash Difference */}
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-[#534AB7] rounded-full flex items-center justify-center">
            <ArrowRightLeft className="w-8 h-8 text-white" />
          </div>
          <div className="text-center">
            {cashDifference > 0 ? (
              <div>
                <p className="text-[#6B6B6B] text-sm">You pay</p>
                <p className="text-[#534AB7]" style={{ fontSize: '24px', fontWeight: 600 }}>
                  ${Math.abs(cashDifference).toFixed(2)}
                </p>
              </div>
            ) : cashDifference < 0 ? (
              <div>
                <p className="text-[#6B6B6B] text-sm">They pay you</p>
                <p className="text-[#1D9E75]" style={{ fontSize: '24px', fontWeight: 600 }}>
                  ${Math.abs(cashDifference).toFixed(2)}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-[#6B6B6B] text-sm">Even trade</p>
                <p className="text-[#1A1A1A]" style={{ fontSize: '24px', fontWeight: 600 }}>
                  $0.00
                </p>
              </div>
            )}
          </div>
        </div>

        {/* You Receive */}
        <div className="bg-white rounded-xl p-6">
          <h2 className="mb-4" style={{ fontSize: '18px', fontWeight: 600, color: '#1A1A1A' }}>
            You receive
          </h2>

          {/* Their Item Card */}
          <div className="border border-[#E5E5E5] rounded-xl overflow-hidden">
            <img
              src={theirItem.image}
              alt={theirItem.name}
              className="w-full aspect-[4/3] object-cover"
            />
            <div className="p-4">
              <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#1A1A1A' }}>
                {theirItem.name}
              </h3>
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
