import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

function MandatesPage() {
  const mandatesQuery = useQuery({
    queryKey: ["mandates"],
    queryFn: api.getMandates
  });
  const mandates = mandatesQuery.data?.mandates || [];
  const [selectedId, setSelectedId] = useState(null);
  const selected = mandates.find((m) => m.mandate_id === selectedId) || mandates[0];

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <section className="card md:col-span-1">
        <h2 className="mb-3 text-sm font-semibold">Mandates</h2>
        <ul className="space-y-2">
          {mandates.map((m) => (
            <li key={m.mandate_id}>
              <button
                type="button"
                onClick={() => setSelectedId(m.mandate_id)}
                className="w-full rounded-md border border-slate-700 px-3 py-2 text-left text-sm hover:bg-slate-800"
              >
                <div className="font-medium">{m.mandate_id}</div>
                <div className="text-xs text-slate-400">{m.dao_id}</div>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="card md:col-span-2">
        <h2 className="mb-3 text-sm font-semibold">Mandate Detail</h2>
        {!selected ? (
          <p className="text-sm text-slate-400">No mandates found.</p>
        ) : (
          <div className="space-y-2 text-sm">
            <p><span className="text-slate-400">Mandate ID:</span> {selected.mandate_id}</p>
            <p><span className="text-slate-400">DAO:</span> {selected.dao_name || selected.dao_id}</p>
            <p><span className="text-slate-400">Version:</span> {selected.mandate_version}</p>
            <p><span className="text-slate-400">Valid Until:</span> {selected.valid_until || "—"}</p>
            <p><span className="text-slate-400">Status:</span> {selected.is_expired ? "Expired" : "Valid"}</p>
            <pre className="mt-3 max-h-80 overflow-auto rounded-md border border-slate-800 bg-slate-900 p-3 text-xs">
              {JSON.stringify(selected.policy || {}, null, 2)}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}

export default MandatesPage;
