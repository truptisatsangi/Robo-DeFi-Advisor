function RecommendationTable({ allocation = [] }) {
  return (
    <section className="card">
      <h3 className="mb-3 text-sm font-semibold text-slate-200">Recommended Pools</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-slate-400">
            <tr>
              <th className="pb-2">Protocol</th>
              <th className="pb-2">Chain</th>
              <th className="pb-2">APY</th>
              <th className="pb-2">Risk</th>
              <th className="pb-2">TVL</th>
              <th className="pb-2">Allocation %</th>
              <th className="pb-2">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {allocation.length === 0 ? (
              <tr>
                <td colSpan={7} className="border-t border-slate-800 py-3 text-slate-400">
                  No recommendations available.
                </td>
              </tr>
            ) : (
              allocation.map((row) => (
                <tr key={row.pool_id} className="border-t border-slate-800 align-top">
                  <td className="py-2">{row.protocol}</td>
                  <td className="py-2">{row.chain}</td>
                  <td className="py-2">{row.apy}%</td>
                  <td className="py-2">
                    {row.risk_score}/100
                    <div className="text-xs text-slate-500">{row.risk_level}</div>
                  </td>
                  <td className="py-2">${Number(row.tvl || 0).toLocaleString()}</td>
                  <td className="py-2">{row.pct}%</td>
                  <td className="py-2 text-slate-400">
                    {Array.isArray(row.explanation) ? row.explanation.join(". ") : row.explanation}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default RecommendationTable;
