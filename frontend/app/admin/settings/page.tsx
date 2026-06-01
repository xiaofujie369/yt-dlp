"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { api } from "@/lib/api";

type Setting = { id: number; key: string; value: string; type: string; description?: string };

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([]);
  useEffect(() => { api<Setting[]>("/admin/settings").then(setSettings); }, []);
  return (
    <AppShell admin>
      <Card>
        <h1 className="mb-4 text-xl font-semibold">系统配置</h1>
        <div className="grid gap-3">
          {settings.map((item) => (
            <div key={item.key} className="grid gap-2 rounded-md border border-slate-100 p-3 md:grid-cols-[260px_1fr_100px]">
              <div><div className="font-medium">{item.key}</div><div className="text-xs text-slate-500">{item.description}</div></div>
              <input className="h-9 rounded-md border px-3 text-sm" value={item.value} onChange={(event) => setSettings((prev) => prev.map((next) => next.key === item.key ? { ...next, value: event.target.value } : next))} />
              <button className="rounded-md bg-koyun-600 px-3 text-sm font-medium text-white" onClick={() => api(`/admin/settings`, { method: "PATCH", body: JSON.stringify(item) })}>保存</button>
            </div>
          ))}
        </div>
      </Card>
    </AppShell>
  );
}
