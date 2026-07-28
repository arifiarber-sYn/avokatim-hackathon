import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gjenero shkresa dhe ankesa ligjore falas",
  description:
    "Gjenerator falas i shkresave ligjore për Kosovën: ankesa, kërkesa, " +
    "autorizime dhe parashtresa të tjera — të plotësuara me të dhënat e tua " +
    "dhe gati për shkarkim.",
  alternates: { canonical: "/dokumentet" },
};

export default function DokumentetLayout({ children }: { children: React.ReactNode }) {
  return children;
}
