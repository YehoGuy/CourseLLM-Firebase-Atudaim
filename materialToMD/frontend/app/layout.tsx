import type { Metadata } from "next";
import { Inter } from "next/font/google";
// import "./globals.css"; // Uncomment this line if you have a globals.css file

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Material to Markdown",
  description: "Convert files to Markdown",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}