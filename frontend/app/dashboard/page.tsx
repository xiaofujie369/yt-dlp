"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { api, type User } from "@/lib/api";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    api<User>("/auth/me").then(setUser).catch(() => setUser(null));
  }, []);
  return (
    <AppShell>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><Metric label="今日额度" value={`${user?.used_today ?? 0}/${user?.daily_quota ?? 0}`} /></Card>
        <Card><Metric label="角色" value={user?.role || "-"} /></Card>
        <Card><Metric label="状态" value={user?.status || "-"} /></Card>
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><div className="text-sm text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}
