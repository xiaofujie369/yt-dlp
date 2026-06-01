"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Download, Headphones, ImageDown, Subtitles } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card } from "@/components/ui";
import { api, type Task } from "@/lib/api";

const taskTypes = [
  { value: "video", label: "MP4 视频", icon: Download },
  { value: "audio", label: "MP3 音频", icon: Headphones },
  { value: "thumbnail", label: "仅封面", icon: ImageDown },
  { value: "subtitle", label: "仅字幕", icon: Subtitles }
];

export default function HomePage() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [taskType, setTaskType] = useState("video");
  const [quality, setQuality] = useState("bv*+ba/b");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    setLoading(true);
    setError("");
    try {
      const created = await api<Task>("/tasks", {
        method: "POST",
        body: JSON.stringify({ url, task_type: taskType, quality })
      });
      router.push(`/tasks/${created.task_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <Card className="space-y-5">
          <div>
            <h1 className="text-2xl font-semibold">可云视频下载工具</h1>
            <p className="mt-2 text-sm text-slate-600">仅限可云账户登录使用，支持视频下载、音频提取、安全排队处理。</p>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">视频链接</label>
            <input
              className="h-11 w-full rounded-md border border-slate-300 px-3 outline-none focus:border-koyun-600"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-4">
            {taskTypes.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.value}
                  className={`rounded-md border p-3 text-left ${taskType === item.value ? "border-koyun-600 bg-koyun-50" : "border-slate-200 bg-white"}`}
                  onClick={() => setTaskType(item.value)}
                >
                  <Icon className="mb-3 h-5 w-5 text-koyun-700" />
                  <span className="text-sm font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
          <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
            <select className="h-10 rounded-md border border-slate-300 px-3" value={quality} onChange={(event) => setQuality(event.target.value)}>
              <option value="bv*+ba/b">最佳视频</option>
              <option value="best">最佳兼容</option>
              <option value="ba">最佳音频</option>
            </select>
            <Button onClick={submit} disabled={loading || !url}>
              {loading ? "提交中" : "提交任务"}
            </Button>
          </div>
          <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">请仅下载你拥有权利或已获得授权的内容，禁止用于侵犯版权或违反平台规则的用途。</p>
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
        </Card>
        <Card className="space-y-4">
          <h2 className="text-base font-semibold">处理状态</h2>
          <div className="grid gap-2">
            {["queued", "downloading", "merging", "transcoding", "completed", "failed", "cancelled"].map((status) => (
              <div key={status} className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2">
                <span className="text-sm text-slate-600">{status}</span>
                <Badge tone={status === "completed" ? "green" : status === "failed" ? "red" : "blue"}>任务状态</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
