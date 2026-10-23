import type { Metadata } from "next";
import Link from "next/link";
import PublicShell from "@/components/public-shell";
import { COUNTRY_BASE_URL, serverCountry } from "@/lib/seo";
import { UDHEZUES_ARTICLES } from "@/lib/udhezues";

// Curated Albanian legal guides for Kosovo (D-048). Content is static
// Albanian — the page targets the XK host; per-host canonical keeps SEO clean.
export async function generateMetadata(): Promise<Metadata> {
  const base = COUNTRY_BASE_URL[await serverCountry()];
  return {
    title: "Udhëzues juridikë: të drejtat tuaja të shpjeguara thjesht",
    description:
      "Largimi nga puna, urdhri përmbarimor, qiraja, trashëgimia, divorci: pyetjet " +
      "juridike më të shpeshta në Kosovë të shpjeguara thjesht — me afate, ligje dhe hapat e radhës.",
    alternates: { canonical: `${base}/udhezues` },
  };
}

export default function UdhezuesIndexPage() {
  return (
    <PublicShell wide>
      <main className="max-w-5xl w-full mx-auto px-4 py-10 space-y-8">
        <div className="space-y-3 max-w-2xl">
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
            Udhëzues juridikë
          </h1>
          <p className="text-slate-600">
            Pyetjet juridike më të shpeshta të shpjeguara thjesht — me afatet dhe
            ligjet më të rëndësishme të Kosovës. Informacion i përgjithshëm, jo
            këshillë juridike për rastin tuaj.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          {UDHEZUES_ARTICLES.map((a) => (
            <Link
              key={a.slug}
              href={`/udhezues/${a.slug}`}
              className="block bg-white rounded-2xl border border-slate-200 p-5 space-y-2 hover:border-indigo-400 hover:shadow-sm transition"
            >
              <span className="inline-block text-[11px] font-semibold uppercase tracking-wider text-indigo-600 bg-indigo-50 rounded-full px-2.5 py-0.5">
                {a.area}
              </span>
              <h2 className="font-bold text-slate-900 leading-snug">{a.title}</h2>
              <p className="text-sm text-slate-500 leading-relaxed">{a.description}</p>
            </Link>
          ))}
        </div>

        <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 text-center space-y-2">
          <p className="font-semibold text-slate-900">
            Pyetja juaj nuk është këtu?
          </p>
          <p className="text-sm text-slate-600">
            Pyeteni Ava-n — asistentja jonë e AI-së përgjigjet falas në bazë të
            ligjeve të Kosovës — ose përshkruajeni rastin tuaj dhe merrni
            përgjigje nga avokatët.
          </p>
          <div className="flex items-center justify-center gap-3 pt-1">
            <Link
              href="/ava"
              className="rounded-lg bg-indigo-600 text-white px-5 py-2 text-sm font-semibold hover:bg-indigo-700"
            >
              Pyete Ava-n
            </Link>
            <Link
              href="/posto-rastin"
              className="rounded-lg border border-indigo-300 text-indigo-700 px-5 py-2 text-sm font-medium hover:bg-indigo-100"
            >
              Përshkruaje rastin
            </Link>
          </div>
        </div>
      </main>
    </PublicShell>
  );
}
