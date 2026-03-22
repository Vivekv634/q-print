import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "next-themes";

export const metadata: Metadata = {
  title: "Q-PRINT",
  description: "Simplifying print chaos into manageable queues.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressContentEditableWarning={true}
      suppressHydrationWarning={true}
    >
      <body className={`antialiased dark:bg-[#222222]`}>
        <ThemeProvider
          defaultTheme="system"
          enableSystem={true}
          attribute={"class"}
          disableTransitionOnChange={false}
          themes={["light", "dark"]}
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
