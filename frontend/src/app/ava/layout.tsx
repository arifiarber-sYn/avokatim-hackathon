import type { Metadata } from "next";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Ava — Rechtsfragen zu deutschen Gesetzen kostenlos stellen"
      : "Ava — pyet falas për ligjet e Kosovës",
    description: de
      ? "Die KI-Rechtsassistentin mit deutschen Bundesgesetzen. Antworten mit " +
        "Zitat der konkreten Paragrafen, per Text oder Sprache — kostenlos, ohne " +
        "Konto. Rechtsinformation, keine Rechtsberatung; für Beratung vermitteln " +
        "wir geprüfte Anwälte."
      : "Asistentja ligjore AI me tekstet e plota të ligjeve të Kosovës në 5 gjuhë " +
        "zyrtare. Përgjigje me citim të neneve konkrete, me tekst ose me zë — " +
        "falas, pa llogari. Për këshillë ligjore të lidhemi me avokat të verifikuar.",
    alternates: { canonical: "/ava" },
  };
}

export default function AvaLayout({ children }: { children: React.ReactNode }) {
  return children;
}
