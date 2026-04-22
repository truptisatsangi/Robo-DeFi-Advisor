import { useMutation, useQuery } from "@tanstack/react-query";
import FormulaPanel from "../components/FormulaPanel";
import ProposalPanel from "../components/ProposalPanel";
import RecommendationTable from "../components/RecommendationTable";
import RunForm from "../components/RunForm";
import StageTimeline from "../components/StageTimeline";
import StatCard from "../components/StatCard";
import TrustStrip from "../components/TrustStrip";
import { api } from "../lib/api";

function DashboardPage() {
  const latestRunQuery = useQuery({
    queryKey: ["defaultRun"],
    queryFn: api.getDefaultRun,
  });

  const runMutation = useMutation({
    mutationFn: api.runRecommendation
  });

  // prefer the fresh mutation result; fall back to last persisted run
  const mutationResult = runMutation.data;
  const activeResult = mutationResult || latestRunQuery.data;
  const recommendation = activeResult?.recommendation || {};
  const allocation = recommendation?.allocation || [];
  const pipelineStats = activeResult?.pipeline_stats;

  // network-level error (fetch failed entirely)
  const networkError = runMutation.error?.message;
  // API-level error: request succeeded but pipeline returned success:false
  const apiError = mutationResult?.success === false ? mutationResult.error : null;
  const loadError = latestRunQuery.error?.message;

  return (
    <div className="space-y-4">
      <TrustStrip />
      <RunForm onRun={runMutation.mutate} isLoading={runMutation.isPending} />
      {networkError ? (
        <section className="card border-red-700 bg-red-950/30 text-sm text-red-200">
          Run request failed: {networkError}
        </section>
      ) : null}
      {apiError ? (
        <section className="card border-red-700 bg-red-950/30 text-sm text-red-200">
          <span className="font-semibold">Pipeline error:</span> {apiError}
        </section>
      ) : null}
      {!runMutation.data && loadError ? (
        <section className="card border-amber-700 bg-amber-950/30 text-sm text-amber-200">
          Could not load latest run: {loadError}
        </section>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="Active Mandate" value={activeResult?.mandate_id || "—"} subtitle="Current run context" />
        <StatCard title="Latest Recommendation" value={recommendation?.recommended_pools?.length || 0} subtitle="Pools in recommendation set" />
        <StatCard
          title="Portfolio APY + Allocation"
          value={`${recommendation?.expected_portfolio_apy || 0}%`}
          subtitle={`$${Number(recommendation?.total_allocated_usd || 0).toLocaleString()} allocated`}
        />
        <StatCard title="Audit Status" value={activeResult?.run_id || "No run"} subtitle="Run ID persisted to audit log" />
      </section>

      <StageTimeline stats={pipelineStats} />
      <RecommendationTable allocation={allocation} />
      <FormulaPanel />
      <ProposalPanel draft={activeResult?.proposal_draft} />
    </div>
  );
}

export default DashboardPage;
