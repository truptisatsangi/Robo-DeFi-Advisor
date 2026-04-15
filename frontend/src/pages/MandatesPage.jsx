import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

const PROTOCOLS = ["aave", "compound", "curve", "uniswap", "balancer", "pendle", "yearn", "lido"];
const CHAINS = ["ethereum", "arbitrum", "polygon", "optimism", "base", "avalanche"];
const RISK_LEVELS = ["very_low", "low", "medium", "high", "very_high"];
const PREFERENCES = ["safest", "balanced", "highest_yield"];

function defaultValidUntil() {
  const d = new Date();
  d.setMonth(d.getMonth() + 1);
  return d.toISOString().slice(0, 10);
}

const DEFAULTS = {
  mandate_id: "",
  dao_id: "",
  dao_name: "",
  approval_ref: "",
  valid_until: defaultValidUntil(),
  amount_usd: 100000,
  min_apy: 1,
  max_apy: "",
  risk_max_level: "medium",
  risk_min_score: 30,
  allowed_protocols: ["aave", "compound", "curve", "uniswap", "balancer"],
  allowed_chains: ["ethereum", "arbitrum", "polygon", "optimism", "base"],
  min_pool_tvl_usd: 1000000,
  max_tvl_per_pool_pct: 40,
  preference: "balanced",
};

function Field({ label, hint, children }) {
  return (
    <div className="space-y-1">
      <label className="block text-xs font-medium text-slate-300">{label}</label>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      {children}
    </div>
  );
}

function Input({ className = "", ...props }) {
  return (
    <input
      className={`w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm placeholder-slate-500 focus:border-indigo-500 focus:outline-none ${className}`}
      {...props}
    />
  );
}

function Select({ children, ...props }) {
  return (
    <select
      className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none"
      {...props}
    >
      {children}
    </select>
  );
}

function CheckGroup({ options, selected, onChange }) {
  const toggle = (val) =>
    onChange(selected.includes(val) ? selected.filter((v) => v !== val) : [...selected, val]);
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
            selected.includes(opt)
              ? "border-indigo-500 bg-indigo-900/60 text-indigo-200"
              : "border-slate-700 bg-slate-800 text-slate-400 hover:border-slate-500"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function CreateMandateForm({ onSuccess }) {
  const [form, setForm] = useState(DEFAULTS);
  const [error, setError] = useState(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: api.createMandate,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["mandates"] });
      setError(null);
      onSuccess(data.mandate);
    },
    onError: (err) => setError(err.message),
  });

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.mandate_id.trim()) return setError("Mandate ID is required.");
    if (!form.dao_id.trim()) return setError("DAO ID is required.");
    mutation.mutate({
      ...form,
      amount_usd: Number(form.amount_usd),
      min_apy: Number(form.min_apy),
      max_apy: form.max_apy !== "" ? Number(form.max_apy) : null,
      risk_min_score: Number(form.risk_min_score),
      min_pool_tvl_usd: Number(form.min_pool_tvl_usd),
      max_tvl_per_pool_pct: Number(form.max_tvl_per_pool_pct),
      allowed_protocols: form.allowed_protocols.join(","),
      allowed_chains: form.allowed_chains.join(","),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Identity */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Mandate ID *" hint="Unique ID used to run recommendations">
          <Input
            placeholder="e.g. mandate-q2-2026"
            value={form.mandate_id}
            onChange={(e) => set("mandate_id", e.target.value)}
          />
        </Field>
        <Field label="DAO ID *" hint="Short identifier for your DAO">
          <Input
            placeholder="e.g. my-dao"
            value={form.dao_id}
            onChange={(e) => set("dao_id", e.target.value)}
          />
        </Field>
        <Field label="DAO Name" hint="Human-readable name (optional)">
          <Input
            placeholder="e.g. My DAO"
            value={form.dao_name}
            onChange={(e) => set("dao_name", e.target.value)}
          />
        </Field>
        <Field label="Approval Reference" hint="Snapshot/Tally vote ID (optional)">
          <Input
            placeholder="e.g. Snapshot #42"
            value={form.approval_ref}
            onChange={(e) => set("approval_ref", e.target.value)}
          />
        </Field>
      </div>

      {/* Capital & validity */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Amount USD" hint="Capital to allocate">
          <Input
            type="number" min="0"
            value={form.amount_usd}
            onChange={(e) => set("amount_usd", e.target.value)}
          />
        </Field>
        <Field label="Valid Until" hint="Default: 1 month from today">
          <Input
            type="date"
            value={form.valid_until}
            onChange={(e) => set("valid_until", e.target.value)}
          />
        </Field>
        <Field label="Preference" hint="Risk/yield trade-off">
          <Select value={form.preference} onChange={(e) => set("preference", e.target.value)}>
            {PREFERENCES.map((p) => <option key={p} value={p}>{p}</option>)}
          </Select>
        </Field>
      </div>

      {/* APY */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Min APY (%)" hint="Pools below this are excluded">
          <Input
            type="number" min="0" step="0.1"
            value={form.min_apy}
            onChange={(e) => set("min_apy", e.target.value)}
          />
        </Field>
        <Field label="Max APY (%) — optional" hint="Leave blank for no ceiling">
          <Input
            type="number" min="0" step="0.1"
            placeholder="No ceiling"
            value={form.max_apy}
            onChange={(e) => set("max_apy", e.target.value)}
          />
        </Field>
      </div>

      {/* Risk */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Max Risk Level" hint="Pools riskier than this are excluded">
          <Select value={form.risk_max_level} onChange={(e) => set("risk_max_level", e.target.value)}>
            {RISK_LEVELS.map((r) => <option key={r} value={r}>{r}</option>)}
          </Select>
        </Field>
        <Field label="Min Risk Score (0–100)" hint="Higher = safer. Pools below this are excluded">
          <Input
            type="number" min="0" max="100"
            value={form.risk_min_score}
            onChange={(e) => set("risk_min_score", e.target.value)}
          />
        </Field>
      </div>

      {/* Protocols */}
      <Field label="Allowed Protocols" hint="Only pools from selected protocols will be considered">
        <CheckGroup
          options={PROTOCOLS}
          selected={form.allowed_protocols}
          onChange={(v) => set("allowed_protocols", v)}
        />
      </Field>

      {/* Chains */}
      <Field label="Allowed Chains" hint="Only pools on selected chains will be considered">
        <CheckGroup
          options={CHAINS}
          selected={form.allowed_chains}
          onChange={(v) => set("allowed_chains", v)}
        />
      </Field>

      {/* TVL */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Min Pool TVL (USD)" hint="Pools below this TVL are excluded">
          <Input
            type="number" min="0"
            value={form.min_pool_tvl_usd}
            onChange={(e) => set("min_pool_tvl_usd", e.target.value)}
          />
        </Field>
        <Field label="Max % per Pool" hint="Capital concentration cap per pool (default 40%)">
          <Input
            type="number" min="1" max="100"
            value={form.max_tvl_per_pool_pct}
            onChange={(e) => set("max_tvl_per_pool_pct", e.target.value)}
          />
        </Field>
      </div>

      {error && <p className="rounded-md border border-red-700 bg-red-950/30 px-3 py-2 text-xs text-red-300">{error}</p>}

      <button
        type="submit"
        disabled={mutation.isPending}
        className="rounded-md bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
      >
        {mutation.isPending ? "Creating…" : "Create Mandate"}
      </button>
    </form>
  );
}

function MandatesPage() {
  const mandatesQuery = useQuery({ queryKey: ["mandates"], queryFn: api.getMandates });
  const mandates = mandatesQuery.data?.mandates || [];
  const [selectedId, setSelectedId] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const selected = mandates.find((m) => m.mandate_id === selectedId) || mandates[0];

  const handleCreated = (mandate) => {
    setSelectedId(mandate.mandate_id);
    setShowForm(false);
  };

  return (
    <div className="space-y-4">
      {/* Create form */}
      <section className="card">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">
            {showForm ? "New Mandate" : "Mandates"}
          </h2>
          <button
            type="button"
            onClick={() => setShowForm((v) => !v)}
            className="rounded-md border border-slate-700 px-3 py-1 text-xs hover:bg-slate-800"
          >
            {showForm ? "Cancel" : "+ New Mandate"}
          </button>
        </div>

        {showForm && (
          <div className="mt-4 border-t border-slate-800 pt-4">
            <p className="mb-4 text-xs text-slate-400">
              Fill in the fields below to create a new mandate. Only <span className="text-white font-medium">Mandate ID</span> and <span className="text-white font-medium">DAO ID</span> are required — everything else has sensible defaults.
            </p>
            <CreateMandateForm onSuccess={handleCreated} />
          </div>
        )}
      </section>

      {/* List + detail */}
      <div className="grid gap-4 md:grid-cols-3">
        <section className="card md:col-span-1">
          <h2 className="mb-3 text-sm font-semibold">Existing Mandates</h2>
          {mandatesQuery.isLoading && <p className="text-xs text-slate-400">Loading…</p>}
          {mandates.length === 0 && !mandatesQuery.isLoading && (
            <p className="text-xs text-slate-400">No mandates yet. Create one above.</p>
          )}
          <ul className="space-y-2">
            {mandates.map((m) => (
              <li key={m.mandate_id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(m.mandate_id)}
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors hover:bg-slate-800 ${
                    selected?.mandate_id === m.mandate_id
                      ? "border-indigo-500 bg-indigo-950/40"
                      : "border-slate-700"
                  }`}
                >
                  <div className="font-medium">{m.mandate_id}</div>
                  <div className="text-xs text-slate-400">{m.dao_id}</div>
                  <div className={`mt-1 text-xs font-medium ${m.is_expired ? "text-red-400" : "text-green-400"}`}>
                    {m.is_expired ? "Expired" : `Valid until ${m.valid_until}`}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="card md:col-span-2">
          <h2 className="mb-3 text-sm font-semibold">Mandate Detail</h2>
          {!selected ? (
            <p className="text-sm text-slate-400">Select a mandate or create a new one.</p>
          ) : (
            <div className="space-y-2 text-sm">
              <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                <p><span className="text-slate-400">Mandate ID: </span>{selected.mandate_id}</p>
                <p><span className="text-slate-400">DAO: </span>{selected.dao_name || selected.dao_id}</p>
                <p><span className="text-slate-400">Version: </span>{selected.mandate_version}</p>
                <p><span className="text-slate-400">Valid Until: </span>{selected.valid_until || "—"}</p>
                <p><span className="text-slate-400">Approval Ref: </span>{selected.approval_ref || "—"}</p>
                <p>
                  <span className="text-slate-400">Status: </span>
                  <span className={selected.is_expired ? "text-red-400" : "text-green-400"}>
                    {selected.is_expired ? "Expired" : "Valid"}
                  </span>
                </p>
              </div>
              <p className="pt-1 text-xs text-slate-400">Policy</p>
              <pre className="max-h-80 overflow-auto rounded-md border border-slate-800 bg-slate-900 p-3 text-xs">
                {JSON.stringify(selected.policy || {}, null, 2)}
              </pre>
              <p className="text-xs text-slate-500">
                Copy the <span className="text-white">Mandate ID</span> above and paste it into the Dashboard run form to use this mandate.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default MandatesPage;
