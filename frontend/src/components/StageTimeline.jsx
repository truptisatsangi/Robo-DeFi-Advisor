function StageTimeline({ stats }) {
  const discovery = stats?.discovery || {};
  const risk = stats?.risk || {};
  const decision = stats?.decision || {};

  const rows = [
    {
      stage: "Discovery",
      in: discovery.total_fetched ?? 0,
      out: discovery.after_apy_crosscheck ?? 0,
      detail: `Policy filters: ${discovery.after_policy_filters ?? 0}, ranked: ${discovery.after_rank_top_n ?? 0}`
    },
    {
      stage: "Risk",
      in: risk.input_candidates ?? 0,
      out: risk.after_risk_policy_filters ?? 0,
      detail: "Applied min_score/max_level policy gates"
    },
    {
      stage: "Decision",
      in: decision.scored_candidates ?? 0,
      out: decision.recommended_count ?? 0,
      detail: "Deterministic weighted ranking (0.5 / 0.3 / 0.2)"
    }
  ];

  return (
    <section className="card">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Filter Timeline</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2">Stage</th>
              <th className="pb-2">Input</th>
              <th className="pb-2">Output</th>
              <th className="pb-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.stage} className="border-t border-slate-800">
                <td className="py-2 font-medium">{row.stage}</td>
                <td className="py-2">{row.in}</td>
                <td className="py-2">{row.out}</td>
                <td className="py-2 text-slate-400">{row.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default StageTimeline;
