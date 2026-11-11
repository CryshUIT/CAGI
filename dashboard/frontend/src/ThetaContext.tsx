import { createContext, useContext, useState, type ReactNode } from "react";

interface ThetaCtx {
  theta: number;
  setTheta: (t: number) => void;
  model: "m1_cal" | "b3_cal";
  setModel: (m: "m1_cal" | "b3_cal") => void;
}

const Ctx = createContext<ThetaCtx | null>(null);

export function ThetaProvider({ children }: { children: ReactNode }) {
  const [theta, setTheta] = useState(0.5);
  const [model, setModel] = useState<"m1_cal" | "b3_cal">("m1_cal");
  return <Ctx.Provider value={{ theta, setTheta, model, setModel }}>{children}</Ctx.Provider>;
}

export function useTheta() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTheta must be used within ThetaProvider");
  return ctx;
}
