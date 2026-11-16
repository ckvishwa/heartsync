import { PixelGrid } from "@/components/PixelGrid";

export default function EditorPage() {
  return (
    <>
      <h1>Pixel editor</h1>
      <p className="muted">
        Placeholder. Click or drag to draw. Saving and sending art to a device arrive in Phase 3.
      </p>
      <PixelGrid />
    </>
  );
}
