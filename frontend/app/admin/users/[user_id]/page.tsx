"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { Badge, Card, statusTone } from "@/components/ui";
import { api, fmtTime, formatBytes, type Task, type User } from "@/lib/api";

type FileItem = { id: number; filename: string; file_size: number; status: string; created_at: string };
type OperationLog = { id: number; action: string; detail?: string | null; ip?: string | null; created_at: string };
type UserDetail = {
  user: User;
  stats: { total_tasks: number; success_tasks: number; failed_tasks: number; active_tasks: number };
  recent_tasks: Task[];
  recent_files: FileItem[];
  operation_logs: OperationLog[];
};

const permissionFields: Array<keyof User> = [
  "daily_quota",
  "used_today",
  "max_concurrent_tasks",
  "max_file_size_mb",
  "max_duration_minutes",
  "file_retention_hours",
  "allow_video",
  "allow_audio",
  "allow_thumbnail",
  "allow_subtitle",
  "allow_playlist",
  "allow_batch",
  "allowed_platforms",
  "denied_platforms",
  "remark",
  "banned_reason",
  "banned_until"
];

export default function AdminUserDetailPage() {
  const params = useParams<{ user_id: string }>();
  const [detail, setDetail] = useState<UserDetail | null>(null);
  const [form, setForm] = useState<Partial<User>>({});
  const [error, setError] = useState("");

  async function load() {
    try {
      const next = await api<UserDetail>(`/admin/users/${params.user_id}`);
      setDetail(next);
      setForm(next.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载用户详情失败");
    }
  }

  useEffect(() => {
    load();
  }, [params.user_id]);

  async function save() {
    const body = Object.fromEntries(permissionFields.map((field) => [field, form[field]]));
    await api(`/admin/users/${params.user_id}`, { method: "PATCH", body: JSON.stringify({ ...body, role: form.role, status: form.status }) });
    await load();
  }

  async function action(path: string, body?: object) {
    await api(`/admin/users/${params.user_id}/${path}`, { method: "POST", body: body ? JSON.stringify(body) : undefined });
    await load();
  }

  const user = detail?.user;
  return (
    <AppShell admin>
      {error ? <p className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {user ? (
        <div className="grid gap-4">
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold">{user.username}</h1>
                <p className="text-sm text-slate-500">{user.email || "-"} · ID {user.id}</p>
              </div>
              <div className="flex gap-2">
                <button className="rounded-md bg-koyun-600 px-3 py-2 text-sm font-medium text-white" onClick={save}>保存</button>
                <button className="rounded-md border px-3 py-2 text-sm" onClick={() => action("apply-role-template")}>套用角色模板</button>
                <button className="rounded-md border px-3 py-2 text-sm" onClick={() => action("reset-quota")}>重置额度</button>
                <button className="rounded-md border px-3 py-2 text-sm" onClick={() => action("unban")}>解封</button>
              </div>
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card id="tasks">
              <h2 className="mb-3 font-semibold">基本信息</h2>
              <Field label="角色"><Select value={form.role} onChange={(value) => setForm({ ...form, role: value })} options={["user", "vip", "admin"]} /></Field>
              <Field label="状态"><Select value={form.status} onChange={(value) => setForm({ ...form, status: value })} options={["active", "readonly", "disabled", "banned"]} /></Field>
              <Info label="注册时间" value={fmtTime(user.created_at)} />
              <Info label="最近登录" value={fmtTime(user.last_login_at)} />
            </Card>

            <Card id="files">
              <h2 className="mb-3 font-semibold">下载额度</h2>
              <NumberField label="每日额度" field="daily_quota" form={form} setForm={setForm} />
              <NumberField label="今日已用" field="used_today" form={form} setForm={setForm} />
              <NumberField label="并发任务" field="max_concurrent_tasks" form={form} setForm={setForm} />
              <NumberField label="最大文件 MB" field="max_file_size_mb" form={form} setForm={setForm} />
              <NumberField label="最大时长分钟" field="max_duration_minutes" form={form} setForm={setForm} />
              <NumberField label="保留小时" field="file_retention_hours" form={form} setForm={setForm} />
            </Card>

            <Card>
              <h2 className="mb-3 font-semibold">风控设置</h2>
              {(["allow_video", "allow_audio", "allow_thumbnail", "allow_subtitle", "allow_playlist", "allow_batch"] as Array<keyof User>).map((field) => (
                <label key={field} className="mb-2 flex items-center justify-between text-sm">
                  {field}
                  <input type="checkbox" checked={Boolean(form[field])} onChange={(event) => setForm({ ...form, [field]: event.target.checked })} />
                </label>
              ))}
              <TextField label="允许平台" field="allowed_platforms" form={form} setForm={setForm} />
              <TextField label="禁止平台" field="denied_platforms" form={form} setForm={setForm} />
              <TextField label="备注" field="remark" form={form} setForm={setForm} />
              <TextField label="封禁原因" field="banned_reason" form={form} setForm={setForm} />
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-4">
            <Card><Metric label="总任务" value={detail.stats.total_tasks} /></Card>
            <Card><Metric label="成功" value={detail.stats.success_tasks} /></Card>
            <Card><Metric label="失败" value={detail.stats.failed_tasks} /></Card>
            <Card><Metric label="进行中" value={detail.stats.active_tasks} /></Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <h2 className="mb-3 font-semibold">最近任务</h2>
              <table className="w-full text-left text-sm">
                <tbody>{detail.recent_tasks.map((task) => <tr key={task.task_id} className="border-b"><td className="py-2">{task.domain}</td><td><Badge tone={statusTone(task.status)}>{task.status}</Badge></td><td>{fmtTime(task.created_at)}</td></tr>)}</tbody>
              </table>
            </Card>
            <Card>
              <h2 className="mb-3 font-semibold">最近文件</h2>
              <table className="w-full text-left text-sm">
                <tbody>{detail.recent_files.map((file) => <tr key={file.id} className="border-b"><td className="py-2">{file.filename}</td><td>{formatBytes(file.file_size)}</td><td>{file.status}</td></tr>)}</tbody>
              </table>
            </Card>
          </div>

          <Card>
            <h2 className="mb-3 font-semibold">管理员操作日志</h2>
            <table className="w-full text-left text-sm">
              <tbody>{detail.operation_logs.map((log) => <tr key={log.id} className="border-b"><td className="py-2">{log.action}</td><td>{log.detail || "-"}</td><td>{log.ip || "-"}</td><td>{fmtTime(log.created_at)}</td></tr>)}</tbody>
            </table>
          </Card>
        </div>
      ) : null}
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="mb-3 block text-sm"><span className="mb-1 block text-slate-500">{label}</span>{children}</label>;
}

function Select({ value, options, onChange }: { value?: string; options: string[]; onChange: (value: string) => void }) {
  return <select className="h-9 w-full rounded-md border px-3" value={value || ""} onChange={(event) => onChange(event.target.value)}>{options.map((option) => <option key={option}>{option}</option>)}</select>;
}

function NumberField({ label, field, form, setForm }: { label: string; field: keyof User; form: Partial<User>; setForm: (value: Partial<User>) => void }) {
  return <Field label={label}><input className="h-9 w-full rounded-md border px-3" type="number" value={Number(form[field] || 0)} onChange={(event) => setForm({ ...form, [field]: Number(event.target.value) })} /></Field>;
}

function TextField({ label, field, form, setForm }: { label: string; field: keyof User; form: Partial<User>; setForm: (value: Partial<User>) => void }) {
  return <Field label={label}><textarea className="min-h-16 w-full rounded-md border px-3 py-2" value={String(form[field] || "")} onChange={(event) => setForm({ ...form, [field]: event.target.value })} /></Field>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="mb-3 text-sm"><span className="block text-slate-500">{label}</span><span className="font-medium">{value}</span></div>;
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div><div className="text-sm text-slate-500">{label}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}
