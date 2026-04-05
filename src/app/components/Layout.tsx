import { Link, Outlet, useLocation, useNavigate } from "react-router";
import { Home, Package, Handshake, User, LogOut } from "lucide-react";
import { useState, useEffect } from "react";
import { getUser, clearAuth } from "../auth";

export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const loadUser = () => {
      const user = getUser();
      setUserName(user?.name ?? null);
    };
    loadUser();
    window.addEventListener("auth_changed", loadUser);
    return () => window.removeEventListener("auth_changed", loadUser);
  }, []);

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  const navItems = [
    { path: "/", label: "Feed", icon: Home },
    { path: "/my-items", label: "My Items", icon: Package },
    { path: "/my-deals", label: "My Deals", icon: Handshake },
    { path: "/profile", label: "Profile", icon: User },
  ];

  return (
    <div className="flex h-screen bg-[#F9F9F9]">
      {/* Left Sidebar */}
      <aside className="w-[240px] bg-white border-r border-[#E5E5E5] flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-[#E5E5E5]">
          <h1 className="text-[#534AB7] tracking-tight" style={{ fontSize: '24px', fontWeight: 600 }}>
            SwapU
          </h1>
          {userName ? (
            <p className="text-sm text-[#6B6B6B] mt-1 truncate">Logged in as <b>{userName}</b></p>
          ) : (
            <p className="text-sm text-[#6B6B6B] mt-1">Welcome</p>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.path === location.pathname;

            return (
              <Link
                key={item.label}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-[#534AB7] text-white"
                    : "text-[#1A1A1A] hover:bg-[#F3F4F6]"
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-[#E5E5E5] space-y-2">
          <Link
            to="/list"
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#534AB7] text-white rounded-lg hover:bg-[#453CA0] transition-colors"
          >
            <Package className="w-5 h-5" />
            List an Item
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 border border-[#E5E5E5] text-[#6B6B6B] rounded-lg hover:bg-[#F3F4F6] transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Log Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
