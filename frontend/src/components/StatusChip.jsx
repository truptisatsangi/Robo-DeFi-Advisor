function StatusChip({ label }) {
  return (
    <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs text-slate-200">
      {label}
    </span>
  );
}

export default StatusChip;
