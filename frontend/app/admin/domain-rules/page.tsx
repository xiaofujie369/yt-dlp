"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Badge, Button, Card } from "@/components/ui";
import { api } from "@/lib/api";

type DomainRule = { id: number; domain: string; rule_type: string; status: string; remark?: string };

export default function DomainRulesPage() {
  const [rules, setRules] = useState<DomainRule[]>([]);
  const [domain, setDomain] = useState("");
  const [ruleType, setRuleType] = useState("allow");
  const load = () => api<DomainRule[]>("/admin/domain-rules").then(setRules);
  useEffect(() => { load(); }, []);
  async function add() {
    await api("/admin/domain-rules", { method: "POST", body: JSON.stringify({ domain, rule_type: ruleType, status: "active" }) });
    setDomain("");
    load();
  }
  return (
    <AppShell admin>
      <Card>
        <div className="mb-4 flex flex-wrap items-end gap-2">
          <div><label className="text-xs text-slate-500">域名</label><input className="block h-9 rounded-md border px-3 text-sm" value={domain} onChange={(event) => setDomain(event.target.value)} /></div>
          <select className="h-9 rounded-md border px-3 text-sm" value={ruleType} onChange={(event) => setRuleType(event.target.value)}><option value="allow">白名单</option><option value="deny">黑名单</option></select>
          <Button onClick={add} disabled={!domain}>新增</Button>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="border-b text-slate-500"><tr><th className="py-3">域名</th><th>类型</th><th>状态</th><th>备注</th></tr></thead>
          <tbody>{rules.map((rule) => <tr key={rule.id} className="border-b border-slate-100"><td className="py-3">{rule.domain}</td><td><Badge tone={rule.rule_type === "allow" ? "green" : "red"}>{rule.rule_type}</Badge></td><td>{rule.status}</td><td>{rule.remark || "-"}</td></tr>)}</tbody>
        </table>
      </Card>
    </AppShell>
  );
}
