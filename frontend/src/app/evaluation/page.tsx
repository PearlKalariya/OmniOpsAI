"use client";

/** LLM-as-judge evaluation: run a question set through the agent and score
 *  faithfulness / answer relevance / context precision. */

import { useCallback, useEffect, useState } from "react";
import { api, type EvalRun } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";

function pct(v: number | null) {
  return v == null ? "—" : `${(v * 100).toFixed(0)}%`;
}

/** Colour a 0..1 score: green good, amber middling, red poor. */
function scoreClass(v: number | null) {
  if (v == null) return "text-muted-foreground";
  if (v >= 0.8) return "text-emerald-500";
  if (v >= 0.5) return "text-amber-500";
  return "text-destructive";
}

export default function EvaluationPage() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [name, setName] = useState("smoke");
  const [questions, setQuestions] = useState("");
  const [busy, setBusy] = useState(false);
  const [latest, setLatest] = useState<EvalRun | null>(null);

  const load = useCallback(
    () => api.listEvalRuns().then(setRuns).catch(() => {}),
    [],
  );
  useEffect(() => {
    load();
  }, [load]);

  const run = async () => {
    const items = questions
      .split("\n")
      .map((q) => q.trim())
      .filter(Boolean)
      .map((question) => ({ question }));
    if (items.length === 0) {
      toast.error("Add at least one question (one per line)");
      return;
    }
    setBusy(true);
    try {
      const r = await api.runEval(name || "adhoc", items);
      setLatest(r);
      toast.success(`Scored ${r.num_questions} questions`);
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Eval failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Evaluation</h1>
        <p className="text-sm text-muted-foreground">
          Each question runs through the full agent, then a judge LLM scores the
          answer against the retrieved context.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">New run</CardTitle>
          <CardDescription>
            One question per line. Rate-limited to 3 runs/minute — each question
            costs an agent run plus a judge call.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2 max-w-xs">
            <Label htmlFor="ds">Dataset name</Label>
            <Input id="ds" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="qs">Questions</Label>
            <textarea
              id="qs"
              rows={4}
              className="w-full rounded-md border bg-transparent px-3 py-2 text-sm"
              placeholder={"What caused the outage?\nWho approved the change?"}
              value={questions}
              onChange={(e) => setQuestions(e.target.value)}
            />
          </div>
          <Button onClick={run} disabled={busy}>
            {busy ? "Scoring…" : "Run evaluation"}
          </Button>
        </CardContent>
      </Card>

      {latest?.results && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">
              Latest run · {latest.dataset_name}
            </CardTitle>
            <CardDescription>
              faithfulness {pct(latest.avg_faithfulness)} · relevance{" "}
              {pct(latest.avg_answer_relevance)} · precision{" "}
              {pct(latest.avg_context_precision)}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Question</TableHead>
                  <TableHead className="text-right">Faith.</TableHead>
                  <TableHead className="text-right">Rel.</TableHead>
                  <TableHead className="text-right">Prec.</TableHead>
                  <TableHead className="text-right">Grounded</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {latest.results.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell className="max-w-sm truncate">{r.question}</TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.faithfulness)}`}>
                      {pct(r.faithfulness)}
                    </TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.answer_relevance)}`}>
                      {pct(r.answer_relevance)}
                    </TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.context_precision)}`}>
                      {pct(r.context_precision)}
                    </TableCell>
                    <TableCell className="text-right">
                      {r.grounded === true ? (
                        <Badge>yes</Badge>
                      ) : r.grounded === false ? (
                        <Badge variant="destructive">no</Badge>
                      ) : (
                        <Badge variant="secondary">—</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Past runs ({runs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {runs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No runs yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Dataset</TableHead>
                  <TableHead className="text-right">Qs</TableHead>
                  <TableHead className="text-right">Faith.</TableHead>
                  <TableHead className="text-right">Rel.</TableHead>
                  <TableHead className="text-right">Prec.</TableHead>
                  <TableHead className="text-right">Latency</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {runs.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">{r.dataset_name}</TableCell>
                    <TableCell className="text-right tabular-nums">{r.num_questions}</TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.avg_faithfulness)}`}>
                      {pct(r.avg_faithfulness)}
                    </TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.avg_answer_relevance)}`}>
                      {pct(r.avg_answer_relevance)}
                    </TableCell>
                    <TableCell className={`text-right tabular-nums ${scoreClass(r.avg_context_precision)}`}>
                      {pct(r.avg_context_precision)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-muted-foreground">
                      {r.avg_latency_ms ? `${Math.round(r.avg_latency_ms)}ms` : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
