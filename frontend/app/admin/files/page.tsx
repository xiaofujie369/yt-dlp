"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card } from "@/components/ui";
import { api, fmtTime, formatBytes, type Page } from "@/lib/api";

type FileItem = { id: number; task_id: number; filename: string; file_size: number; download_count: number; expired_at?: string; status: string; created_at: string };

export default function AdminFilesPage() {
  const [data, setData] = useState<Page<FileItem> | null>(null);
  useEffect(() => { api<Page<FileItem>>("/admin/files").then(setData); }, []);
  return (
    <AppShell admin>
      <Card>
        <h1 className="mb-4 text-xl font-semibold">文件管理</h1>
        <table className="w-full text-left text-sm">
          <thead className="border-b text-slate-500"><tr><th className="py-3">文件名</th><th>大小</th><th>下载</th><th>过期</th><th>状态</th></tr></thead>
          <tbody>{(data?.items || []).map((file) => <tr key={file.id} className="border-b border-slate-100"><td className="py-3">{file.filename}</td><td>{formatBytes(file.file_size)}</td><td>{file.download_count}</td><td>{fmtTime(file.expired_at)}</td><td><Badge>{file.status}</Badge></td></tr>)}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
