"use client";

import { useState } from "react";

// Placeholder editor grid. One colour, no save. The art format and saving
// arrive in Phase 3 (see docs/protocol.md, `art` events).
const SIZES = [
  { label: "Small LED (8 x 8)", width: 8, height: 8 },
  { label: "Panel (64 x 32)", width: 64, height: 32 },
];

const ON_COLOR = "#ff0028";

export function PixelGrid() {
  const [sizeIndex, setSizeIndex] = useState(0);
  const [pixels, setPixels] = useState<ReadonlySet<number>>(new Set());
  // While dragging: true paints, false erases. null when not dragging.
  const [painting, setPainting] = useState<boolean | null>(null);
  const { width, height } = SIZES[sizeIndex];

  function setPixel(index: number, on: boolean) {
    setPixels((current) => {
      if (current.has(index) === on) return current;
      const next = new Set(current);
      if (on) next.add(index);
      else next.delete(index);
      return next;
    });
  }

  return (
    <div className="panel">
      <div className="toolbar">
        <select
          aria-label="Canvas size"
          value={sizeIndex}
          onChange={(event) => {
            setSizeIndex(Number(event.target.value));
            setPixels(new Set());
          }}
        >
          {SIZES.map((size, index) => (
            <option key={size.label} value={index}>
              {size.label}
            </option>
          ))}
        </select>
        <button type="button" onClick={() => setPixels(new Set())}>
          Clear
        </button>
        <span className="muted">{pixels.size} pixels lit</span>
      </div>
      <div
        className="pixel-grid"
        style={{
          gridTemplateColumns: `repeat(${width}, 1fr)`,
          maxWidth: width === 8 ? 320 : undefined,
        }}
        onPointerUp={() => setPainting(null)}
        onPointerLeave={() => setPainting(null)}
      >
        {Array.from({ length: width * height }, (_, index) => {
          const on = pixels.has(index);
          return (
            <button
              key={index}
              type="button"
              aria-label={`Pixel ${index % width}, ${Math.floor(index / width)}`}
              aria-pressed={on}
              style={on ? { background: ON_COLOR } : undefined}
              onPointerDown={(event) => {
                // Let the pointer move on to other cells while dragging.
                event.currentTarget.releasePointerCapture(event.pointerId);
                setPainting(!on);
                setPixel(index, !on);
              }}
              onPointerEnter={() => {
                if (painting !== null) setPixel(index, painting);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setPixel(index, !on);
                }
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
