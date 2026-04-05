import { useState, useEffect } from "react";

export function GuestLogin() {
  const [users, setUsers] = useState<any[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch("/users")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch users");
        return res.json();
      })
      .then((data) => setUsers(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("guest_user_id");
    if (stored) setSelected(stored);
  }, []);

  function login() {
    if (!selected) return;
    localStorage.setItem("guest_user_id", selected);

    const selectedUser = users.find((u) => u.id === selected);
    if (selectedUser) {
      console.log(
        `Switched guest user to: ${selectedUser.name} (${selectedUser.id})`
      );
    }

    // Notify other components to refresh user-dependent data without a full reload
    window.dispatchEvent(new Event("guest_user_changed"));
  }

  if (loading) return <div>Loading accounts...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="p-4 border-b border-[#E5E5E5]">
      <label className="text-sm text-[#6B6B6B] mb-2 block">Continue as</label>
      <div className="flex gap-2 items-center">
        <select
          value={selected ?? ""}
          onChange={(e) => setSelected(e.target.value)}
          className="px-4 py-2 bg-white border border-[#E5E5E5] rounded-lg"
        >
          <option value="">Select account...</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name} — {u.email}
            </option>
          ))}
        </select>
        <button
          onClick={login}
          className="px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}
