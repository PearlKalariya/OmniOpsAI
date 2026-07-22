"use client";

/** Auth state shared across pages: token presence + login/register/logout. */

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, clearToken, getToken } from "@/lib/api";

type AuthCtx = {
  authed: boolean;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authed, setAuthed] = useState(false);
  const [ready, setReady] = useState(false);

  // Probe a cheap authed endpoint so a stale/expired token doesn't leave the
  // UI thinking it's logged in.
  useEffect(() => {
    if (!getToken()) {
      setReady(true);
      return;
    }
    api
      .metrics()
      .then(() => setAuthed(true))
      .catch(() => clearToken())
      .finally(() => setReady(true));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    await api.login(email, password);
    setAuthed(true);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await api.register(email, password);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setAuthed(false);
  }, []);

  return (
    <Ctx.Provider value={{ authed, ready, login, register, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
