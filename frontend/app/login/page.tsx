"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ShieldCheck } from "lucide-react";

import { API_BASE, setToken } from "@/lib/api";
import { LinkButton } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      setToken(token);
      router.replace("/");
    }
  }, [params, router]);

  return (
    <main className="grid min-h-screen place-items-center p-4">
      <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-koyun-600 text-white">
            <ShieldCheck className="h-5 w-5" />
          </span>
          <div>
            <h1 className="text-xl font-semibold">可云账户登录</h1>
            <p className="text-sm text-slate-600">登录后继续使用下载队列。</p>
          </div>
        </div>
        <LinkButton href={`${API_BASE}/api/auth/login`} className="w-full">
          使用可云账户登录
        </LinkButton>
      </section>
    </main>
  );
}
