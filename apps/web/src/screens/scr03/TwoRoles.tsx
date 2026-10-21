import { Card, CardBody, CardHeader } from "@/components/ui";
import { STEPS } from "./copy";

export function TwoRoles() {
  return (
    <Card>
      <CardHeader as="h2" title="How to play both roles" />
      <CardBody>
        <ol className="list-decimal pl-5 text-body">
          {STEPS.map((s) => <li key={s} className="py-0.5">{s}</li>)}
        </ol>
      </CardBody>
    </Card>
  );
}
