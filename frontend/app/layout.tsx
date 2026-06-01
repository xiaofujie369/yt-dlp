import "./globals.css";

export const metadata = {
  title: "可云视频下载工具",
  description: "Koyun yt-dlp download system"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
