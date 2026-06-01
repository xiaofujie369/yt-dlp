"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui";
import { api, type User } from "@/lib/api";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    api<User>("/auth/me").then(setUser);
  }, []);
  return (
    <AppShell>
      <Card className="max-w-2xl">
        <h1 className="mb-4 text-xl font-semibold">个人资料</h1>
        <dl className="grid gap-4 sm:grid-cols-2">
          <Info label="用户名" value={user?.username || "-"} />
          <Info label="邮箱" value={user?.email || "-"} />
          <Info label="可云用户ID" value={user?.koyun_user_id || "-"} />
          <Info label="角色" value={user?.role || "-"} />
        </dl>
      </Card>
    </AppShell>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return <div><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 text-sm font-medium">{value}</dd></div>;
}
