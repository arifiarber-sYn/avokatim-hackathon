import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Për noterët — zyra digjitale me AI dhe klientë të rinj",
  description:
    "Regjistri i akteve noteriale, terminet online, tarifat zyrtare sipas AI " +
    "02/2012 dhe asistentja Ava që njeh Ligjin për Noterinë. Viti i parë " +
    "falas, pastaj çmim fiks mujor.",
  alternates: { canonical: "/per-noteret" },
};

export default function PerNoteretLayout({ children }: { children: React.ReactNode }) {
  return children;
}
