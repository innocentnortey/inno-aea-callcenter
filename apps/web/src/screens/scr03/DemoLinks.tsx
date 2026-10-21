import { Link } from "react-router";
import { Card, CardBody, CardHeader } from "@/components/ui";
import { screenById, type ScreenId } from "@/routes";

// The demo inbox and the staff queue open in a new tab (decision G-5); the rest stay in this tab.
const LINKS: { label: string; id: ScreenId; newTab: boolean }[] = [
  { label: "Chat", id: "SCR-1", newTab: false },
  { label: "Demo inbox", id: "SCR-2", newTab: true },
  { label: "Staff queue", id: "SCR-5", newTab: true },
  { label: "Monitoring", id: "SCR-10", newTab: false },
  { label: "Evaluation", id: "SCR-11", newTab: false },
];

export function DemoLinks() {
  return (
    <Card>
      <CardHeader as="h2" title="Links" />
      <CardBody>
        <ul className="flex flex-col gap-1">
          {LINKS.map((l) => {
            const path = screenById(l.id).path;
            return (
              <li key={l.id} className="min-h-11 content-center">
                {l.newTab ? (
                  <a href={path} target="_blank" rel="noopener" className="link-text">{l.label}</a>
                ) : (
                  <Link to={path} className="link-text">{l.label}</Link>
                )}
              </li>
            );
          })}
        </ul>
      </CardBody>
    </Card>
  );
}
