"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Download, RotateCcw, Trash2, XCircle } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card, statusTone } from "@/components/ui";
import { API_BASE, api, fmtTime, formatBytes, getToken, type Page, type Task } from "@/lib/api";

type FileItem = {
  id: number;
  filename: string;
  file_size: number;
  expired_at?: string | null;
  status: string;
};

const cancellableStatuses = new Set(["pending", "queued", "running", "downloading", "processing", "merging", "transcoding"]);
const retryableStatuses = new Set(["failed", "cancelled"]);

export default function TasksPage() {
  const [data, setData] = useState<Page<Task> | null>(null);
  const [error, setError] = useState("");
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);

  async function loadTasks() {
    try {
      setError("");
      setData(await api<Page<Task>>("/tasks"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "任务列表加载失败");
    }
  }

  useEffect(() => {
    loadTasks();
  }, []);

  async function runTaskAction(taskId: string, action: () => Promise<void>) {
    setBusyTaskId(taskId);
    setError("");
    try {
      await action();
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setBusyTaskId(null);
    }
  }

  async function cancelTask(task: Task) {
    if (!window.confirm("确定要取消这个下载任务吗？正在执行的 yt-dlp 进程会被终止。")) return;
    await runTaskAction(task.task_id, () => api(`/tasks/${task.task_id}/cancel`, { method: "POST" }));
  }

  async function retryTask(task: Task) {
    await runTaskAction(task.task_id, () => api(`/tasks/${task.task_id}/retry`, { method: "POST" }));
  }

  async function deleteTask(task: Task) {
    if (!window.confirm("确定要删除这个任务记录吗？")) return;
    await runTaskAction(task.task_id, () => api(`/tasks/${task.task_id}`, { method: "DELETE" }));
  }

  async function downloadTask(task: Task) {
    await runTaskAction(task.task_id, async () => {
      const fileId = task.file_id ?? (await api<FileItem[]>(`/tasks/${task.task_id}/files`))[0]?.id;
      if (!fileId) throw new Error("没有可下载文件");

      const response = await fetch(`${API_BASE}/api/files/${fileId}/download`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (!response.ok) throw new Error("文件下载失败");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = task.filename || `task-${task.task_id}`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  return (
    <AppShell>
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">我的任务</h1>
          <Link href="/" className="text-sm font-medium text-koyun-700">
            新建任务
          </Link>
        </div>
        {error ? <p className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
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
                <th className="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((task) => (
                <tr key={task.task_id} className="border-b border-slate-100">
                  <td className="max-w-[320px] py-3">
                    <Link href={`/tasks/${task.task_id}`} className="font-medium text-koyun-700">
                      {task.task_id}
                    </Link>
                    <div className="truncate text-xs text-slate-500">{task.url}</div>
                  </td>
                  <td>{task.task_type}</td>
                  <td>
                    <Badge tone={statusTone(task.status)}>{task.status}</Badge>
                  </td>
                  <td>{task.progress.toFixed(0)}%</td>
                  <td>{formatBytes(task.file_size)}</td>
                  <td>{fmtTime(task.created_at)}</td>
                  <td>
                    <TaskActions
                      task={task}
                      busy={busyTaskId === task.task_id}
                      onCancel={() => cancelTask(task)}
                      onDownload={() => downloadTask(task)}
                      onRetry={() => retryTask(task)}
                      onDelete={() => deleteTask(task)}
                    />
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 ? (
                <tr>
                  <td className="py-8 text-center text-slate-500" colSpan={7}>
                    暂无任务
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}

function TaskActions({
  task,
  busy,
  onCancel,
  onDownload,
  onRetry,
  onDelete
}: {
  task: Task;
  busy: boolean;
  onCancel: () => void;
  onDownload: () => void;
  onRetry: () => void;
  onDelete: () => void;
}) {
  if (cancellableStatuses.has(task.status)) {
    return (
      <div className="flex justify-end">
        <ActionButton disabled={busy} tone="danger" onClick={onCancel}>
          <XCircle className="h-4 w-4" />
          取消
        </ActionButton>
      </div>
    );
  }

  if (task.status === "completed") {
    return (
      <div className="flex justify-end gap-2">
        <ActionButton disabled={busy} onClick={onDownload}>
          <Download className="h-4 w-4" />
          下载
        </ActionButton>
        <ActionButton disabled={busy} tone="muted" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
          删除
        </ActionButton>
      </div>
    );
  }

  if (retryableStatuses.has(task.status)) {
    return (
      <div className="flex justify-end gap-2">
        <ActionButton disabled={busy} onClick={onRetry}>
          <RotateCcw className="h-4 w-4" />
          重试
        </ActionButton>
        <ActionButton disabled={busy} tone="muted" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
          删除
        </ActionButton>
      </div>
    );
  }

  return <div className="text-right text-xs text-slate-400">-</div>;
}

function ActionButton({
  children,
  tone = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode; tone?: "primary" | "danger" | "muted" }) {
  const toneClass = {
    primary: "border-koyun-600 bg-koyun-50 text-koyun-700 hover:bg-koyun-100",
    danger: "border-red-200 bg-red-50 text-red-700 hover:bg-red-100",
    muted: "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
  }[tone];
  return (
    <button
      className={`inline-flex h-8 items-center gap-1 rounded-md border px-3 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${toneClass}`}
      {...props}
    >
      {children}
    </button>
  );
}
