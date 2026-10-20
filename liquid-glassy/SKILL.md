---
name: liquid-glassy
description: Recipe for building Apple-style "liquid glass" / glassmorphism surfaces with Tailwind CSS v4 — frosted blur, saturation boost, glass tint, edge highlight, drop shadow, and an optional SVG turbulence-displacement filter for the rippled/refracted look. Use whenever you need a glass card, glass modal, glass navbar, frosted overlay, or any translucent "liquid glass" UI surface. Tailored to this project's stack (Tailwind v4 + React 19 + HeroUI v3, RTL/Arabic). Triggers — "liquid glass", "glassmorphism", "frosted glass", "glassy card", "glass effect", "backdrop blur", "translucent panel", "apple glass".
---

# Liquid Glass in Tailwind v4

A real liquid-glass surface is **five layers stacked on one element**, not just a blur. Skipping any layer makes it look like cheap frosted plastic. Build them in this order:

1. **Backdrop blur + saturation** — what makes it "glass" (refracts + intensifies what's behind it).
2. **Tint** — a faint translucent fill so the pane reads as a physical surface.
3. **Edge highlight** — a light border (or gradient border) catching the light at the rim.
4. **Specular sheen** — an inset highlight on the top/left edges (the "wet" look).
5. **Drop shadow** — lifts the pane off the page so it floats.

The optional 6th layer — an **SVG turbulence + displacement filter** — adds the rippled/refracted "liquid" distortion. It's expensive and Firefox-flaky; treat it as garnish, not foundation.

> **Hard requirement:** glass only works over a **busy, colorful background** (image, gradient, photo). Over a flat color it looks like nothing. If there's no background, add one (`bg-gradient-to-br from-... via-... to-...`).

---

## The one-class recipe (copy this)

The cleanest approach in Tailwind v4 is a custom `@utility` in your CSS, so you get `glass` as a single class. Add to your main stylesheet (e.g. `resources/css/app.css`):

```css
@utility glass {
  /* 1. blur + saturation — the actual glass */
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  backdrop-filter: blur(12px) saturate(180%);
  /* 2. tint */
  background-color: color-mix(in oklab, white 12%, transparent);
  /* 3. edge highlight */
  border: 1px solid color-mix(in oklab, white 25%, transparent);
  /* 4. specular sheen (top-left highlight) + 5. drop shadow */
  box-shadow:
    inset 1px 1px 0 0 color-mix(in oklab, white 40%, transparent),
    inset -1px -1px 0 0 color-mix(in oklab, white 8%, transparent),
    0 8px 32px 0 color-mix(in oklab, black 25%, transparent);
}

/* dark-surface variant: dark tint, dimmer highlights */
@utility glass-dark {
  -webkit-backdrop-filter: blur(12px) saturate(160%);
  backdrop-filter: blur(12px) saturate(160%);
  background-color: color-mix(in oklab, black 30%, transparent);
  border: 1px solid color-mix(in oklab, white 12%, transparent);
  box-shadow:
    inset 1px 1px 0 0 color-mix(in oklab, white 18%, transparent),
    0 8px 32px 0 color-mix(in oklab, black 40%, transparent);
}
```

Then use it with normal Tailwind for shape:

```html
<div class="glass rounded-3xl p-6">
  <h3 class="text-white font-semibold">Liquid glass card</h3>
  <p class="text-white/80 text-sm">Frosted, saturated, floating.</p>
</div>
```

This project is **RTL/Arabic** — the inset highlight is symmetric enough to read fine in RTL, but if you want the sheen on the leading edge, swap the inset x-offsets under `rtl:`.

---

## Pure-utility version (no CSS file edit)

If you can't touch the stylesheet, compose it inline. Tailwind v4 ships `backdrop-blur-*` and `backdrop-saturate-*`:

```html
<div class="
  rounded-3xl p-6
  bg-white/10
  backdrop-blur-lg backdrop-saturate-150
  border border-white/20
  shadow-[0_8px_32px_rgba(0,0,0,0.25)]
  shadow-inner
">
  ...
</div>
```

The inline version can't do the *two-tone inset* sheen cleanly (only one `box-shadow` set wins), so it looks slightly flatter than the `@utility`. For anything hero-level, use the `@utility`.

**Tuning knobs:**
| Want | Change |
|---|---|
| More frost | `blur(16–24px)` / `backdrop-blur-xl` |
| Punchier colors behind | `saturate(180–200%)` |
| Thinner/clearer pane | drop tint to `white 6%`, blur to `6px` |
| Sharper rim | bump border to `white 35%` |
| Heavier float | shadow `0 16px 48px black 35%` |

---

## Layer 6 — the "liquid" distortion (SVG displacement)

This is what separates *glassmorphism* from *liquid* glass: a turbulence map displaces the backdrop so edges of content behind it ripple like water/refraction.

Drop the filter once anywhere in the DOM (it's invisible itself):

```html
<svg class="absolute size-0" aria-hidden="true">
  <filter id="liquid-glass">
    <feTurbulence type="fractalNoise" baseFrequency="0.008 0.008"
                  numOctaves="2" seed="92" result="noise" />
    <feGaussianBlur in="noise" stdDeviation="2" result="blurred" />
    <feDisplacementMap in="SourceGraphic" in2="blurred"
                       scale="40" xChannelSelector="R" yChannelSelector="G" />
  </filter>
</svg>
```

Apply it via `backdrop-filter` (so it distorts the *backdrop*, not the card's own content) using arbitrary properties:

```html
<div class="glass rounded-3xl p-6 [backdrop-filter:url(#liquid-glass)_blur(8px)_saturate(180%)]">
  ...
</div>
```

**Caveats — read before shipping:**
- `url(#id)` in `backdrop-filter` works in Chromium; **Firefox/Safari support is patchy** — always pair it with a plain `blur()` so it degrades to ordinary glass.
- Large `scale` (>60) warps text behind it into mush. Keep `scale` 20–45 for subtle refraction.
- `baseFrequency` controls ripple size: lower (`0.005`) = big slow waves, higher (`0.03`) = fine frost.
- It's GPU-heavy. **One or two on screen, never on a scrolling list of cards.**

---

## Animating the "liquid" (optional)

Two cheap options. Prefer the background drift — animating `feTurbulence` attributes is jankier.

```css
@keyframes glass-float {
  0%, 100% { background-position: center center; }
  25%      { background-position: 30% 70%; }
  50%      { background-position: 70% 30%; }
  75%      { background-position: 40% 60%; }
}
/* apply to the *background image* layer behind the glass, not the glass itself */
.glass-bg-anim { animation: glass-float 15s ease-in-out infinite; }
```

Respect motion preferences — wrap any auto-animation:

```css
@media (prefers-reduced-motion: reduce) {
  .glass-bg-anim { animation: none; }
}
```

---

## Ready-to-paste React component (React 19, this project)

```jsx
// Drop the <svg> filter once near your layout root.
function LiquidGlassFilter() {
  return (
    <svg className="absolute size-0" aria-hidden="true">
      <filter id="liquid-glass">
        <feTurbulence type="fractalNoise" baseFrequency="0.008 0.008" numOctaves="2" seed="92" result="noise" />
        <feGaussianBlur in="noise" stdDeviation="2" result="blurred" />
        <feDisplacementMap in="SourceGraphic" in2="blurred" scale="40" xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </svg>
  );
}

function GlassCard({ children, className = "", liquid = false }) {
  return (
    <div
      className={[
        "glass rounded-3xl p-6 text-white",
        liquid && "[backdrop-filter:url(#liquid-glass)_blur(8px)_saturate(180%)]",
        className,
      ].filter(Boolean).join(" ")}
    >
      {children}
    </div>
  );
}
```

---

## Accessibility & gotchas (don't skip)

- **Contrast:** blurred backdrops kill text contrast. Use `text-white` + a `text-shadow` or a darker tint, and verify against the *brightest* part of the background, not the average.
- **`overflow-hidden` clips the blur** on rounded corners — keep `rounded-*` on the same element as the `backdrop-filter`, or the blur leaks past the radius.
- **A parent `filter`/`transform`/`will-change`/`opacity` on an ancestor breaks `backdrop-filter`** (it creates a containing block that resets the backdrop). If your glass shows no blur, an ancestor is the culprit.
- **Stacking:** the element needs something *behind* it in the same stacking context to blur. A glass card with nothing behind it = invisible effect.
- **Performance:** `backdrop-filter` repaints on scroll. Avoid on long lists; fine for modals, navbars, hero cards.
- **HeroUI v3:** for a glass `Modal`/`Card`, apply `glass` to the panel/content slot via `className`, and make sure the modal's own backdrop isn't already a solid overlay hiding the page behind it.
