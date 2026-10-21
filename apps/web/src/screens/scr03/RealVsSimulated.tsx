import { Card, CardBody, CardHeader } from "@/components/ui";
import { REAL, SIMULATED } from "./copy";

function Column({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="t-card-title">{title}</h3>
      <ul className="mt-1 list-disc pl-5 text-body">
        {items.map((i) => <li key={i}>{i}</li>)}
      </ul>
    </div>
  );
}

export function RealVsSimulated() {
  return (
    <Card>
      <CardHeader as="h2" title="What is real and what is simulated" />
      <CardBody className="grid gap-4 min-[700px]:grid-cols-2">
        <Column title="Real" items={REAL} />
        <Column title="Simulated" items={SIMULATED} />
      </CardBody>
    </Card>
  );
}
