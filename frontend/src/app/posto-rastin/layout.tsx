import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Posto rastin tënd — avokatët të kontaktojnë ty",
  description:
    "Përshkruaje rastin tënd ligjor falas dhe avokatët e verifikuar që " +
    "mbulojnë fushën dhe qytetin tënd të kontaktojnë direkt. Pa telefonata, " +
    "pa kërkim — ti zgjedh me kë vazhdon.",
  alternates: { canonical: "/posto-rastin" },
};

export default function PostoRastinLayout({ children }: { children: React.ReactNode }) {
  return children;
}
