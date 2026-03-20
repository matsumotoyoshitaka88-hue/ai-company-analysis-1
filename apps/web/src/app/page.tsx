"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CompanySearchInput } from "@/components/CompanySearchInput";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (companyCode: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/diagnosis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          /^\d{4,5}$/.test(companyCode)
            ? { company_code: companyCode }
            : { company_name: companyCode }
        ),
      });
      if (!res.ok) throw new Error("診断の開始に失敗しました");
      const data = await res.json();
      router.push(`/diagnosis/${data.job_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col items-center justify-center min-h-screen px-4">
      <div className="w-full max-w-2xl text-center">
        <h1 className="text-4xl font-bold mb-4 text-[var(--color-primary)]">
          AI企業診断
        </h1>
        <p className="text-lg text-[var(--color-text-secondary)] mb-12">
          企業名または証券コードを入力するだけで、
          <br />
          AIが公開データを分析し、総合診断レポートを無料で生成します。
        </p>

        <CompanySearchInput onSubmit={handleSubmit} disabled={loading} />

        {error && (
          <p className="mt-4 text-[var(--color-danger)]">{error}</p>
        )}

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="p-6 bg-[var(--color-surface)] rounded-xl shadow-sm">
            <h3 className="font-bold text-lg mb-2">財務診断</h3>
            <p className="text-[var(--color-text-secondary)] text-base">
              収益性・安全性・効率性を業界平均と比較しスコアリング
            </p>
          </div>
          <div className="p-6 bg-[var(--color-surface)] rounded-xl shadow-sm">
            <h3 className="font-bold text-lg mb-2">競合分析</h3>
            <p className="text-[var(--color-text-secondary)] text-base">
              同業他社3〜5社との比較でポジションを可視化
            </p>
          </div>
          <div className="p-6 bg-[var(--color-surface)] rounded-xl shadow-sm">
            <h3 className="font-bold text-lg mb-2">総合スコア</h3>
            <p className="text-[var(--color-text-secondary)] text-base">
              100点満点の信号機方式で経営状態を直感的に把握
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
