import { lazy, Suspense, useEffect, useMemo, type ComponentType } from "react";
import { createBrowserRouter, Link, Navigate, Outlet, useLocation, type RouteObject } from "react-router";
import { SCREENS } from "@/routes";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import { Skeleton } from "@/components/ui/Skeleton";
import { AppFrame } from "@/components/shell/AppFrame";
import { Main } from "@/components/shell/chrome";
import { DemoStatusProvider } from "@/state/demoStatus";
import { SessionProvider, useSession } from "@/state/session";
import { applyTheme } from "@/state/theme";

// Each screen is a lazy module so the groups' folders stay independent.
const LOADERS: Record<string, () => Promise<{ default: ComponentType }>> = {
  scr01: () => import("@/screens/scr01"),
  scr02: () => import("@/screens/scr02"),
  scr03: () => import("@/screens/scr03"),
  scr04: () => import("@/screens/scr04"),
  scr05: () => import("@/screens/scr05"),
  scr06: () => import("@/screens/scr06"),
  scr07: () => import("@/screens/scr07"),
  scr08: () => import("@/screens/scr08"),
  scr09: () => import("@/screens/scr09"),
  scr10: () => import("@/screens/scr10"),
  scr11: () => import("@/screens/scr11"),
  scr12: () => import("@/screens/scr12"),
};

function FrameSkeleton() {
  return (
    <AppFrame variant="page">
      <Main className="p-4"><Skeleton height={24} width={240} rows={1} /><div className="mt-3"><Skeleton height={64} rows={3} /></div></Main>
    </AppFrame>
  );
}

export function RequireSession() {
  const { status, lostReason } = useSession();
  const loc = useLocation();
  if (status === "loading") return <FrameSkeleton />;
  if (status === "signed-out") {
    const qs = new URLSearchParams({ return_to: loc.pathname + loc.search, reason: lostReason ?? "none" });
    return <Navigate to={`/login?${qs.toString()}`} replace />;
  }
  return <Outlet />;
}

function RootLayout() {
  useEffect(() => { applyTheme(); }, []);
  return (
    <AnnounceProvider>
      <SessionProvider>
        <DemoStatusProvider>
          <Outlet />
        </DemoStatusProvider>
      </SessionProvider>
    </AnnounceProvider>
  );
}

function NotFound() {
  return (
    <AppFrame variant="auth">
      <Main className="p-4">
        <h1 className="t-title">Page not found</h1>
        <p className="mt-2"><Link to="/" className="text-accent underline">Back to the start</Link></p>
      </Main>
    </AppFrame>
  );
}

function screenElement(slug: string) {
  const Lazy = lazy(LOADERS[slug]);
  return <Suspense fallback={<FrameSkeleton />}><Lazy /></Suspense>;
}

export function buildRoutes(extra: RouteObject[] = []): RouteObject[] {
  const publicScreens = SCREENS.filter((s) => s.public);
  const guarded = SCREENS.filter((s) => !s.public);
  return [
    {
      element: <RootLayout />,
      children: [
        ...publicScreens.map((s) => ({ path: s.path, element: screenElement(s.slug) })),
        ...extra,
        {
          element: <RequireSession />,
          children: [
            ...guarded.map((s) => ({ path: s.path, element: screenElement(s.slug) })),
            // FR-2: SCR-6 with no case picked ("Pick a case from the queue.")
            { path: "/staff/cases", element: screenElement("scr06") },
          ],
        },
        { path: "*", element: <NotFound /> },
      ],
    },
  ];
}

/** A function, not a module-level router: the dev layer registers /__kit before the first render. */
export function createAppRouter() {
  const devRoutes = (globalThis as { __mhcDevRoutes?: RouteObject[] }).__mhcDevRoutes ?? [];
  return createBrowserRouter(buildRoutes(devRoutes));
}

export function useAppRouter() {
  return useMemo(() => createAppRouter(), []);
}
