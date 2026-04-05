import { useState, useEffect } from "react";
import { Edit } from "lucide-react";
import { GuestLogin } from "./GuestLogin";

export function Profile() {
  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("guest_user_id");
    }
    return null;
  });
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showGuestLogin, setShowGuestLogin] = useState(false);

  useEffect(() => {
    if (!userId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetch(`/users/${userId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch user");
        return res.json();
      })
      .then((data) => setUser(data))
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

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!userId) return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>Profile</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowGuestLogin((s) => !s)}
            className="px-4 py-2 border border-[#E5E5E5] rounded-lg bg-white hover:bg-[#F3F4F6]"
          >
            Switch account
          </button>
        </div>
      </div>
      {showGuestLogin && <div className="mb-6"><GuestLogin /></div>}
      <div className="text-center py-16 text-[#6B6B6B]">Please select an account.</div>
    </div>
  );
  if (!user) return <div>No user found.</div>;

  return (
    <div className="max-w-[1100px] mx-auto px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1A1A1A' }}>
          Profile
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowGuestLogin((s) => !s)}
            className="px-4 py-2 border border-[#E5E5E5] rounded-lg bg-white hover:bg-[#F3F4F6]"
          >
            Switch account
          </button>
        </div>
      </div>
      {showGuestLogin && (
        <div className="mb-6">
          <GuestLogin />
        </div>
      )}
      <div className="bg-white rounded-xl p-8">
        <div className="flex items-center gap-4 mb-6">
          {/* Avatar placeholder, as API does not provide avatar */}
          <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center text-3xl text-gray-500">
            {user.name ? user.name[0] : "?"}
          </div>
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>
              {user.name}
            </h2>
            <div className="text-[#6B6B6B]">{user.email}</div>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-[#E5E5E5] rounded-lg hover:bg-[#F3F4F6] transition-colors">
            <Edit className="w-4 h-4" />
            Edit
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4 pt-6 border-t border-[#E5E5E5]">
          <div>
            <p className="text-[#6B6B6B] text-sm mb-1">Max Cash Amount</p>
            <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>{user.max_cash_amt ?? "-"}</p>
          </div>
          <div>
            <p className="text-[#6B6B6B] text-sm mb-1">Max Cash %</p>
            <p style={{ fontSize: '24px', fontWeight: 600, color: '#1A1A1A' }}>{user.max_cash_pct ?? "-"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
