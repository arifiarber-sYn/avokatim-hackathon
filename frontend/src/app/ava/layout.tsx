import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ava — pyet falas për ligjet e Kosovës",
  description:
    "Asistentja ligjore AI me tekstet e plota të ligjeve të Kosovës në 5 gjuhë " +
    "zyrtare. Përgjigje me citim të neneve konkrete, me tekst ose me zë — " +
    "falas, pa llogari. Për këshillë ligjore të lidhemi me avokat të verifikuar.",
  alternates: { canonical: "/ava" },
};

export default function AvaLayout({ children }: { children: React.ReactNode }) {
  return children;
}
