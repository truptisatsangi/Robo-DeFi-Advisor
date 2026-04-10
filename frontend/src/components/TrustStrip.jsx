import StatusChip from "./StatusChip";

const TRUST_LABELS = [
  "Deterministic Scoring",
  "No Autonomous Fund Movement",
  "Mandate-Gated Runs",
  "Audit Logged"
];

function TrustStrip() {
  return (
    <section className="card flex flex-wrap gap-2">
      {TRUST_LABELS.map((label) => (
        <StatusChip key={label} label={label} />
      ))}
    </section>
  );
}

export default TrustStrip;
