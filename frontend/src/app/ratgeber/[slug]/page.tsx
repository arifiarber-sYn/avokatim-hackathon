import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import PublicShell from "@/components/public-shell";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";
import { RATGEBER_ARTICLES, ratgeberBySlug } from "@/lib/ratgeber";

interface Props {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return RATGEBER_ARTICLES.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const article = ratgeberBySlug(slug);
  if (!article) return {};
  const base = COUNTRY_BASE_URL[await serverCountry()];
  return {
    title: article.title,
    description: article.description,
    alternates: { canonical: `${base}/ratgeber/${article.slug}` },
  };
}

export default async function RatgeberArticlePage({ params }: Props) {
  const { slug } = await params;
  const article = ratgeberBySlug(slug);
  if (!article) notFound();
  const base = COUNTRY_BASE_URL[await serverCountry()];

  // Article JSON-LD so search engines and answer engines can cite the guide
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    dateModified: article.updated,
    inLanguage: "de",
    mainEntityOfPage: `${base}/ratgeber/${article.slug}`,
    author: { "@type": "Organization", name: "AvokatIM" },
  };

  return (
    <PublicShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <main className="max-w-2xl w-full mx-auto px-4 py-10 space-y-8">
        <div className="space-y-3">
          <Link href="/ratgeber" className="text-sm text-indigo-600 hover:underline">
            ← Alle Ratgeber
          </Link>
          <div>
            <span className="inline-block text-[11px] font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 rounded-full px-2.5 py-0.5 mb-2">
              {article.area}
            </span>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900 leading-tight">
              {article.title}
            </h1>
          </div>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-amber-700 mb-2">
            Das Wichtigste in Kürze
          </p>
          <ul className="space-y-1.5">
            {article.facts.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-700">
                <span className="text-amber-500 shrink-0">•</span>
                {f}
              </li>
            ))}
          </ul>
        </div>

        <article className="space-y-6">
          {article.sections.map((s, i) => (
            <section key={i} className="space-y-2.5">
              <h2 className="text-lg font-bold text-slate-900">{s.h}</h2>
              {s.p.map((para, j) => (
                <p key={j} className="text-[15px] text-slate-700 leading-relaxed">
                  {para}
                </p>
              ))}
            </section>
          ))}
        </article>

        {/* RDG-safe disclaimer + conversion path */}
        <div className="border-t border-slate-200 pt-6 space-y-4">
          <p className="text-xs text-slate-400">
            Dieser Beitrag informiert allgemein über die Rechtslage (Stand:{" "}
            {new Date(article.updated).toLocaleDateString("de-DE")}) und ersetzt
            keine Rechtsberatung im Einzelfall.
          </p>
          <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 space-y-2">
            <p className="font-semibold text-slate-900 text-sm">
              Was bedeutet das für Ihren Fall?
            </p>
            <p className="text-sm text-slate-600">
              Fragen Sie Ava kostenlos — oder schildern Sie Ihren Fall und
              erhalten Sie Rückmeldungen von Anwälten.
            </p>
            <div className="flex gap-3 pt-1">
              <Link
                href="/ava"
                className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-700"
              >
                Ava fragen
              </Link>
              <Link
                href="/posto-rastin"
                className="rounded-lg border border-indigo-300 text-indigo-700 px-4 py-2 text-sm font-medium hover:bg-indigo-100"
              >
                Fall schildern
              </Link>
            </div>
          </div>
        </div>
      </main>
    </PublicShell>
  );
}
