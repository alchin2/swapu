import { useState } from "react";
import { useNavigate, Link } from "react-router";
import { setAuth } from "../auth";

export function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }
      const data = await res.json();
      setAuth(data.access_token, data.user);
      navigate("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F9F9F9]">
      <div className="w-full max-w-md bg-white rounded-xl p-8 shadow-sm">
        <h1 className="text-[#534AB7] text-center mb-2" style={{ fontSize: "28px", fontWeight: 600 }}>
          SwapU
        </h1>
        <p className="text-center text-[#6B6B6B] mb-8">Create your account</p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 rounded-lg px-4 py-3 mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-[#6B6B6B] mb-1 block">Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="text-sm text-[#6B6B6B] mb-1 block">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
              placeholder="you@ucsd.edu"
            />
          </div>
          <div>
            <label className="text-sm text-[#6B6B6B] mb-1 block">Password</label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-[#E5E5E5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#534AB7]"
              placeholder="At least 6 characters"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors disabled:opacity-50 font-medium"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-[#6B6B6B] mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-[#534AB7] hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
