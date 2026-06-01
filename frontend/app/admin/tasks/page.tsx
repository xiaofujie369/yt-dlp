"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card, statusTone } from "@/components/ui";
import { api, fmtTime, formatBytes, type Page, type Task } from "@/lib/api";

export default function AdminTasksPage() {
  const [data, setData] = useState<Page<Task> | null>(null);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const params = new URLSearchParams();
    if (status) params.set("status_filter", status);
    if (q) params.set("q", q);
    api<Page<Task>>(`/admin/tasks?${params}`).then(setData);
  }, [status, q]);
  return (
    <AppShell admin>
      <Card>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-xl font-semibold">下载任务</h1>
          <div className="flex gap-2">
            <input className="h-9 rounded-md border px-3 text-sm" placeholder="搜索" value={q} onChange={(event) => setQ(event.target.value)} />
            <select className="h-9 rounded-md border px-3 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">全部状态</option>
              {["queued", "downloading", "completed", "failed", "cancelled"].map((item) => <option key={item}>{item}</option>)}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-slate-500"><tr><th className="py-3">任务ID</th><th>平台</th><th>类型</th><th>状态</th><th>进度</th><th>大小</th><th>创建</th></tr></thead>
            <tbody>{(data?.items || []).map((task) => (
              <tr key={task.task_id} className="border-b border-slate-100">
                <td className="max-w-[280px] truncate py-3">{task.task_id}</td>
                <td>{task.domain}</td>
                <td>{task.task_type}</td>
                <td><Badge tone={statusTone(task.status)}>{task.status}</Badge></td>
                <td>{task.progress.toFixed(0)}%</td>
                <td>{formatBytes(task.file_size)}</td>
                <td>{fmtTime(task.created_at)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}
