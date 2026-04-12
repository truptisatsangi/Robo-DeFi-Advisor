import { useState } from "react";

const INITIAL_FORM = {
  mandate_id: "",
  dao_id: "",
  amount_usd: "",
  top_n: "",
  min_apy: "",
  max_apy: ""
};

function RunForm({ onRun, isLoading }) {
  const [form, setForm] = useState(INITIAL_FORM);

  function onChange(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function onSubmit(event) {
    event.preventDefault();
    if (!form.mandate_id.trim()) {
      return;
    }
    const payload = {
      mandate_id: form.mandate_id.trim(),
      dao_id: form.dao_id.trim() || undefined,
      amount_usd: form.amount_usd ? Number(form.amount_usd) : undefined
    };
    onRun(payload);
  }

  return (
    <form className="card grid gap-3 md:grid-cols-3" onSubmit={onSubmit}>
      <label className="text-sm">
        <span className="mb-1 block text-slate-300">Mandate ID (required)</span>
        <input
          name="mandate_id"
          value={form.mandate_id}
          onChange={onChange}
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
          placeholder="test-mandate-001"
          required
        />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-slate-300">DAO ID (optional)</span>
        <input
          name="dao_id"
          value={form.dao_id}
          onChange={onChange}
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
          placeholder="test-dao"
        />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-slate-300">Amount USD (optional)</span>
        <input
          name="amount_usd"
          value={form.amount_usd}
          onChange={onChange}
          type="number"
          min="0"
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
          placeholder="100000"
        />
      </label>
      <div className="md:col-span-3 flex items-center justify-between pt-1">
        <p className="text-xs text-slate-400">
          Optional policy overrides can be added to API request in next iteration.
        </p>
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-md bg-slate-200 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-60"
        >
          {isLoading ? "Running..." : "Run Recommendation"}
        </button>
      </div>
    </form>
  );
}

export default RunForm;
