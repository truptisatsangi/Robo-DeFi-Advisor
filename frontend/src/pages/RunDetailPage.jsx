import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import ProposalPanel from "../components/ProposalPanel";
import RecommendationTable from "../components/RecommendationTable";
import StageTimeline from "../components/StageTimeline";
import { api } from "../lib/api";

function RunDetailPage() {
  const { runId } = useParams();
  const isLatest = runId === "latest";
  const runQuery = useQuery({
    queryKey: ["run", runId],
    queryFn: () => (isLatest ? api.getLatestRun() : api.getRunById(runId)),
    retry: false
  });

  const entry = runQuery.data?.recommendation_output || runQuery.data || {};
  const recommendation = entry.recommendation || {};
  const allocation = recommendation.allocation || [];
  const pipelineStats = entry.pipeline_stats;

  return (
    <div className="space-y-4">
      <section className="card">
        <h2 className="text-sm font-semibold">Run Detail</h2>
        <div className="mt-2 grid gap-2 text-sm md:grid-cols-3">
          <p><span className="text-slate-400">Run ID:</span> {runQuery.data?.run_id || entry.run_id || "—"}</p>
          <p><span className="text-slate-400">Mandate:</span> {runQuery.data?.mandate_id || entry.mandate_id || "—"}</p>
          <p><span className="text-slate-400">Timestamp:</span> {runQuery.data?.timestamp || "—"}</p>
        </div>
      </section>
      <StageTimeline stats={pipelineStats} />
      <RecommendationTable allocation={allocation} />
      <ProposalPanel draft={entry.proposal_draft || runQuery.data?.proposal_draft} />
      <section className="card">
        <h3 className="mb-3 text-sm font-semibold">Raw Payload</h3>
        <pre className="max-h-96 overflow-auto text-xs text-slate-300">{JSON.stringify(runQuery.data || {}, null, 2)}</pre>
      </section>
    </div>
  );
}

export default RunDetailPage;
