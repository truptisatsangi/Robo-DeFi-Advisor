import { useNavigate } from "react-router-dom";

const STEPS = [
  {
    number: "01",
    title: "Create a Mandate",
    description:
      "A mandate is your DAO's investment policy — it defines which protocols are allowed, your risk tolerance, APY targets, and how much capital to deploy. Think of it as the rules the advisor must follow.",
    action: "Go to Mandates →",
    href: "/mandates",
    highlight: false,
  },
  {
    number: "02",
    title: "Run a Recommendation",
    description:
      "Paste your mandate ID into the Dashboard and click Run. The system scans ~19,000 DeFi pools, filters by your policy, scores each pool for risk, and ranks the best options in seconds.",
    action: "Go to Dashboard →",
    href: "/dashboard",
    highlight: true,
  },
  {
    number: "03",
    title: "Review & Propose",
    description:
      "You get a ranked allocation across multiple pools with a Snapshot-ready governance proposal. No funds move automatically — a governance vote is always required before execution.",
    action: null,
    href: null,
    highlight: false,
  },
];

const GUARANTEES = [
  {
    icon: "⚖️",
    title: "Deterministic scoring",
    body: "Same mandate + same data = same ranking, every time. No hidden model variance.",
  },
  {
    icon: "🔒",
    title: "No autonomous execution",
    body: "The advisor only generates proposals. Funds never move without a governance vote.",
  },
  {
    icon: "📋",
    title: "Mandate-gated",
    body: "Every run is tied to a DAO-approved mandate. Expired or missing mandates are blocked.",
  },
  {
    icon: "🗂️",
    title: "Full audit trail",
    body: "Every recommendation is logged with run ID, mandate snapshot, and timestamp.",
  },
];

function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="space-y-16 py-8">

      {/* Hero */}
      <section className="text-center space-y-6 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1 text-xs text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          Proposal-only MVP · No autonomous fund movement
        </div>

        <h2 className="text-4xl font-bold tracking-tight text-white leading-tight">
          Your DAO treasury,{" "}
          <span className="text-emerald-400">deployed with confidence</span>
        </h2>

        <p className="text-slate-400 text-lg leading-relaxed">
          Most DAO treasuries hold millions in idle stablecoins — earning nothing while
          governance debates where to deploy them. RDA converts your DAO-approved policy
          into deterministic DeFi yield recommendations and Snapshot-ready proposals
          in seconds.
        </p>

        <div className="flex flex-wrap justify-center gap-3 pt-2">
          <button
            onClick={() => navigate("/dashboard")}
            className="rounded-md bg-emerald-600 hover:bg-emerald-500 px-5 py-2.5 text-sm font-medium text-white transition-colors"
          >
            Try the Dashboard
          </button>
          <button
            onClick={() => navigate("/mandates")}
            className="rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-5 py-2.5 text-sm font-medium text-slate-200 transition-colors"
          >
            Create a Mandate
          </button>
        </div>
      </section>

      {/* How it works */}
      <section className="space-y-6">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-500 text-center">
          How it works
        </h3>

        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className={`rounded-lg border p-6 space-y-3 transition-colors ${
                step.highlight
                  ? "border-emerald-700 bg-emerald-950/30"
                  : "border-slate-800 bg-slate-900/60"
              }`}
            >
              <span className="text-2xl font-bold text-slate-600">{step.number}</span>
              <h4 className="font-semibold text-white">{step.title}</h4>
              <p className="text-sm text-slate-400 leading-relaxed">{step.description}</p>
              {step.action && (
                <button
                  onClick={() => navigate(step.href)}
                  className="text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  {step.action}
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* What is a mandate callout */}
      <section className="rounded-lg border border-slate-700 bg-slate-900/80 p-6 md:p-8 space-y-4 max-w-3xl mx-auto">
        <div className="flex items-start gap-4">
          <span className="text-2xl">📋</span>
          <div className="space-y-2">
            <h4 className="font-semibold text-white text-lg">What is a mandate?</h4>
            <p className="text-slate-400 text-sm leading-relaxed">
              A <span className="text-slate-200 font-medium">mandate</span> is a JSON
              policy file that represents your DAO's approved investment rules. It defines:
            </p>
            <ul className="text-sm text-slate-400 space-y-1 list-none">
              {[
                ["🏦", "Which protocols are allowed", "(e.g. Aave, Compound, Curve)"],
                ["⛓️", "Which chains to consider", "(e.g. Ethereum, Arbitrum)"],
                ["📈", "APY range", "(minimum and maximum acceptable yield)"],
                ["⚠️", "Risk tolerance", "(max risk level and minimum risk score)"],
                ["💰", "Capital to deploy", "(total USD amount)"],
                ["📅", "Validity period", "(mandates expire and require renewal)"],
              ].map(([icon, label, note]) => (
                <li key={label} className="flex items-baseline gap-2">
                  <span>{icon}</span>
                  <span>
                    <span className="text-slate-300">{label}</span>{" "}
                    <span className="text-slate-500">{note}</span>
                  </span>
                </li>
              ))}
            </ul>
            <p className="text-slate-500 text-sm pt-1">
              The advisor enforces every rule in the mandate before returning a single recommendation.
            </p>
            <button
              onClick={() => navigate("/mandates")}
              className="mt-2 inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs text-slate-200 transition-colors"
            >
              Create your first mandate →
            </button>
          </div>
        </div>
      </section>

      {/* Guarantees */}
      <section className="space-y-6">
        <h3 className="text-sm font-semibold uppercase tracking-widest text-slate-500 text-center">
          Built for governance-first DAOs
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {GUARANTEES.map((g) => (
            <div
              key={g.title}
              className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 space-y-2"
            >
              <span className="text-xl">{g.icon}</span>
              <p className="text-sm font-medium text-slate-200">{g.title}</p>
              <p className="text-xs text-slate-500 leading-relaxed">{g.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick start CTA */}
      <section className="text-center space-y-4 pb-4">
        <p className="text-slate-500 text-sm">Ready to see it in action?</p>
        <button
          onClick={() => navigate("/dashboard")}
          className="rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 px-6 py-2.5 text-sm font-medium text-slate-200 transition-colors"
        >
          View sample recommendation on Dashboard →
        </button>
      </section>

    </div>
  );
}

export default HomePage;
