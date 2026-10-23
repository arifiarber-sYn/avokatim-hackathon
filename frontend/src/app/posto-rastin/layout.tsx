import type { Metadata } from "next";
import { serverCountry } from "@/lib/seo";

export async function generateMetadata(): Promise<Metadata> {
  const de = (await serverCountry()) === "DE";
  return {
    title: de
      ? "Fall einstellen — Anwälte melden sich bei Ihnen"
      : "Posto rastin tënd — avokatët të kontaktojnë ty",
    description: de
      ? "Beschreiben Sie Ihren Rechtsfall kostenlos, und geprüfte Anwälte aus " +
        "Ihrem Rechtsgebiet und Ihrer Stadt melden sich direkt bei Ihnen. Kein " +
        "Herumtelefonieren — Sie entscheiden, mit wem Sie weitermachen."
      : "Përshkruaje rastin tënd ligjor falas dhe avokatët e verifikuar që " +
        "mbulojnë fushën dhe qytetin tënd të kontaktojnë direkt. Pa telefonata, " +
        "pa kërkim — ti zgjedh me kë vazhdon.",
    alternates: { canonical: "/posto-rastin" },
  };
}

export default function PostoRastinLayout({ children }: { children: React.ReactNode }) {
  return children;
}
