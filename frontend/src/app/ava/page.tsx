"use client";

/**
 * Public Ava page: page chrome (title, intro, disclaimer) around the shared
 * AvaChat core. The same core renders inside the floating launcher panel on
 * every other public page (D-052).
 */
import { useI18n } from "@/lib/i18n";
import PublicShell from "@/components/public-shell";
import PageIntro from "@/components/page-intro";
import AvaChat from "@/components/ava-chat";

export default function PublicAvaPage() {
  const { t } = useI18n();
  return (
    <PublicShell>
      <main className="flex-1 w-full max-w-2xl mx-auto px-4 py-6 flex flex-col gap-4">
        <div>
          <h1 className="text-2xl font-bold">{t.mkAvaTitle}</h1>
          <p className="text-sm text-slate-500 mt-1">{t.mkAvaIntro}</p>
        </div>

        <PageIntro k="ava" title={t.avaIntroT} body={t.avaIntro} />

        <p className="text-xs bg-amber-50 text-amber-800 rounded-lg p-3">{t.mkAvaDisclaimer}</p>

        <AvaChat />
      </main>
    </PublicShell>
  );
}
