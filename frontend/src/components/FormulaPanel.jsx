function FormulaPanel() {
  return (
    <details className="card">
      <summary className="cursor-pointer text-sm font-semibold text-slate-200">
        Deterministic scoring formula (click to expand)
      </summary>
      <div className="mt-3 space-y-2 text-sm text-slate-300">
        <p>
          score = 0.5 * normalized_apy + 0.3 * normalized_risk_score + 0.2 * normalized_tvl
        </p>
        <p className="text-slate-400">
          Each metric is normalized to [0,1] over the candidate set. Same policy + same market data
          yields the same ranking.
        </p>
      </div>
    </details>
  );
}

export default FormulaPanel;
