"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Card, Spinner } from "@/components/ui";

function VerifyInner() {
  const { t } = useI18n();
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [state, setState] = useState<"pending" | "ok" | "error">("pending");

  useEffect(() => {
    if (!token) {
      setState("error");
      return;
    }
    apiPost("/auth/verify-email", { token })
      .then(() => setState("ok"))
      .catch(() => setState("error"));
  }, [token]);

  return (
    <Card className="w-full max-w-md p-8 text-center space-y-4">
      <h1 className="text-2xl font-bold text-indigo-700">{t.appName}</h1>
      {state === "pending" && <Spinner />}
      {state === "ok" && (
        <>
          <p className="text-emerald-700 font-medium">✓ {t.emailVerified}</p>
          <Link href="/login" className="text-indigo-600 hover:underline text-sm">
            {t.login}
          </Link>
        </>
      )}
      {state === "error" && (
        <p className="text-red-600 text-sm">{t.linkInvalid}</p>
      )}
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-indigo-50 via-slate-50 to-purple-50">
      <Suspense fallback={null}>
        <VerifyInner />
      </Suspense>
    </div>
  );
}
