"use client";

/** Dashboard: LLM cost/token/latency metrics + corpus counts. */

import { useCallback, useEffect, useState } from "react";
import { api, type DocumentOut, type Metrics } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold tabular-nums">{value}</div>
        {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    Promise.all([api.metrics(), api.listDocuments()])
      .then(([m, d]) => {
        setMetrics(m);
        setDocs(d);
        setErr(null);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Failed to load"));
  }, []);

  useEffect(() => load(), [load]);

  const processed = docs.filter((d) => d.status === "processed").length;
  const chunks = docs.reduce((n, d) => n + (d.chunk_count ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            LLM usage since the API process started.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load}>
          Refresh
        </Button>
      </div>

      {err && <p className="text-sm text-destructive">{err}</p>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="LLM calls"
          value={metrics ? String(metrics.calls) : "—"}
          hint={metrics ? `${metrics.errors} errors` : undefined}
        />
        <Stat
          label="Tokens"
          value={
            metrics
              ? (metrics.prompt_tokens + metrics.completion_tokens).toLocaleString()
              : "—"
          }
          hint={
            metrics
              ? `${metrics.prompt_tokens.toLocaleString()} in / ${metrics.completion_tokens.toLocaleString()} out`
              : undefined
          }
        />
        <Stat
          label="Cost"
          value={metrics ? `$${metrics.cost_usd.toFixed(4)}` : "—"}
          hint="$0 on free-tier providers"
        />
        <Stat label="Avg latency" value={metrics ? `${metrics.avg_latency_ms}ms` : "—"} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Documents" value={String(docs.length)} />
        <Stat label="Processed" value={String(processed)} />
        <Stat label="Indexed chunks" value={String(chunks)} />
      </div>

      {metrics && Object.keys(metrics.by_model).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">By model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {Object.entries(metrics.by_model).map(([model, v]) => (
              <div key={model} className="flex justify-between border-b py-1 last:border-0">
                <span className="font-mono text-xs">{model}</span>
                <span className="text-muted-foreground tabular-nums">
                  {v.calls} calls · {v.tokens.toLocaleString()} tokens
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
