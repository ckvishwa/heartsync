import Link from "next/link";

const sections = [
  { href: "/devices", title: "Devices", text: "Status of both devices: online, firmware, battery." },
  { href: "/editor", title: "Pixel editor", text: "Draw pixel art for the display. Placeholder grid for now." },
  { href: "/releases", title: "Releases", text: "Signed firmware releases and rollout. Phase 2b." },
];

export default function HomePage() {
  return (
    <>
      <h1>heartsync dashboard</h1>
      <div className="cards">
        {sections.map((section) => (
          <Link key={section.href} href={section.href} className="panel">
            <strong>{section.title}</strong>
            <p className="muted">{section.text}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
