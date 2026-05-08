# DESIGN BRIEF — PME AI Toolkit

> Paste this entire file into Claude (or any capable AI) when you want UI/UX design help. The prompt is self-contained.

---

## Role

You are a senior product designer specialised in B2B SaaS interfaces for French SMBs (PME). You will design the UI/UX of a Streamlit web app called **PME AI Toolkit — Facture → FEC**. Your output should include layout sketches (ASCII or markdown), a colour palette (hex codes), typography choices, micro-copy in French, component-level CSS that works inside Streamlit, and a `.streamlit/config.toml` theme configuration.

You must read the entire brief before producing anything. Then ask me up to 3 clarifying questions if needed, and only then propose a design.

---

## Product context

**What it does (one line):** Drop 10–50 supplier invoices (PDF / image) → app extracts amounts, supplier, SIRET, TVA via Gemini Vision → user reviews + corrects in a table → app exports a French legal accounting file (FEC.txt) ready to import into Sage / EBP / Cegid / Pennylane / OpenConcerto.

**Who uses it:**
- Primary persona: solo PME owner (artisan, freelancer, small shop) — 35-55 years old, low tech literacy, cares about saving time on bookkeeping. Mobile likely.
- Secondary persona: internal bookkeeper at a 5-50 employee PME — uses Sage / EBP daily, wants to spend less time typing invoices.
- Tertiary: external accountant (cabinet d'expertise comptable) — high volume, manages many clients.

**Where it runs:** Streamlit (Python framework). The app is currently functional. You are improving its visual + interaction design without changing the core flow.

**Language:** All UI copy in French. Tone: confident, professional, calm. Not playful. Not "AI hype." Speak to a 50-year-old comptable, not a CTO.

---

## Hard constraints

1. **Streamlit-native components only.** No React, no custom JS components, no third-party Streamlit components that aren't in the standard library. You may use `st.markdown(..., unsafe_allow_html=True)` for CSS injection, and `.streamlit/config.toml` for theming. That's it.
2. **No images / illustrations.** SVG / icons are OK if inlined as HTML.
3. **Font:** must be a free Google Font (loaded via CSS `@import`).
4. **Mobile responsive:** must work on iPhone 12+ width (390px). Streamlit's default is responsive, but verify your spacing.
5. **Performance:** zero heavy assets. Demo runs on local laptop and judges' laptops.
6. **Accessibility:** WCAG AA contrast for text. No colour-only state indication.

---

## Current UI structure (do not change the order)

The app is a single-page Streamlit layout with these zones top-to-bottom:

```
┌──────────────────────────────────────────────────────────┐
│ HEADER                                                   │
│ - Page title: "PME AI Toolkit — Facture → FEC"          │
│ - Subtitle/tagline: "De la facture papier à l'écriture   │
│   comptable en un clic."                                 │
│ - Top-right metric: "⏱ X min économisées"               │
├──────────────────────────────────────────────────────────┤
│ SIDEBAR (always visible)                                 │
│ - SIREN input (text_input, 9 digits)                     │
│ - "Nouveau batch" button                                 │
│ - List of past batches (small)                           │
├──────────────────────────────────────────────────────────┤
│ ① UPLOAD ZONE                                            │
│ - st.file_uploader (multi-file: PDF, PNG, JPG)          │
│ - Primary CTA: "Traiter X factures"                     │
├──────────────────────────────────────────────────────────┤
│ ② PROCESSING ZONE (visible during extraction)           │
│ - Per-file st.status (✅ / ❌ / ⏳ + filename)          │
│ - Overall st.progress bar                                │
├──────────────────────────────────────────────────────────┤
│ ③ REVIEW TABLE                                           │
│ - st.data_editor — columns: file | fournisseur |        │
│   SIRET | TVA | date | HT | TVA EUR | TTC | conf | src │
│ - Cells where field confidence < 0.7 → red background   │
│ - Click cell → edit inline → autosave                    │
├──────────────────────────────────────────────────────────┤
│ ④ EXPORT ZONE                                            │
│ - FEC preview (first 10 lines, monospace)               │
│ - Validation badge: ✅ Valid OR list of errors          │
│ - st.download_button: "Télécharger FEC"                 │
└──────────────────────────────────────────────────────────┘
```

You may suggest minor reorderings if they improve flow, but justify them.

---

## Design goals (in priority order)

1. **Look credible to a 50-year-old comptable.** Not a "ChatGPT demo." The app handles legal accounting documents — visual gravitas matters.
2. **Reduce cognitive load.** A user uploading invoices is already mentally taxed. The interface should feel calm. Whitespace > density.
3. **Make confidence highlights actionable.** Red cells today are just red. The user should immediately know: "this needs my attention, here's how to fix it."
4. **Anchor French regulatory feel.** Subtle nods to French administrative aesthetic (clean blue/white, République-style typography) without being kitsch.
5. **Polish the "wow" moment.** When the user clicks "Télécharger FEC," the UI should feel like delivering a finished product, not a CSV dump. The validation badge is your hero element.

---

## What to deliver

Produce a single response containing the following sections, in this order. Be specific. Include exact hex codes, font names, spacing values, and copy strings.

### A. Brand foundations

- **Name treatment:** how is the app name displayed? Is it "PME AI Toolkit" or rebranded? If rebranded, propose a name and justify in one line.
- **Colour palette:** 5–7 hex codes with role labels (background, surface, primary, primary-hover, text-primary, text-secondary, success, warning, error, low-confidence-cell). Provide the rationale.
- **Typography:** one heading font + one body font from Google Fonts. Sizes for h1, h2, h3, body, caption (in rem or px). Line heights.
- **Iconography:** which icon set? (e.g. Lucide via inlined SVG, or Streamlit native emoji). State your choice.
- **Radius / shadow / spacing scale:** define a spacing scale (e.g. 4 / 8 / 12 / 16 / 24 / 32 / 48 px) and apply consistently.

### B. `.streamlit/config.toml`

Provide a complete theme block:

```toml
[theme]
base = "..."
primaryColor = "..."
backgroundColor = "..."
secondaryBackgroundColor = "..."
textColor = "..."
font = "..."
```

### C. Global CSS injection

Provide a single multi-line `st.markdown("""<style>...</style>""", unsafe_allow_html=True)` block to drop into `app.py` at the top. Cover:
- Google Font import
- Body / heading typography
- Sidebar styling
- File-uploader styling (override Streamlit's default dashed border)
- Button styling (primary CTA — make it feel like a real CTA)
- `st.metric` styling
- Data editor: low-confidence cell highlighting (improve over `#ffcccc`)
- Code block styling for FEC preview
- Validation badge style (success / error variants)

### D. Per-zone redesign

For each of the 5 zones (HEADER, SIDEBAR, UPLOAD, PROCESSING, REVIEW, EXPORT):
- Brief: what's the user feeling here, what's the goal of the zone
- Layout sketch (ASCII or markdown structure) at desktop and mobile widths
- Specific copy in French (replace the current generic strings)
- Component states: empty / loading / success / error
- Micro-copy edge cases (what does the upload zone say when 0 files vs N files vs API key missing?)

### E. Confidence highlight redesign

The current implementation paints cells `#ffcccc`. Propose a more refined treatment:
- What signal does the user need? (severity? what to do?)
- Visual: colour, icon, tooltip, or all three?
- Hover/click affordance
- Provide CSS

### F. Empty / first-run state

What does the user see on first launch (no batch, no invoices)?
- Headline + sub-headline + CTA
- Inspirational micro-copy that explains the value (without being marketing fluff)

### G. Demo mode polish

The hackathon demo is 3 minutes in front of judges. Suggest 2–3 small additions that make the demo feel premium without changing the core flow:
- Animated counter on the time-saved metric? (subtle CSS keyframes)
- Toast notifications on success?
- Skeleton loaders during extraction?

### H. What you would NOT do

List 3–5 design moves you considered and rejected, with one-line reasoning. (e.g. "Dark mode — rejected because comptables work in spreadsheet-bright environments.")

---

## Inspiration / mood (for your reference, not to be copied)

- **Linear.app** — clean utility, low chrome, restraint
- **Pennylane** — French B2B fintech, professional but warm
- **Notion** — typography-led, calm
- **Stripe Dashboard** — table-heavy, data-first, but never cold
- **NOT** — Apple-style glassmorphism, neon AI gradients, dark mode purple-pink, dashboards with animated chart vomit

---

## What you must avoid

- Em-dashes that look AI-generated (use them sparingly, only where natural)
- Emoji-heavy headers
- Phrases like "Powered by AI" / "AI-powered" / "Smart" — say what it does, not how
- Bouncing / pulsing micro-animations on idle elements
- Forced gradient backgrounds
- Sans-serif "geometric" futuristic fonts (Poppins, Montserrat) — they shout "startup deck"

---

## Output format

Respond in markdown. Use code fences for CSS / TOML. Use tables where structure helps. Keep prose tight. Total length: target 1500–2500 words. Don't pad.

End your response with a one-line summary I can drop into a commit message.

---

*Brief written 2026-05-07 for a 1-week hackathon project. Source spec lives at `/docs/superpowers/specs/2026-05-07-pme-ai-toolkit-design.md` (or in this repo's plan file).*
