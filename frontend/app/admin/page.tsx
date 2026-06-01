"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { formatBytes } from "@/lib/api";
import { api } from "@/lib/api";

type Dashboard = {
  today_tasks: number;
  today_success: number;
  today_failed: number;
  today_bytes: number;
  queued_tasks: number;
  downloading_tasks: number;
  disk_used_bytes: number;
  redis_status: string;
  worker_status: string;
  ytdlp_version: string;
  ffmpeg_available: boolean;
  recent_daily: { date: string; total_tasks: number; success_tasks: number; failed_tasks: number }[];
  popular_platforms: { platform: string; count: number }[];
  failure_reasons: { reason: string; count: number }[];
};

export default function AdminDashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  useEffect(() => {
    api<Dashboard>("/admin/dashboard").then(setData);
  }, []);
  const cards = [
    ["今日任务", data?.today_tasks],
    ["今日成功", data?.today_success],
    ["今日失败", data?.today_failed],
    ["今日流量", formatBytes(data?.today_bytes)],
    ["排队任务", data?.queued_tasks],
    ["下载中", data?.downloading_tasks],
    ["磁盘使用", formatBytes(data?.disk_used_bytes)],
    ["Redis", data?.redis_status || "-"],
    ["Worker", data?.worker_status || "-"],
    ["yt-dlp", data?.ytdlp_version || "-"],
    ["ffmpeg", data?.ffmpeg_available ? "可用" : "-"]
  ];
  return (
    <AppShell admin>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => <Card key={label as string}><Metric label={label as string} value={String(value ?? "-")} /></Card>)}
      </div>
      <div className="mt-5 grid gap-4 lg:grid-cols-3">
        <Card>
          <h2 className="mb-3 font-semibold">最近 7 日</h2>
          <Rows items={data?.recent_daily.map((item) => [item.date, String(item.total_tasks)]) || []} />
        </Card>
        <Card>
          <h2 className="mb-3 font-semibold">热门平台</h2>
          <Rows items={data?.popular_platforms.map((item) => [item.platform, String(item.count)]) || []} />
        </Card>
        <Card>
          <h2 className="mb-3 font-semibold">失败原因</h2>
          <Rows items={data?.failure_reasons.map((item) => [item.reason, String(item.count)]) || []} />
        </Card>
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div><div className="text-sm text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}

function Rows({ items }: { items: string[][] }) {
  return <div className="space-y-2">{items.map(([a, b]) => <div key={a} className="flex justify-between text-sm"><span className="truncate">{a}</span><span>{b}</span></div>)}</div>;
}
