"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { api, fmtTime } from "@/lib/api";

type Log = { id: number; action: string; target_type?: string; target_id?: string; detail?: string; ip?: string; created_at: string };

export default function AdminLogsPage() {
  const [data, setData] = useState<{ items: Log[] } | null>(null);
  useEffect(() => { api<{ items: Log[] }>("/admin/logs").then(setData); }, []);
  return (
    <AppShell admin>
      <Card>
        <h1 className="mb-4 text-xl font-semibold">操作日志</h1>
        <table className="w-full text-left text-sm">
          <thead className="border-b text-slate-500"><tr><th className="py-3">动作</th><th>目标</th><th>IP</th><th>时间</th></tr></thead>
          <tbody>{(data?.items || []).map((log) => <tr key={log.id} className="border-b border-slate-100"><td className="py-3">{log.action}</td><td>{log.target_type}:{log.target_id}</td><td>{log.ip || "-"}</td><td>{fmtTime(log.created_at)}</td></tr>)}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
