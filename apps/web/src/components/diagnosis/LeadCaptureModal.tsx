"use client";

import { useState } from "react";

interface Props {
  jobId: string;
  companyCode: string;
  onClose: () => void;
}

export function LeadCaptureModal({ jobId, companyCode, onClose }: Props) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          name: name || undefined,
          company_code: companyCode,
          job_id: jobId,
        }),
      });

      if (!res.ok) throw new Error("送信に失敗しました");
      const data = await res.json();

      // Trigger PDF download
      window.open(data.pdf_download_url, "_blank");
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "エラーが発生しました");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8">
        <h3 className="text-xl font-bold mb-2">レポートをPDFで受け取る</h3>
        <p className="text-[var(--color-text-secondary)] mb-6">
          メールアドレスをご登録いただくと、診断レポートのPDFをダウンロードできます。
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">
              メールアドレス <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="email@example.com"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg
                         focus:border-[var(--color-primary-light)] focus:outline-none"
            />
          </div>
          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">
              お名前（任意）
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="山田 太郎"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg
                         focus:border-[var(--color-primary-light)] focus:outline-none"
            />
          </div>

          {error && (
            <p className="mb-4 text-[var(--color-danger)] text-sm">{error}</p>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg
                         hover:bg-gray-50 transition-colors font-medium"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={submitting || !email}
              className="flex-1 px-4 py-3 bg-[var(--color-primary)] text-white
                         rounded-lg hover:bg-[var(--color-primary-light)]
                         disabled:opacity-50 transition-colors font-bold"
            >
              {submitting ? "送信中..." : "PDFをダウンロード"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
