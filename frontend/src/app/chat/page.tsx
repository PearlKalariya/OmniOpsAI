"use client";

/** Ask the agent. Optionally render the answer as a report format
 *  (summary / ticket / email / slack) via the Report Agent. */

import { useState } from "react";
import { api, type AgentResponse } from "@/lib/api";
import { AgentTrace } from "@/components/agent-trace";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const FORMATS = [
  { value: "", label: "Answer only" },
  { value: "summary", label: "Summary" },
  { value: "report", label: "Tech report" },
  { value: "ticket", label: "Jira ticket" },
  { value: "email", label: "Email" },
  { value: "slack", label: "Slack" },
];

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [format, setFormat] = useState("");
  const [slackChannel, setSlackChannel] = useState("");
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [busy, setBusy] = useState(false);

  const ask = async () => {
    const q = question.trim();
    if (!q) return;
    setBusy(true);
    setResult(null);
    try {
      const r = format
        ? await api.report(q, format, slackChannel || undefined)
        : await api.ask(q);
      setResult(r);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Chat</h1>
        <p className="text-sm text-muted-foreground">
          Planner → retrieval (+ rerank) → answer → verifier, over your documents.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Ask</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <Input
              placeholder="What does the document say about…?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !busy) ask();
              }}
            />
            <Button onClick={ask} disabled={busy}>
              {busy ? "Running…" : "Ask"}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {FORMATS.map((f) => (
              <Button
                key={f.value}
                size="sm"
                variant={format === f.value ? "default" : "outline"}
                onClick={() => setFormat(f.value)}
              >
                {f.label}
              </Button>
            ))}
            {format === "slack" && (
              <Input
                className="max-w-40 h-8"
                placeholder="#channel (optional)"
                value={slackChannel}
                onChange={(e) => setSlackChannel(e.target.value)}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {busy && (
        <p className="text-sm text-muted-foreground">Running the agent graph…</p>
      )}
      {result && <AgentTrace result={result} />}
    </div>
  );
}
