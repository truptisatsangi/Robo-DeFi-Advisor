function SettingsPage() {
  return (
    <div className="space-y-4">
      <section className="card">
        <h2 className="mb-3 text-sm font-semibold">Display Settings</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="text-sm">
            <span className="mb-1 block text-slate-300">Timezone</span>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2">
              <option>Local timezone</option>
              <option>UTC</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-300">Number format</span>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2">
              <option>1,234,567.89</option>
              <option>12,34,567.89</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-slate-300">Table density</span>
            <select className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2">
              <option>Comfortable</option>
              <option>Compact</option>
            </select>
          </label>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          MVP settings are presentation-only. No execution controls or secret management are exposed.
        </p>
      </section>
    </div>
  );
}

export default SettingsPage;
