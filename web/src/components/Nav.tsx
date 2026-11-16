"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/devices", label: "Devices" },
  { href: "/editor", label: "Editor" },
  { href: "/releases", label: "Releases" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav>
      <Link href="/" className="brand">
        heartsync
      </Link>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          aria-current={pathname.startsWith(link.href) ? "page" : undefined}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
