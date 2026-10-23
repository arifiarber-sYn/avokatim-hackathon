/**
 * Citizen avatar (D-058): the social-login photo when available, otherwise
 * initials on the brand gradient. Photos are data URLs fetched server-side,
 * so no third-party image hosts are ever contacted (CSP img-src 'self' data:).
 */

export function initialsOf(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0].toUpperCase())
      .join("") || "?"
  );
}

export default function CitizenAvatar({
  name,
  photo,
  className = "h-7 w-7 text-xs",
}: {
  name: string;
  photo?: string | null;
  className?: string;
}) {
  if (photo) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- data URL, not an optimizable remote asset
      <img
        src={photo}
        alt={name}
        className={`${className} rounded-full object-cover shrink-0`}
      />
    );
  }
  return (
    <span
      className={`${className} rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0`}
    >
      {initialsOf(name)}
    </span>
  );
}
