import { clsx } from "clsx";
import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={clsx(
        "inline-flex h-10 items-center justify-center rounded-md bg-koyun-600 px-4 text-sm font-medium text-white transition hover:bg-koyun-700 disabled:cursor-not-allowed disabled:opacity-60",
        className
      )}
      {...props}
    />
  );
}

export function LinkButton({ href, children, className }: { href: string; children: ReactNode; className?: string }) {
  return (
    <Link
      href={href}
      className={clsx(
        "inline-flex h-10 items-center justify-center rounded-md bg-koyun-600 px-4 text-sm font-medium text-white transition hover:bg-koyun-700",
        className
      )}
    >
      {children}
    </Link>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={clsx("rounded-lg border border-slate-200 bg-white p-5 shadow-sm", className)}>{children}</section>;
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "green" | "red" | "yellow" | "blue" | "neutral" }) {
  const tones = {
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    red: "bg-red-50 text-red-700 ring-red-200",
    yellow: "bg-amber-50 text-amber-700 ring-amber-200",
    blue: "bg-sky-50 text-sky-700 ring-sky-200",
    neutral: "bg-slate-50 text-slate-700 ring-slate-200"
  };
  return <span className={clsx("inline-flex rounded px-2 py-1 text-xs font-medium ring-1", tones[tone])}>{children}</span>;
}

export function statusTone(status: string): "green" | "red" | "yellow" | "blue" | "neutral" {
  if (status === "completed") return "green";
  if (["failed", "cancelled", "deleted", "expired"].includes(status)) return "red";
  if (status === "queued") return "yellow";
  if (["downloading", "merging", "transcoding"].includes(status)) return "blue";
  return "neutral";
}
