"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Button, Card } from "@/components/ui";
import { api, fmtTime } from "@/lib/api";

type RecordItem = { id: number; ip?: string; cidr?: string; reason?: string; expired_at?: string; status: string };

export default function IPBlacklistPage() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [ip, setIp] = useState("");
  const [cidr, setCidr] = useState("");
  const [reason, setReason] = useState("");
  const load = () => api<RecordItem[]>("/admin/ip-blacklist").then(setRecords);
  useEffect(() => { load(); }, []);
  async function add() {
    await api("/admin/ip-blacklist", { method: "POST", body: JSON.stringify({ ip: ip || null, cidr: cidr || null, reason, status: "active" }) });
    setIp("");
    setCidr("");
    setReason("");
    load();
  }
  return (
    <AppShell admin>
      <Card>
        <div className="mb-4 grid gap-2 md:grid-cols-[1fr_1fr_1fr_auto]">
          <input className="h-9 rounded-md border px-3 text-sm" placeholder="IP" value={ip} onChange={(event) => setIp(event.target.value)} />
          <input className="h-9 rounded-md border px-3 text-sm" placeholder="CIDR" value={cidr} onChange={(event) => setCidr(event.target.value)} />
          <input className="h-9 rounded-md border px-3 text-sm" placeholder="备注" value={reason} onChange={(event) => setReason(event.target.value)} />
          <Button onClick={add} disabled={!ip && !cidr}>新增</Button>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b text-slate-500"><tr><th className="py-3">IP</th><th>CIDR</th><th>原因</th><th>过期</th><th>状态</th></tr></thead>
          <tbody>{records.map((record) => <tr key={record.id} className="border-b border-slate-100"><td className="py-3">{record.ip || "-"}</td><td>{record.cidr || "-"}</td><td>{record.reason || "-"}</td><td>{fmtTime(record.expired_at)}</td><td>{record.status}</td></tr>)}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
