"use client";

import { Download, Files, LayoutDashboard, ListChecks, LogOut, Settings, Shield, UserRound, Users } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clsx } from "clsx";

const userNav = [
  { href: "/", label: "下载", icon: Download },
  { href: "/tasks", label: "任务", icon: ListChecks },
  { href: "/dashboard", label: "中心", icon: LayoutDashboard },
  { href: "/profile", label: "资料", icon: UserRound }
];

const adminNav = [
  { href: "/admin", label: "仪表盘", icon: LayoutDashboard },
  { href: "/admin/tasks", label: "任务", icon: ListChecks },
  { href: "/admin/users", label: "用户", icon: Users },
  { href: "/admin/files", label: "文件", icon: Files },
  { href: "/admin/domain-rules", label: "域名", icon: Shield },
  { href: "/admin/ip-blacklist", label: "IP", icon: Shield },
  { href: "/admin/settings", label: "设置", icon: Settings },
  { href: "/admin/stats", label: "统计", icon: Shield },
  { href: "/admin/logs", label: "日志", icon: Shield }
];

export function AppShell({ children, admin = false }: { children: React.ReactNode; admin?: boolean }) {
  const pathname = usePathname();
  const router = useRouter();
  const nav = admin ? adminNav : userNav;
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-60 border-r border-slate-200 bg-white px-3 py-4 md:block">
        <Link href={admin ? "/admin" : "/"} className="mb-6 flex items-center gap-2 px-2 text-lg font-semibold">
          <span className="grid h-8 w-8 place-items-center rounded-md bg-koyun-600 text-white">K</span>
          {admin ? "Koyun Download Admin" : "可云视频下载工具"}
        </Link>
        <nav className="space-y-1">
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                  pathname === item.href ? "bg-koyun-50 text-koyun-700" : "text-slate-600 hover:bg-slate-50"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="md:pl-60">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur">
          <div className="text-sm font-medium text-slate-700">{admin ? "管理后台" : "用户端"}</div>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md border border-slate-200 px-3 text-sm"
            onClick={() => {
              localStorage.removeItem("koyun_token");
              router.push("/login");
            }}
          >
            <LogOut className="h-4 w-4" />
            退出
          </button>
        </header>
        <div className="mx-auto max-w-7xl p-4 md:p-6">{children}</div>
      </main>
    </div>
  );
}
