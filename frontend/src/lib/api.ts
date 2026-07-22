/**
 * Typed client for the OmniOps FastAPI backend.
 *
 * The token lives in localStorage; every call attaches it. Backend errors
 * come back as {detail: string} — unwrapped into thrown Errors so callers
 * can just try/catch.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "omniops_token";

export const getToken = () =>
  typeof window === "undefined" ? null : localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const isForm = init.body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(isForm ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail[0]?.msg ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

/* ---------- types (mirror the FastAPI schemas) ---------- */

export type DocumentOut = {
  id: string;
  filename: string;
  content_type: string;
  status: string;
  created_at: string;
  size_bytes: number | null;
  page_count: number | null;
  char_count: number | null;
  chunk_count: number | null;
};

export type SearchHit = {
  chunk_id: string;
  score: number;
  document_id: string;
  chunk_index: number;
  content: string;
  sources: string[];
  rerank_score: number | null;
};

export type TraceEntry = {
  node: string;
  ms: number;
  [k: string]: unknown;
};

export type Verification = {
  grounded: boolean | null;
  notes: string;
  citations_used?: number[];
  phantom_citations?: number[];
  uncited?: boolean;
};

export type AgentResponse = {
  answer: string | null;
  model: string | null;
  plan: Record<string, unknown>;
  verification: Verification | null;
  sources: SearchHit[];
  trace: TraceEntry[];
  report: string | null;
  report_format: string | null;
  delivered_to: string | null;
};

export type Metrics = {
  calls: number;
  errors: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
  by_model: Record<string, { calls: number; tokens: number }>;
};

export type EvalResultRow = {
  question: string;
  answer: string | null;
  faithfulness: number | null;
  answer_relevance: number | null;
  context_precision: number | null;
  grounded: boolean | null;
  latency_ms: number | null;
  notes: string | null;
};

export type EvalRun = {
  id: string;
  dataset_name: string;
  model: string;
  num_questions: number;
  avg_faithfulness: number | null;
  avg_answer_relevance: number | null;
  avg_context_precision: number | null;
  avg_latency_ms: number | null;
  created_at: string;
  results?: EvalResultRow[];
};

/* ---------- endpoints ---------- */

export const api = {
  register: (email: string, password: string) =>
    request<{ id: string; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: async (email: string, password: string) => {
    const r = await request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(r.access_token);
    return r;
  },

  listDocuments: () => request<DocumentOut[]>("/api/documents"),
  getDocument: (id: string) => request<DocumentOut>(`/api/documents/${id}`),

  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<DocumentOut>("/api/documents/upload", {
      method: "POST",
      body: fd,
    });
  },

  ask: (question: string) =>
    request<AgentResponse>("/api/agent/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  report: (question: string, format: string, slack_channel?: string) =>
    request<AgentResponse>("/api/agent/report", {
      method: "POST",
      body: JSON.stringify({ question, format, slack_channel }),
    }),

  metrics: () => request<Metrics>("/api/metrics"),

  listEvalRuns: () => request<EvalRun[]>("/api/eval"),
  runEval: (dataset_name: string, items: { question: string; expected?: string }[]) =>
    request<EvalRun>("/api/eval/run", {
      method: "POST",
      body: JSON.stringify({ dataset_name, items }),
    }),
};
