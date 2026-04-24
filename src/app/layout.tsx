import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AIMS Chat Interface — Automated Academic Reference System",
  description:
    "Get instant answers about AIMS Institutes — courses, admissions, fees, scholarships, campus life and more from our AI-powered academic assistant.",
  keywords: "AIMS, chatbot, college, admissions, MBA, MCA, BBA, BCA, M.Com, B.Com",
  openGraph: {
    title: "AIMS Chat Interface",
    description: "Your AI-powered academic assistant for AIMS Institutes.",
    type: "website",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-inter antialiased">
        {children}
      </body>
    </html>
  );
}
