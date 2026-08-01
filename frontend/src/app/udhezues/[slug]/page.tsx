import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import PublicShell from "@/components/public-shell";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";
import { UDHEZUES_ARTICLES, udhezuesBySlug } from "@/lib/udhezues";

interface Props {
  params: Promise<{ slug: string }>;
}

export function generateStaticParams() {
  return UDHEZUES_ARTICLES.map((a) => ({ slug: a.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const article = udhezuesBySlug(slug);
  if (!article) return {};
  const base = COUNTRY_BASE_URL[await serverCountry()];
  return {
    title: article.title,
    description: article.description,
    alternates: { canonical: `${base}/udhezues/${article.slug}` },
  };
}

export default async function UdhezuesArticlePage({ params }: Props) {
  const { slug } = await params;
  const article = udhezuesBySlug(slug);
  if (!article) notFound();
  const base = COUNTRY_BASE_URL[await serverCountry()];

  // Article JSON-LD so search engines and answer engines can cite the guide
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.description,
    dateModified: article.updated,
    inLanguage: "sq",
    mainEntityOfPage: `${base}/udhezues/${article.slug}`,
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
          <Link href="/udhezues" className="text-sm text-indigo-600 hover:underline">
            ← Të gjithë udhëzuesit
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
            Më e rëndësishmja shkurt
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

        {/* Disclaimer + conversion path */}
        <div className="border-t border-slate-200 pt-6 space-y-4">
          <p className="text-xs text-slate-400">
            Ky shkrim informon në mënyrë të përgjithshme për gjendjen ligjore
            (përditësuar më {new Date(article.updated).toLocaleDateString("sq-AL")})
            dhe nuk zëvendëson këshillën juridike për rastin tuaj konkret.
          </p>
          <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-5 space-y-2">
            <p className="font-semibold text-slate-900 text-sm">
              Çfarë do të thotë kjo për rastin tuaj?
            </p>
            <p className="text-sm text-slate-600">
              Pyeteni Ava-n falas — ose përshkruajeni rastin tuaj dhe merrni
              përgjigje nga avokatët.
            </p>
            <div className="flex gap-3 pt-1">
              <Link
                href="/ava"
                className="rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-semibold hover:bg-indigo-700"
              >
                Pyete Ava-n
              </Link>
              <Link
                href="/posto-rastin"
                className="rounded-lg border border-indigo-300 text-indigo-700 px-4 py-2 text-sm font-medium hover:bg-indigo-100"
              >
                Përshkruaje rastin
              </Link>
            </div>
          </div>
        </div>
      </main>
    </PublicShell>
  );
}
