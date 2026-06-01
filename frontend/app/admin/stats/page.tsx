"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { api, formatBytes } from "@/lib/api";

type Stat = { date: string; total_tasks: number; success_tasks: number; failed_tasks: number; total_file_size: number; active_users: number };

export default function AdminStatsPage() {
  const [stats, setStats] = useState<Stat[]>([]);
  useEffect(() => { api<Stat[]>("/admin/stats/daily").then(setStats); }, []);
  return (
    <AppShell admin>
      <Card>
        <h1 className="mb-4 text-xl font-semibold">统计报表</h1>
        <table className="w-full text-left text-sm">
          <thead className="border-b text-slate-500"><tr><th className="py-3">日期</th><th>任务</th><th>成功</th><th>失败</th><th>流量</th><th>活跃用户</th></tr></thead>
          <tbody>{stats.map((row) => <tr key={row.date} className="border-b border-slate-100"><td className="py-3">{row.date}</td><td>{row.total_tasks}</td><td>{row.success_tasks}</td><td>{row.failed_tasks}</td><td>{formatBytes(row.total_file_size)}</td><td>{row.active_users}</td></tr>)}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
