/**
 * Small shared SVG icon set for the public pages — replaces emoji so the
 * interface renders identically on every device. Stroke-based, 24x24,
 * inherits currentColor.
 */
import { ReactNode } from "react";

function base(props: { className?: string }, children: ReactNode) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={props.className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function IconScale(props: { className?: string }) {
  return base(
    props,
    <>
      <path d="M12 3v18M8 21h8M12 6h7M12 6H5" />
      <path d="M5 6l-2.5 6a3 3 0 0 0 5 0L5 6zM19 6l-2.5 6a3 3 0 0 0 5 0L19 6z" />
    </>
  );
}

export function IconChat(props: { className?: string }) {
  return base(
    props,
    <>
      <path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 8-8h2a8 8 0 0 1 8 8z" />
      <circle cx="9.5" cy="12" r="0.6" fill="currentColor" stroke="none" />
      <circle cx="13" cy="12" r="0.6" fill="currentColor" stroke="none" />
      <circle cx="16.5" cy="12" r="0.6" fill="currentColor" stroke="none" />
    </>
  );
}

export function IconShield(props: { className?: string }) {
  return base(
    props,
    <>
      <path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3z" />
      <path d="M9 12l2 2 4-4" />
    </>
  );
}

export function IconMic(props: { className?: string }) {
  return base(
    props,
    <>
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0M12 17v4" />
    </>
  );
}

export function IconDoc(props: { className?: string }) {
  return base(
    props,
    <>
      <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
      <path d="M14 3v5h5M9.5 13h5M9.5 17h5" />
    </>
  );
}

export function IconCalendar(props: { className?: string }) {
  return base(
    props,
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M8 3v4M16 3v4M3 10h18" />
    </>
  );
}

export function IconStar(props: { className?: string }) {
  return base(
    props,
    <path d="M12 3l2.7 5.6 6.1.8-4.5 4.3 1.1 6-5.4-2.9L6.6 19.7l1.1-6L3.2 9.4l6.1-.8L12 3z" />
  );
}

export function IconUsers(props: { className?: string }) {
  return base(
    props,
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <path d="M16.5 4.5a3.5 3.5 0 0 1 0 7M21 20c0-2.8-1.9-5.1-4.5-5.8" />
    </>
  );
}

export function IconLock(props: { className?: string }) {
  return base(
    props,
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </>
  );
}

export function IconGlobe(props: { className?: string }) {
  return base(
    props,
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c2.5 2.6 4 5.7 4 9s-1.5 6.4-4 9c-2.5-2.6-4-5.7-4-9s1.5-6.4 4-9z" />
    </>
  );
}

export function IconCheck(props: { className?: string }) {
  return base(props, <path d="M20 6L9 17l-5-5" />);
}

export function IconBolt(props: { className?: string }) {
  return base(props, <path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z" />);
}

export function IconMail(props: { className?: string }) {
  return base(
    props,
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </>
  );
}

export function IconArrowRight(props: { className?: string }) {
  return base(props, <path d="M5 12h14M13 6l6 6-6 6" />);
}
