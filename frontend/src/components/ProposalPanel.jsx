function ProposalPanel({ draft }) {
  async function copyDraft() {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
  }

  return (
    <section className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">Proposal Draft</h3>
        <button
          type="button"
          onClick={copyDraft}
          className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-800"
        >
          Copy Proposal Draft
        </button>
      </div>
      <pre className="max-h-80 overflow-auto whitespace-pre-wrap text-xs text-slate-300">{draft || "No proposal draft yet."}</pre>
    </section>
  );
}

export default ProposalPanel;
