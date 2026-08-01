"use client";

/**
 * Impressum — mandatory for the German host under § 5 DDG. Static German
 * text by design (the legal notice must be authoritative in German);
 * placeholders are filled at the DE public-launch gate
 * (docs/legal/DE-LAUNCH-GATE.md).
 */
import Link from "next/link";
import { useI18n } from "@/lib/i18n";
import { Card, LocaleSwitcher } from "@/components/ui";

export default function ImpressumPage() {
  const { t } = useI18n();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between gap-3">
          <Link href="/" className="text-lg font-bold text-indigo-700">
            {t.appName}
          </Link>
          <LocaleSwitcher />
        </div>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-8">
        <Card className="p-6 sm:p-8 space-y-5">
          <div>
            <h1 className="text-xl font-bold">Impressum</h1>
            <p className="text-xs text-slate-500 mt-1">Angaben gemäß § 5 DDG</p>
          </div>
          <section className="space-y-1 text-sm text-slate-600">
            <h2 className="font-semibold text-sm text-slate-800">Diensteanbieter</h2>
            <p>AvokatIM — Arbër Arifi</p>
            <p className="text-slate-400 italic">
              [Anschrift wird vor dem öffentlichen Start in Deutschland ergänzt]
            </p>
          </section>
          <section className="space-y-1 text-sm text-slate-600">
            <h2 className="font-semibold text-sm text-slate-800">Kontakt</h2>
            <p>
              E-Mail:{" "}
              <a href="mailto:info@avokatiim.ai" className="text-indigo-600 hover:underline">
                info@avokatiim.ai
              </a>
            </p>
            <p>
              Web:{" "}
              <a href="https://de.avokatiim.ai" className="text-indigo-600 hover:underline">
                de.avokatiim.ai
              </a>
            </p>
          </section>
          <section className="space-y-1 text-sm text-slate-600">
            <h2 className="font-semibold text-sm text-slate-800">
              Verantwortlich für den Inhalt
            </h2>
            <p>Arbër Arifi</p>
          </section>
          <section className="space-y-1 text-sm text-slate-600">
            <h2 className="font-semibold text-sm text-slate-800">Hinweis zum Dienst</h2>
            <p>
              AvokatIM ist eine Software-Plattform für Kanzleiverwaltung und die
              Vermittlung des Kontakts zwischen Bürgerinnen/Bürgern und zugelassenen
              Rechtsanwältinnen/Rechtsanwälten. AvokatIM erbringt selbst keine
              Rechtsdienstleistungen im Sinne des RDG. Die KI-Assistentin Ava liefert
              ausschließlich allgemeine Rechtsinformationen (Art. 50 EU-KI-Verordnung:
              Sie interagieren mit einem KI-System).
            </p>
          </section>
          <section className="space-y-1 text-sm text-slate-600">
            <h2 className="font-semibold text-sm text-slate-800">
              Streitbeilegung
            </h2>
            <p>
              Wir sind nicht bereit und nicht verpflichtet, an
              Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
              teilzunehmen.
            </p>
          </section>
          <div className="pt-2 border-t border-slate-100 flex gap-4 text-sm">
            <Link href="/kushtet" className="text-indigo-600 hover:underline">
              {t.termsOfService}
            </Link>
            <Link href="/privatesia" className="text-indigo-600 hover:underline">
              {t.privacyPolicy}
            </Link>
          </div>
        </Card>
      </main>
    </div>
  );
}
