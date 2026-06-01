"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card, statusTone } from "@/components/ui";
import { API_BASE, api, fmtTime, formatBytes, getToken, type Task } from "@/lib/api";

type FileItem = { id: number; filename: string; file_size: number; expired_at?: string | null; status: string };

export default function TaskDetailPage() {
  const params = useParams<{ task_id: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const next = await api<Task>(`/tasks/${params.task_id}`);
        if (active) setTask(next);
        if (next.status === "completed") {
          const taskFiles = await api<FileItem[]>(`/tasks/${params.task_id}/files`);
          if (active) setFiles(taskFiles);
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : "加载失败");
      }
    }
    load();
    const timer = setInterval(load, 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [params.task_id]);

  async function cancel() {
    const next = await api<Task>(`/tasks/${params.task_id}/cancel`, { method: "POST" });
    setTask(next);
  }

  return (
    <AppShell>
      <Card className="space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-xl font-semibold">任务详情</h1>
          {task ? <Badge tone={statusTone(task.status)}>{task.status}</Badge> : null}
        </div>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {task ? (
          <>
            <div className="h-3 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full bg-koyun-600" style={{ width: `${Math.min(task.progress, 100)}%` }} />
            </div>
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Info label="任务ID" value={task.task_id} />
              <Info label="平台" value={task.domain} />
              <Info label="类型" value={task.task_type} />
              <Info label="文件" value={task.filename || "-"} />
              <Info label="大小" value={formatBytes(task.file_size)} />
              <Info label="清理时间" value={fmtTime(task.expired_at)} />
              <Info label="创建时间" value={fmtTime(task.created_at)} />
              <Info label="完成时间" value={fmtTime(task.updated_at)} />
            </dl>
            {task.error_message ? <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">{task.error_message}</p> : null}
            <div className="flex gap-3">
              <Button onClick={cancel} disabled={["completed", "failed", "cancelled"].includes(task.status)}>取消任务</Button>
              {files[0] ? (
                <a
                  className="inline-flex h-10 items-center justify-center rounded-md border border-koyun-600 px-4 text-sm font-medium text-koyun-700"
                  href={`${API_BASE}/api/files/${files[0].id}/download`}
                  onClick={(event) => {
                    event.preventDefault();
                    fetch(`${API_BASE}/api/files/${files[0].id}/download`, { headers: { Authorization: `Bearer ${getToken()}` } })
                      .then((response) => response.blob())
                      .then((blob) => {
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = files[0].filename;
                        link.click();
                        URL.revokeObjectURL(url);
                      });
                  }}
                >
                  下载文件
                </a>
              ) : null}
            </div>
          </>
        ) : null}
      </Card>
    </AppShell>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium">{value}</dd>
    </div>
  );
}
