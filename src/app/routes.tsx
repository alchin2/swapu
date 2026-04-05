import { createBrowserRouter, Navigate } from "react-router";
import { Layout } from "./components/Layout";
import { Feed } from "./components/Feed";
import { ItemDetails } from "./components/ItemDetails";
import { ListItem } from "./components/ListItem";
import { ProposeTrade } from "./components/ProposeTrade";
import { DealNegotiation } from "./components/DealNegotiation";
import { MyItems } from "./components/MyItems";
import { MyDeals } from "./components/MyDeals";
import { Profile } from "./components/Profile";
import { Login } from "./components/Login";
import { Signup } from "./components/Signup";
import { isLoggedIn } from "./auth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!isLoggedIn()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/signup",
    Component: Signup,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <Layout />
      </RequireAuth>
    ),
    children: [
      { index: true, Component: Feed },
      { path: "item/:id", Component: ItemDetails },
      { path: "list", Component: ListItem },
      { path: "propose/:id", Component: ProposeTrade },
      { path: "deal/:id", Component: DealNegotiation },
      { path: "my-items", Component: MyItems },
      { path: "my-deals", Component: MyDeals },
      { path: "profile", Component: Profile },
    ],
  },
]);
