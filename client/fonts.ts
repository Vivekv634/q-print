import { JetBrains_Mono, Inter, Space_Grotesk } from "next/font/google";

export const space_grotesk = Space_Grotesk({
  weight: ["400", "500", "700"],
  preload: true,
  style: ["normal"],
  subsets: ["latin"],
  adjustFontFallback: true,
});

export const inter = Inter({
  weight: ["400", "500", "600"],
  preload: true,
  style: ["normal"],
  subsets: ["latin"],
  adjustFontFallback: true,
});

export const jetbrains_mono = JetBrains_Mono({
  weight: ["400", "500", "600"],
  preload: true,
  style: ["normal"],
  subsets: ["latin"],
  adjustFontFallback: true,
});
