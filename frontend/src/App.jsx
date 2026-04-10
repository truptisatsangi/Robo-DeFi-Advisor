import { NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import MandatesPage from "./pages/MandatesPage";
import RunDetailPage from "./pages/RunDetailPage";
import SettingsPage from "./pages/SettingsPage";

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/90 px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">RDA Treasury Dashboard</h1>
            <p className="text-sm text-slate-400">Clarity. Control. Auditability.</p>
          </div>
          <nav className="flex gap-2 text-sm">
            {[
              ["/dashboard", "Dashboard"],
              ["/mandates", "Mandates"],
              ["/runs/latest", "Run Detail"],
              ["/settings", "Settings"]
            ].map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 ${isActive ? "bg-slate-700 text-white" : "text-slate-300 hover:bg-slate-800"}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/mandates" element={<MandatesPage />} />
          <Route path="/runs/:runId" element={<RunDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
