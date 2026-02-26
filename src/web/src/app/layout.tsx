import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Navbar } from "@/components/ui/Navbar";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { QuickAddModal } from "@/components/ui/QuickAddModal";
import { ForkEraModal } from "@/components/ui/ForkEraModal";
import { GlobalActivityBar } from "@/components/ui/GlobalActivityBar";
import { BackgroundJobsWidget } from "@/components/ui/BackgroundJobsWidget";
import { ChatSidebarWrapper } from "@/components/chat/ChatSidebarWrapper";
import { ArtifactPreviewOverlay } from "@/components/chat/ArtifactPreviewOverlay";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Showrunner Studio",
  description: "Visual studio for manga/manhwa creation with AI workflows",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning={true}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased h-screen flex flex-col overflow-hidden bg-gray-950`}
        suppressHydrationWarning={true}
      >
        <Navbar />
        <div className="flex flex-1 overflow-hidden pt-12">
          <main className="flex-1 overflow-hidden relative border-r border-gray-800">
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
            <ArtifactPreviewOverlay />
          </main>

          <ChatSidebarWrapper />
        </div>

        <CommandPalette />
        <QuickAddModal />
        <ForkEraModal />
        <GlobalActivityBar />
        <BackgroundJobsWidget />
        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            style: {
              background: "#1a1a2e",
              border: "1px solid #374151",
              color: "#e5e7eb",
            },
          }}
        />
      </body>
    </html>
  );
}
