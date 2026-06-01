"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Card } from "@/components/ui";
import { api, type Page, type User } from "@/lib/api";

export default function AdminUsersPage() {
  const [data, setData] = useState<Page<User> | null>(null);
  useEffect(() => {
    api<Page<User>>("/admin/users").then(setData);
  }, []);
  return (
    <AppShell admin>
      <Card>
        <h1 className="mb-4 text-xl font-semibold">用户管理</h1>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-slate-500"><tr><th className="py-3">用户</th><th>邮箱</th><th>角色</th><th>状态</th><th>额度</th></tr></thead>
            <tbody>{(data?.items || []).map((user) => (
              <tr key={user.id} className="border-b border-slate-100">
                <td className="py-3"><div className="font-medium">{user.username}</div><div className="text-xs text-slate-500">{user.koyun_user_id}</div></td>
                <td>{user.email || "-"}</td>
                <td><Badge tone={user.role === "admin" ? "blue" : user.role === "vip" ? "green" : "neutral"}>{user.role}</Badge></td>
                <td>{user.status}</td>
                <td>{user.used_today}/{user.daily_quota}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Card>
    </AppShell>
  );
}
