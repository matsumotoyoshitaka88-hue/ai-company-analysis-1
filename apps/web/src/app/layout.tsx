import type { Metadata } from "next";
import { Noto_Sans_JP } from "next/font/google";
import "./globals.css";

const notoSansJP = Noto_Sans_JP({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI企業診断サービス",
  description:
    "企業名を入力するだけで、AIが公開データを自動収集・分析し、総合診断レポートを無料で生成します。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className={notoSansJP.className}>
      <body className="min-h-screen bg-[var(--color-bg)]">{children}</body>
    </html>
  );
}
