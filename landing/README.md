# Taco — landing + demo console

Polished clickable prototype for **Taco — The Autonomous Casualty Office**, a B2B
pre-deployment certification platform for robot policies.

- **Landing page** (`/`) — scrolling product narrative: problem → what Taco does →
  6-stage pipeline → deep failure story (FR-001) → certification model →
  deliverables → commercial value → demo CTA.
- **Demo console** (`/demo`) — stubbed enterprise dashboard for the *Skild AI*
  account: Overview, Policies, Audit Runs, Failure Evidence, Internal Traces,
  Controls, Certification, Binder.

Visual system follows `DESIGN.md`: warm dark canvas, off-white ink, hairline
borders (no shadows), tight rectangular cards/buttons, Inter for prose, DM Mono
for traces/certs/IDs/terminals. No backend — all data is static stub
(`src/data/stub.js`).

## Run

```bash
npm install
npm run dev      # http://localhost:5180
npm run build    # production build → dist/
```

## Hero video click path

1. Landing hero → scroll the pipeline → scroll to the FR-001 failure story.
2. Click **Open Skild AI demo** → `/demo` Overview.
3. **Failure Evidence** → FR-001 native / counterfactual / mitigated replays.
4. **Internal Traces** → target-feature collapse + risk signature 0.82s early.
5. **Certification** → conditional policy-version certificate.
6. **Binder** → conditional underwriting artifact.

The **Controls** page is lightly interactive: disabling any required control
degrades certification from *Conditional Pass* to *Pass with Exclusion*
everywhere it's shown (Overview, Certification, sidebar badge).

## Structure

```
src/
  components/   Nav, Footer, Wordmark, RobotScene (SVG), TraceViewer (Perfetto-style)
  landing/      Landing.jsx — all 8 sections + hero
  dashboard/    Dashboard.jsx (shell + routing) and pages/*
  data/stub.js  all stubbed enterprise data
  styles/       global.css (design tokens) + app.css
```
