"use client";

/** Agent execution graph + retrieval inspector for one agent run. */

import type { AgentResponse, TraceEntry } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function nodeDetail(t: TraceEntry) {
  const bits: string[] = [];
  if (typeof t.mode === "string") bits.push(t.mode);
  if (typeof t.hits === "number") bits.push(`${t.hits} hits`);
  if (t.reranked === true) bits.push("reranked");
  if (typeof t.fallback_from === "string") bits.push(`fallback from ${t.fallback_from}`);
  if (typeof t.format === "string") bits.push(t.format);
  if (t.grounded === true) bits.push("grounded");
  if (t.grounded === false) bits.push("not grounded");
  return bits.join(" · ");
}

export function AgentTrace({ result }: { result: AgentResponse }) {
  const v = result.verification;

  return (
    <div className="space-y-4">
      {/* execution graph */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Agent execution graph</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-stretch gap-2">
            {result.trace.map((t, i) => (
              <div key={i} className="flex items-center gap-2">
                <div className="rounded-lg border bg-card px-3 py-2 min-w-28">
                  <div className="text-xs font-medium capitalize">{t.node}</div>
                  <div className="text-[11px] text-muted-foreground tabular-nums">
                    {t.ms}ms
                  </div>
                  {nodeDetail(t) && (
                    <div className="text-[11px] text-muted-foreground mt-0.5">
                      {nodeDetail(t)}
                    </div>
                  )}
                </div>
                {i < result.trace.length - 1 && (
                  <span className="text-muted-foreground">→</span>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* answer + verification */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            Answer
            {v?.grounded === true && <Badge>grounded</Badge>}
            {v?.grounded === false && <Badge variant="destructive">not grounded</Badge>}
            {v?.grounded == null && <Badge variant="secondary">unverified</Badge>}
            {result.model && (
              <span className="ml-auto text-[11px] font-mono font-normal text-muted-foreground">
                {result.model}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm whitespace-pre-wrap">{result.answer}</p>
          {v && (
            <p className="text-xs text-muted-foreground">
              {v.citations_used && v.citations_used.length > 0 && (
                <>cites [{v.citations_used.join("], [")}] · </>
              )}
              {v.phantom_citations && v.phantom_citations.length > 0 && (
                <span className="text-destructive">
                  phantom [{v.phantom_citations.join("], [")}] ·{" "}
                </span>
              )}
              {v.notes}
            </p>
          )}
        </CardContent>
      </Card>

      {/* report */}
      {result.report && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">
              Report · {result.report_format}
              {result.delivered_to && (
                <Badge className="ml-2">sent to #{result.delivered_to}</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-sm whitespace-pre-wrap font-sans">{result.report}</pre>
          </CardContent>
        </Card>
      )}

      {/* retrieval inspector */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">
            Retrieved passages ({result.sources.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {result.sources.map((s, i) => (
            <div key={s.chunk_id} className="rounded-md border p-3">
              <div className="flex items-center gap-2 text-[11px] text-muted-foreground mb-1">
                <span className="font-medium text-foreground">[{i + 1}]</span>
                <span className="tabular-nums">
                  {s.rerank_score != null
                    ? `rerank ${s.rerank_score.toFixed(3)}`
                    : `score ${s.score.toFixed(2)}`}
                </span>
                {s.sources?.length > 0 && <span>· {s.sources.join(" + ")}</span>}
              </div>
              <p className="text-xs text-muted-foreground line-clamp-4">{s.content}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
