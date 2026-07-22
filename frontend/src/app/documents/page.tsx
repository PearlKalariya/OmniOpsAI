"use client";

/** Upload + ingestion status. Uploads return immediately (Celery worker
 *  processes them), so we poll the document until it leaves "queued". */

import { useCallback, useEffect, useRef, useState } from "react";
import { api, type DocumentOut } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";

const TERMINAL = ["processed", "failed", "no_text", "index_failed"];

function statusVariant(status: string) {
  if (status === "processed") return "default" as const;
  if (status === "failed" || status === "index_failed") return "destructive" as const;
  return "secondary" as const;
}

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(
    () => api.listDocuments().then(setDocs).catch(() => {}),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  // Poll while anything is still being ingested.
  useEffect(() => {
    if (docs.every((d) => TERMINAL.includes(d.status))) return;
    const t = setTimeout(load, 2000);
    return () => clearTimeout(t);
  }, [docs, load]);

  const upload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const doc = await api.upload(file);
      toast.success(`Uploaded ${doc.filename} — ingesting…`);
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Documents</h1>
        <p className="text-sm text-muted-foreground">
          PDF, CSV, text, images (OCR + captioning), or audio (transcribed).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Upload</CardTitle>
          <CardDescription>
            Ingestion runs asynchronously on the Celery worker: extract → chunk →
            BM25 index + vector embed.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Input ref={fileRef} type="file" className="max-w-sm" />
          <Button onClick={upload} disabled={busy}>
            {busy ? "Uploading…" : "Upload"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Corpus ({docs.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {docs.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing uploaded yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Chunks</TableHead>
                  <TableHead className="text-right">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {docs.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.filename}</TableCell>
                    <TableCell className="text-muted-foreground text-xs font-mono">
                      {d.content_type}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {d.chunk_count ?? "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant={statusVariant(d.status)}>{d.status}</Badge>
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
