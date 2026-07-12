"use client";

/**
 * The citizen's account page: profile (name, phone, language), password
 * change, quick links to their things, and a visible sign-out — the "place"
 * a citizen has in the system.
 */
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n";
import { Locale, dictionaries } from "@/lib/dictionaries";
import {
  CitizenInfo,
  citizenApi,
  citizenGet,
  citizenPost,
  getCitizenToken,
  setCitizenToken,
} from "@/lib/citizen";
import { Button, Card, ErrorNote, Input, Label, Select, Spinner } from "@/components/ui";
import PublicShell from "@/components/public-shell";
import { IconArrowRight, IconCalendar, IconCheck, IconDoc, IconShield } from "@/components/icons";

const LOCALE_NAMES: Record<string, string> = {
  sq: "Shqip",
  en: "English",
  zh: "中文",
  sr: "Srpski",
  tr: "Türkçe",
  bs: "Bosanski",
};

export default function CitizenAccountPage() {
  const { t, setLocale } = useI18n();
  const router = useRouter();
  const [citizen, setCitizen] = useState<CitizenInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const [profile, setProfile] = useState({ full_name: "", phone: "", locale: "sq" });
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileError, setProfileError] = useState("");

  const [pw, setPw] = useState({ current: "", next: "" });
  const [pwBusy, setPwBusy] = useState(false);
  const [pwChanged, setPwChanged] = useState(false);
  const [pwError, setPwError] = useState("");

  useEffect(() => {
    if (!getCitizenToken()) {
      router.replace("/kycu");
      return;
    }
    citizenGet<CitizenInfo>("/citizen/me")
      .then((c) => {
        setCitizen(c);
        setProfile({ full_name: c.full_name, phone: c.phone || "", locale: c.locale });
        setLoading(false);
      })
      .catch(() => {
        setCitizenToken(null);
        router.replace("/kycu");
      });
  }, [router]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileBusy(true);
    setProfileError("");
    setProfileSaved(false);
    try {
      const updated = await citizenApi<CitizenInfo>("/citizen/me", {
        method: "PATCH",
        body: JSON.stringify({
          full_name: profile.full_name,
          phone: profile.phone,
          locale: profile.locale,
        }),
      });
      setCitizen(updated);
      if (dictionaries[profile.locale as Locale]) setLocale(profile.locale as Locale);
      setProfileSaved(true);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : t.error);
    } finally {
      setProfileBusy(false);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwBusy(true);
    setPwError("");
    setPwChanged(false);
    try {
      await citizenPost("/citizen/change-password", {
        current_password: pw.current,
        new_password: pw.next,
      });
      setPw({ current: "", next: "" });
      setPwChanged(true);
    } catch (err) {
      setPwError(err instanceof Error ? err.message : t.error);
    } finally {
      setPwBusy(false);
    }
  }

  function logout() {
    setCitizenToken(null);
    router.push("/");
  }

  return (
    <PublicShell>
      <main className="w-full max-w-xl mx-auto px-4 py-8 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">{t.acctTitle}</h1>
          <Button variant="secondary" onClick={logout}>
            {t.acctLogout}
          </Button>
        </div>

        {loading || !citizen ? (
          <Spinner />
        ) : (
          <>
            {/* Quick links: the citizen's things */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { href: "/rasti-im", label: t.mkMyCase, Icon: IconDoc },
                { href: "/rasti-im#rezervimet", label: t.bkMyBookings, Icon: IconCalendar },
                { href: "/rasti-im#deshmite", label: t.evVaultT, Icon: IconShield },
              ].map(({ href, label, Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="bg-white rounded-xl border border-slate-200 p-4 hover:border-indigo-300 hover:shadow-sm transition text-center space-y-1.5"
                >
                  <Icon className="h-5 w-5 text-indigo-600 mx-auto" />
                  <p className="text-xs font-medium text-slate-700 flex items-center justify-center gap-1">
                    {label}
                    <IconArrowRight className="h-3 w-3 text-slate-400" />
                  </p>
                </Link>
              ))}
            </div>

            {/* Profile */}
            <Card className="p-6 space-y-4">
              <h2 className="font-semibold">{t.acctProfileT}</h2>
              <div className="text-sm text-slate-600 flex items-center gap-2 flex-wrap">
                <span>{citizen.email}</span>
                {citizen.email_verified ? (
                  <span className="inline-flex items-center gap-1 text-xs text-emerald-700 bg-emerald-50 rounded-full px-2 py-0.5">
                    <IconCheck className="h-3 w-3" />
                    {t.mkVerifVerified}
                  </span>
                ) : (
                  <span className="text-xs text-amber-700 bg-amber-50 rounded-full px-2 py-0.5">
                    {t.acctNotVerified}
                  </span>
                )}
              </div>
              <form onSubmit={saveProfile} className="space-y-4">
                <div>
                  <Label>{t.fullName}</Label>
                  <Input
                    value={profile.full_name}
                    onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                    required
                    minLength={2}
                  />
                </div>
                <div>
                  <Label>{t.mkPhone}</Label>
                  <Input
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  />
                </div>
                <div>
                  <Label>{t.acctLocale}</Label>
                  <Select
                    value={profile.locale}
                    onChange={(e) => setProfile({ ...profile, locale: e.target.value })}
                  >
                    {Object.entries(LOCALE_NAMES).map(([code, name]) => (
                      <option key={code} value={code}>
                        {name}
                      </option>
                    ))}
                  </Select>
                </div>
                <ErrorNote message={profileError} />
                {profileSaved && (
                  <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
                    {t.acctSaved}
                  </p>
                )}
                <Button type="submit" disabled={profileBusy}>
                  {profileBusy ? t.loading : t.save}
                </Button>
              </form>
            </Card>

            {/* Password change */}
            <Card className="p-6 space-y-4">
              <h2 className="font-semibold">{t.acctPwT}</h2>
              <form onSubmit={changePassword} className="space-y-4">
                <div>
                  <Label>{t.acctPwCurrent}</Label>
                  <Input
                    type="password"
                    value={pw.current}
                    onChange={(e) => setPw({ ...pw, current: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label>{t.acctPwNew}</Label>
                  <Input
                    type="password"
                    value={pw.next}
                    onChange={(e) => setPw({ ...pw, next: e.target.value })}
                    required
                    minLength={8}
                  />
                </div>
                <ErrorNote message={pwError} />
                {pwChanged && (
                  <p className="text-sm text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2">
                    {t.acctPwChanged}
                  </p>
                )}
                <Button type="submit" disabled={pwBusy}>
                  {pwBusy ? t.loading : t.acctPwT}
                </Button>
              </form>
            </Card>
          </>
        )}
      </main>
    </PublicShell>
  );
}
