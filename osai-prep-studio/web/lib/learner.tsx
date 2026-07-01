"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api, readCookie } from "./api";

interface LearnerCtx {
  learner: string;
  token: string | null;
  authed: boolean;
  setLearner: (v: string) => void;
  login: (learner: string, token: string) => void;
  logout: () => void;
}

const Ctx = createContext<LearnerCtx>({
  learner: "demo",
  token: null,
  authed: false,
  setLearner: () => {},
  login: () => {},
  logout: () => {},
});

export function LearnerProvider({ children }: { children: React.ReactNode }) {
  const [learner, setState] = useState("demo");
  const [token, setToken] = useState<string | null>(null);
  const [cookieSession, setCookieSession] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const l = window.localStorage.getItem("osai_learner");
    if (l) setState(l);
    const t = window.localStorage.getItem("osai_token");
    if (t) setToken(t);
    setCookieSession(readCookie("osai_csrf") !== "");
  }, []);

  const setLearner = (v: string) => {
    setState(v);
    if (typeof window !== "undefined") window.localStorage.setItem("osai_learner", v);
  };

  const login = (l: string, t: string) => {
    setState(l);
    if (typeof window !== "undefined") window.localStorage.setItem("osai_learner", l);
    // cookie mode: the server set an HttpOnly session + a readable osai_csrf cookie —
    // keep no bearer token in JS (XSS-safe); the cookie carries the session.
    const cookieMode = readCookie("osai_csrf") !== "";
    setCookieSession(cookieMode);
    if (cookieMode) {
      setToken(null);
      if (typeof window !== "undefined") window.localStorage.removeItem("osai_token");
    } else {
      setToken(t);
      if (typeof window !== "undefined") window.localStorage.setItem("osai_token", t);
    }
  };

  const logout = () => {
    // best-effort server-side revocation (invalidates the session everywhere), then clear local
    api.logout().catch(() => {});
    setToken(null);
    setCookieSession(false);
    if (typeof window !== "undefined") window.localStorage.removeItem("osai_token");
  };

  return (
    <Ctx.Provider
      value={{ learner, token, authed: !!token || cookieSession, setLearner, login, logout }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useLearner(): LearnerCtx {
  return useContext(Ctx);
}
