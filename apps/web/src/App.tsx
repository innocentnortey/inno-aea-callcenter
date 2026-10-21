import { RouterProvider } from "react-router/dom";
import { useAppRouter } from "./router";

export default function App() {
  const router = useAppRouter();
  return <RouterProvider router={router} />;
}
