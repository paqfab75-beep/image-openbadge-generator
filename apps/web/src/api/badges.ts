/** The badge generator's two API calls, over fetch — no generated client needed for these two. */

import { env } from "../env";

const baseUrl = () => env.VITE_API_URL.replace(/\/+$/u, "");

export interface GeneratedBadge {
  png_b64: string;
  size_bytes: number;
  width: number;
  height: number;
}

export interface Charte {
  colors: string[];
}

/** FastAPI refusals read as one sentence, however they encode it (`{detail}` strings, or fields). */
const toMessage = (body: unknown, status: number): string => {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((problem) =>
          problem && typeof problem === "object" && "msg" in problem
            ? String((problem as { msg: unknown }).msg)
            : String(problem)
        )
        .join(" · ");
    }
    if (detail && typeof detail === "object" && "message" in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  return `La demande a échoué (${status}).`;
};

const post = async <T>(path: string, payload: unknown): Promise<T> => {
  const res = await fetch(`${baseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => undefined);
  if (!res.ok) {
    throw new Error(toMessage(body, res.status));
  }
  return body as T;
};

export const generateBadge = (payload: unknown): Promise<GeneratedBadge> =>
  post("/api/v1/badges/generate", payload);

export const extractCharte = (payload: unknown): Promise<Charte> =>
  post("/api/v1/badges/charte/extract", payload);

export const generatedBadgeToDataUrl = (badge: GeneratedBadge): string =>
  `data:image/png;base64,${badge.png_b64}`;
