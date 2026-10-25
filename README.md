# Eclipse Compass MCP

**Powered by Cyan Eclipse Technologies** — https://cetech.ai

**Eclipse Compass — the Thumbtack adapter: one approved Task Brief becomes a native Thumbtack request, matched pros and their quotes return normalized and all-in, and a hire runs only inside an Eclipse Procure mandate. The pro side gives CETech the same discipline as a Thumbtack business.**

## Why this exists

Thumbtack is the one open door in the gig landscape: a real, publicly documented Partner Platform (categories with per-category request forms, business search, requests, reviews, OAuth). Compass is the first adapter of the Eclipse gig family — the shared Task Brief core (Eclipse Gig Core) rendered into Thumbtack's own shape: ZIP-first, the category's own form answered from the brief, pros' quotes normalized to one all-in total, and the hire gated by the core's mandate check. Compass points; it does not vouch. The platform's ratings say what they say.

## Status — honest labels

v0.1.0, phase **G0 (fixture adapter)**. Local stdio transport, Python stdlib only. All data comes from shipped fixtures shaped like Partner Platform responses. **No live Thumbtack call exists in the code, no partner application has been filed, nothing is submitted, and no certification is claimed — bench pending.** Sanction grade: **Split A/B** — the Partner Platform is documented (A as a surface); obtaining partner credentials and production access is an onboarding gate (B), and it is the **owner's G1 step** [verify current application steps at G1].

Explicitly NOT in v0.1: live request submission, any hire execution (the adapter holds no independent hire power — the gig core's `hire_check` evaluates the mandate), messaging, and the pro-side surface. Session/cookie automation, unofficial endpoints, and scraping are prohibited at any tier (spec §8.6) and are absent by construction — the denylist is enforced in code.

## Native adaptation, diffed — never silent

`tt_form_preview` answers Thumbtack's per-category form from the brief's details and classifies every difference:

| Diff class | In the Thumbtack chapter |
|---|---|
| `CATEGORY_MAP` | Core taxonomy → Thumbtack category, explicit. An unmapped core category is a named error, never a silent nearest-match. |
| `BUDGET_FORM` | `hidden` — the classic lead flow states no buyer price; pros price the job. The brief ceiling is not presented; it governs at quote time. |
| `FEE_FORM` | `pro_pays_lead_fee` — the platform charges the pro per lead; the pro-side fee is itemized on quotes because it explains quote levels, but it is not charged to the buyer. |
| `LICENSE_FIELD` | Licensed categories (e.g. Plumbing) carry the brief's license posture. Posture `unknown` on a licensed category **blocks** the variant until the brief declares it. |
| `FORMAT_OMISSION` | A form field the brief does not answer. Omissions are diffs — answers are never invented. |
| `LOCATION_PRECISION` | The request anchors to the brief's ZIP tier; precision never increases in adaptation. |
| `SAFETY_ACCESS_CARRIED` | The brief's safety + access block (who is present, pets, entry) rides with the variant; it is never dropped for form convenience. |

The variant carries a SHA-256 variant hash that joins the brief hash in the owner's approval record — any later brief edit invalidates both.

## Pros + quotes

Pro search surfaces ratings, hire counts, platform badges, and license claims **verbatim with provenance** (`verified_by_compass: false`). Compass never asserts a claim is valid, current, or sufficient; verification is a link-out to the issuing authority, recorded as owner-performed.

Quotes are normalized by the **gig core engine** (loaded from the sibling `eclipse-gig-core-mcp`), raw form preserved alongside: face price, itemized fees with bearers, and the all-in the ceiling test runs on. The fixture request ships the teaching pair — an exposed-fee quote at all-in 180 that passes a 250 ceiling, and a cheaper-on-its-face quote whose fees are `UNEXPOSED`, which **cannot** be marked hireable under the ceiling.

## Tools (7)

| Tool | What it does |
|---|---|
| `tt_capability_probe` | Dated capability record: grade, mode matrix, the G1 partner gate. |
| `tt_category_map` | Core category → Thumbtack category, as an explicit diff. |
| `tt_form_preview` | Brief → native request variant + classified diffs + variant hash. |
| `tt_pro_search` | Fixture pro results; claims verbatim with provenance. |
| `tt_request_lifecycle` | Fixture request states, recorded verbatim. |
| `tt_quotes_read` | Fixture quotes through the core normalization engine + ceiling test. |
| `receipt_list` | List the append-only receipt chain and verify it. |

## Run it

```bash
python3 server.py            # MCP over stdio, stdlib only, no dependencies
python3 smoke.py             # end-to-end smoke over real stdio (temp state)
python3 -m unittest discover tests
python3 make_icon.py         # regenerate icon-512.png
```

Requires the sibling `eclipse-gig-core-mcp` (the family's shared normalization + hire-gate engine). State persists in `data/state.json` beside the server (override with `ECLIPSE_COMPASS_STATE`). `data/` is gitignored.

## Roadmap (per spec)

- **G1** — live `REQUEST_API` + `READ_API` behind owner-obtained Thumbtack partner credentials; hire execution only through the core mandate gate.
- **Pro side** — leads/messages/profile discipline for a CETech Thumbtack business (Sterling chapter), later phase.

## License / attribution

A Cyan Eclipse Technologies product. The "Powered by Cyan Eclipse Technologies" attribution travels with it.
