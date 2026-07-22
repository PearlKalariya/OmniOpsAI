"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export function LoginCard() {
  const { login, register } = useAuth();
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("secret123");
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<void>, okMsg?: string) => {
    setBusy(true);
    try {
      await fn();
      if (okMsg) toast.success(okMsg);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>
          OmniOps <span className="text-primary">AI</span>
        </CardTitle>
        <CardDescription>
          Multimodal RAG · multi-agent orchestration · LLM evaluation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") run(() => login(email, password));
            }}
          />
        </div>
        <div className="flex gap-2 pt-1">
          <Button
            className="flex-1"
            disabled={busy}
            onClick={() => run(() => login(email, password))}
          >
            Log in
          </Button>
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() => run(() => register(email, password), "Registered — now log in")}
          >
            Register
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
