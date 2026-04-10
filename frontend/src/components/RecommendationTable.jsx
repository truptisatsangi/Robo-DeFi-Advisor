const RISK_BADGE = {
  very_low:  "bg-emerald-900/60 text-emerald-300 border border-emerald-700",
  low:       "bg-teal-900/60 text-teal-300 border border-teal-700",
  medium:    "bg-amber-900/60 text-amber-300 border border-amber-700",
  high:      "bg-orange-900/60 text-orange-300 border border-orange-700",
  very_high: "bg-red-900/60 text-red-300 border border-red-700",
};

function riskBadgeClass(level) {
  return RISK_BADGE[(level || "").toLowerCase().replace(" ", "_")] || RISK_BADGE.medium;
}

function poolLink(row) {
  if (row.url) return row.url;
  if (row.pool_id) return `https://defillama.com/yields/pool/${row.pool_id}`;
  return null;
}

function RecommendationTable({ allocation = [] }) {
  return (
    <section className="card">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Recommended Pools</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2 pr-4">Protocol</th>
              <th className="pb-2 pr-4">Chain</th>
              <th className="pb-2 pr-4">APY</th>
              <th className="pb-2 pr-4">Risk</th>
              <th className="pb-2 pr-4">TVL</th>
              <th className="pb-2 pr-4">Allocation</th>
              <th className="pb-2 pr-4">Amount</th>
              <th className="pb-2 pr-4">Verify</th>
            </tr>
          </thead>
          <tbody>
            {allocation.length === 0 ? (
              <tr>
                <td colSpan={8} className="border-t border-slate-800 py-3 text-slate-400">
                  No recommendations available.
                </td>
              </tr>
            ) : (
              allocation.map((row) => {
                const link = poolLink(row);
                const riskLevel = (row.risk_level || "").toLowerCase().replace(" ", "_");
                return (
                  <tr key={row.pool_id} className="border-t border-slate-800 align-middle hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 pr-4 font-medium text-slate-100">
                      {row.protocol}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-300">{row.chain}</td>
                    <td className="py-2.5 pr-4 font-mono text-emerald-400">
                      {Number(row.apy).toFixed(2)}%
                    </td>
                    <td className="py-2.5 pr-4">
                      <div className="flex flex-col gap-1">
                        <span className="font-mono text-slate-200">{row.risk_score}/100</span>
                        {riskLevel && (
                          <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${riskBadgeClass(riskLevel)}`}>
                            {riskLevel.replace("_", " ")}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-slate-300">
                      ${Number(row.tvl || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-2.5 pr-4 font-semibold text-sky-400">
                      {row.pct}%
                    </td>
                    <td className="py-2.5 pr-4 font-mono text-slate-200">
                      ${Number(row.amount_usd || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-2.5 pr-4">
                      {link ? (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 rounded border border-slate-700 px-2 py-0.5 text-xs text-sky-400 hover:border-sky-600 hover:bg-sky-900/20 transition-colors"
                        >
                          View ↗
                        </a>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default RecommendationTable;
