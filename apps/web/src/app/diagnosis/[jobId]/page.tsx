"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { TrafficLight } from "@/components/diagnosis/TrafficLight";
import { SectionCard } from "@/components/diagnosis/SectionCard";
import { FinancialMetrics } from "@/components/diagnosis/FinancialMetrics";
import { LeadCaptureModal } from "@/components/diagnosis/LeadCaptureModal";
import type { DiagnosisStatus } from "@/lib/types";

const STEP_LABELS: Record<string, string> = {
  PENDING: "準備中...",
  COLLECTING: "公開データを収集中...",
  ANALYZING: "財務データを分析中...",
  GENERATING: "AIがレポートを生成中...",
  COMPLETED: "完了",
  FAILED: "エラーが発生しました",
};

export default function DiagnosisPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const [status, setStatus] = useState<DiagnosisStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showLeadModal, setShowLeadModal] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const res = await fetch(`/api/v1/diagnosis/${jobId}`);
        if (!res.ok) throw new Error("診断情報の取得に失敗しました");
        const data: DiagnosisStatus = await res.json();
        setStatus(data);

        if (data.status !== "COMPLETED" && data.status !== "FAILED") {
          setTimeout(poll, 2000);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "エラーが発生しました");
      }
    };

    poll();
  }, [jobId]);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-[var(--color-danger)] text-lg">{error}</p>
      </div>
    );
  }

  if (!status || status.status !== "COMPLETED") {
    const progressMsg = status?.progress?.message || STEP_LABELS[status?.status ?? "PENDING"];
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="w-full max-w-md">
          <h2 className="text-2xl font-bold text-center mb-8">企業診断中</h2>
          <div className="bg-white rounded-xl shadow-sm p-8">
            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-[var(--color-primary)] h-3 rounded-full transition-all duration-500"
                  style={{ width: `${status?.progress?.percent ?? 5}%` }}
                />
              </div>
            </div>
            <p className="text-center text-[var(--color-text-secondary)]">
              {progressMsg}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const report = status.report;
  if (!report) return null;

  const { overall_score: overallScore, sections, company } = report;

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      {/* Company Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{company.name}</h1>
        <p className="text-[var(--color-text-secondary)]">
          {company.industry} | コード: {company.code}
        </p>
      </div>

      {/* Overall Score Banner */}
      <div className="bg-white rounded-2xl shadow-sm p-8 mb-8 text-center">
        <h2 className="text-xl font-bold mb-6">総合診断結果</h2>
        <div className="flex items-center justify-center gap-6 mb-4">
          <TrafficLight color={overallScore.traffic_light} size="lg" />
          <span className="text-6xl font-bold">
            {overallScore.score}
            <span className="text-2xl text-[var(--color-text-secondary)]">/100</span>
          </span>
        </div>
        <p className="text-lg text-[var(--color-text-secondary)]">
          {overallScore.summary_text}
        </p>
      </div>

      {/* Section Scores Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { title: "収益性", data: sections.financial_diagnosis.profitability },
          { title: "安全性", data: sections.financial_diagnosis.safety },
          { title: "競合", data: sections.competitive_position },
          { title: "DX", data: sections.dx_maturity },
        ].map(({ title, data }) => (
          <div key={title} className="bg-white rounded-xl shadow-sm p-4 text-center">
            <TrafficLight color={data.traffic_light} size="md" />
            <p className="mt-2 font-bold text-2xl">{data.score}</p>
            <p className="text-sm text-[var(--color-text-secondary)]">{title}</p>
          </div>
        ))}
      </div>

      {/* Diagnosis Sections */}
      <div className="space-y-4">
        <SectionCard title="エグゼクティブサマリー" defaultOpen>
          <div className="prose max-w-none whitespace-pre-wrap">
            {sections.executive_summary.content}
          </div>
        </SectionCard>

        <SectionCard title="財務診断">
          <FinancialMetrics
            title="収益性"
            data={sections.financial_diagnosis.profitability}
          />
          <FinancialMetrics
            title="安全性"
            data={sections.financial_diagnosis.safety}
          />
          <FinancialMetrics
            title="効率性"
            data={sections.financial_diagnosis.efficiency}
          />
          <div className="mt-6 prose max-w-none whitespace-pre-wrap">
            {sections.financial_diagnosis.narrative}
          </div>
        </SectionCard>

        <SectionCard title="競合ポジション">
          <div className="prose max-w-none whitespace-pre-wrap">
            {sections.competitive_position.narrative}
          </div>
        </SectionCard>

        <SectionCard title="DX成熟度">
          <div className="prose max-w-none whitespace-pre-wrap">
            {sections.dx_maturity.narrative}
          </div>
        </SectionCard>

        <SectionCard title="リスク・機会分析">
          <div className="prose max-w-none whitespace-pre-wrap">
            {sections.risk_opportunity.narrative}
          </div>
        </SectionCard>
      </div>

      {/* PDF Download + Lead Capture */}
      <div className="mt-8 text-center">
        <button
          onClick={() => setShowLeadModal(true)}
          className="px-8 py-4 bg-[var(--color-surface)] border-2 border-[var(--color-primary)]
                     text-[var(--color-primary)] font-bold rounded-xl hover:bg-blue-50
                     transition-colors text-lg"
        >
          診断レポートをPDFでダウンロード
        </button>
      </div>

      {/* Data Sources */}
      {report.data_sources.length > 0 && (
        <div className="mt-8 text-sm text-[var(--color-text-secondary)]">
          <p className="font-medium mb-1">データソース:</p>
          <ul className="list-disc list-inside">
            {report.data_sources.map((src, i) => (
              <li key={i}>{src}</li>
            ))}
          </ul>
        </div>
      )}

      {/* CTA Section */}
      <div className="mt-12 bg-[var(--color-primary)] text-white rounded-2xl p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">
          診断結果を踏まえた改善をご検討ですか？
        </h2>
        <p className="mb-6 text-blue-100">
          専門家による詳細分析と改善提案をご提供します
        </p>
        <button className="px-8 py-4 bg-white text-[var(--color-primary)] font-bold rounded-xl hover:bg-blue-50 transition-colors text-lg">
          詳しく相談する
        </button>
      </div>

      {/* Lead Capture Modal */}
      {showLeadModal && (
        <LeadCaptureModal
          jobId={jobId}
          companyCode={company.code}
          onClose={() => setShowLeadModal(false)}
        />
      )}
    </main>
  );
}
