"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card } from "@/components/ui";
import { api, fmtTime, type Page, type User } from "@/lib/api";

export default function AdminUsersPage() {
  const [data, setData] = useState<Page<User> | null>(null);
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  async function load() {
    const params = new URLSearchParams();
    if (role) params.set("role", role);
    if (status) params.set("status", status);
    if (q) params.set("q", q);
    try {
      setError("");
      setData(await api<Page<User>>(`/admin/users?${params}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载用户失败");
    }
  }

  useEffect(() => {
    load();
  }, [role, status]);

  async function run(user: User, action: () => Promise<unknown>) {
    setBusyId(user.id);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setBusyId(null);
    }
  }

  function patchRole(user: User, nextRole: string) {
    return run(user, () => api(`/admin/users/${user.id}`, { method: "PATCH", body: JSON.stringify({ role: nextRole }) }));
  }

  return (
    <AppShell admin>
      <Card>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold">用户管理</h1>
            <p className="mt-1 text-sm text-slate-500">管理用户角色、状态、额度和下载权限。</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input className="h-9 rounded-md border px-3 text-sm" placeholder="邮箱 / 用户名" value={q} onChange={(event) => setQ(event.target.value)} onBlur={load} />
            <select className="h-9 rounded-md border px-3 text-sm" value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="">全部角色</option>
              <option value="user">user</option>
              <option value="vip">vip</option>
              <option value="admin">admin</option>
            </select>
            <select className="h-9 rounded-md border px-3 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
              <option value="">全部状态</option>
              <option value="active">active</option>
              <option value="readonly">readonly</option>
              <option value="disabled">disabled</option>
              <option value="banned">banned</option>
            </select>
          </div>
        </div>
        {error ? <p className="mb-3 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-slate-500">
              <tr>
                <th className="py-3">ID</th>
                <th>邮箱</th>
                <th>用户名</th>
                <th>角色</th>
                <th>状态</th>
                <th>今日额度</th>
                <th>并发</th>
                <th>最大文件</th>
                <th>创建时间</th>
                <th>最近登录</th>
                <th className="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((user) => (
                <tr key={user.id} className="border-b border-slate-100">
                  <td className="py-3">{user.id}</td>
                  <td>{user.email || "-"}</td>
                  <td>{user.username}</td>
                  <td><Badge tone={user.role === "admin" ? "blue" : user.role === "vip" ? "green" : "neutral"}>{user.role}</Badge></td>
                  <td><Badge tone={user.status === "active" ? "green" : user.status === "readonly" ? "yellow" : "red"}>{user.status}</Badge></td>
                  <td>{user.used_today}/{user.daily_quota}</td>
                  <td>{user.max_concurrent_tasks}</td>
                  <td>{user.max_file_size_mb} MB</td>
                  <td>{fmtTime(user.created_at)}</td>
                  <td>{fmtTime(user.last_login_at)}</td>
                  <td>
                    <div className="flex min-w-[420px] justify-end gap-2">
                      <Action href={`/admin/users/${user.id}`}>编辑</Action>
                      <Action href={`/admin/users/${user.id}#tasks`}>查看任务</Action>
                      <Action href={`/admin/users/${user.id}#files`}>查看文件</Action>
                      <Action onClick={() => run(user, () => api(`/admin/users/${user.id}/reset-quota`, { method: "POST" }))} disabled={busyId === user.id}>重置额度</Action>
                      <Action onClick={() => patchRole(user, "vip")} disabled={busyId === user.id}>设为 VIP</Action>
                      <Action onClick={() => patchRole(user, "admin")} disabled={busyId === user.id}>设为管理员</Action>
                      <Action onClick={() => patchRole(user, "user")} disabled={busyId === user.id}>降为普通</Action>
                      {user.status === "banned" || user.status === "disabled" ? (
                        <Action onClick={() => run(user, () => api(`/admin/users/${user.id}/enable`, { method: "POST" }))} disabled={busyId === user.id}>解封</Action>
                      ) : (
                        <Action onClick={() => run(user, () => api(`/admin/users/${user.id}/disable`, { method: "POST" }))} disabled={busyId === user.id}>禁用</Action>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}

function Action({ children, href, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode; href?: string }) {
  const className = "inline-flex h-8 items-center rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60";
  if (href) return <Link href={href} className={className}>{children}</Link>;
  return <button className={className} {...props}>{children}</button>;
}
