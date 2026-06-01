"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card, statusTone } from "@/components/ui";
import { api, fmtTime, formatBytes, type Page, type Task } from "@/lib/api";

export default function TasksPage() {
  const [data, setData] = useState<Page<Task> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Page<Task>>("/tasks").then(setData).catch((err) => setError(err.message));
  }, []);

  return (
    <AppShell>
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">我的任务</h1>
          <Link href="/" className="text-sm font-medium text-koyun-700">新建任务</Link>
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-slate-500">
              <tr>
                <th className="py-3">任务</th>
                <th>类型</th>
                <th>状态</th>
                <th>进度</th>
                <th>大小</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((task) => (
                <tr key={task.task_id} className="border-b border-slate-100">
                  <td className="max-w-[320px] py-3">
                    <Link href={`/tasks/${task.task_id}`} className="font-medium text-koyun-700">{task.task_id}</Link>
                    <div className="truncate text-xs text-slate-500">{task.url}</div>
                  </td>
                  <td>{task.task_type}</td>
                  <td><Badge tone={statusTone(task.status)}>{task.status}</Badge></td>
                  <td>{task.progress.toFixed(0)}%</td>
                  <td>{formatBytes(task.file_size)}</td>
                  <td>{fmtTime(task.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}
