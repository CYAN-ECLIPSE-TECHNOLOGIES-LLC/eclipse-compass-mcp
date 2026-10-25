#!/usr/bin/env python3
"""Eclipse Compass MCP — v0.1.0, phase G0 (Thumbtack fixture adapter).

Powered by Cyan Eclipse Technologies (cetech.ai).

Eclipse Compass — the Thumbtack adapter: one approved Task Brief
becomes a native Thumbtack request, matched pros and their quotes
return normalized and all-in, and a hire runs only inside an Eclipse
Procure mandate. The pro side gives CETech the same discipline as a
Thumbtack business.

G0 SCOPE — FIXTURES ONLY:
  * Category mapping + native request-form previews are built from
    shipped fixtures shaped like Thumbtack Partner Platform
    responses (categories with per-category request forms, pro
    search results, request/quote shapes).
  * Quote normalization is delegated to the Eclipse Gig Core engine,
    loaded from the sibling eclipse-gig-core-mcp directory — one
    normalization law for the whole family.
  * NO live Thumbtack call exists in this file. Thumbtack partner
    access is an owner G1 step. Session, cookie, and scraping routes
    are prohibited at any tier (spec 8.6) and are absent by
    construction — the denylist below is enforced in code.

Pro license claims are surfaced VERBATIM with provenance. Compass
never asserts a claim is valid, current, or sufficient (spec 8.3).

Transport: MCP over stdio (newline-delimited JSON-RPC 2.0), stdlib only.
State: $ECLIPSE_COMPASS_STATE or ./data/state.json beside this file.
"""
import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
STATE_PATH = Path(os.environ.get(
    "ECLIPSE_COMPASS_STATE", HERE / "data" / "state.json"))
CORE_SERVER = HERE.parent / "eclipse-gig-core-mcp" / "server.py"


def _load_core():
    spec = importlib.util.spec_from_file_location(
        "eclipse_gig_core_server", CORE_SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE = _load_core()
ToolError = CORE.ToolError
sha, canon, money = CORE.sha, CORE.canon, CORE.money


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------- state
def empty_state() -> dict:
    return {"previews": {}, "receipts": []}


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return empty_state()


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=1))


def emit_receipt(state: dict, rtype: str, detail: dict) -> dict:
    prev = state["receipts"][-1]["hash"] if state["receipts"] else "GENESIS"
    entry = {"seq": len(state["receipts"]) + 1, "ts": int(time.time()),
             "type": rtype, "prev_hash": prev, "detail": detail}
    entry["hash"] = sha(prev + canon(
        {k: v for k, v in entry.items() if k != "hash"}))
    state["receipts"].append(entry)
    return entry


def verify_receipt_chain(receipts) -> bool:
    return CORE.verify_receipt_chain(receipts)


# ------------------------------------------------------------------ fixtures
def load_categories():
    data = json.loads((FIXTURES / "thumbtack_categories.json").read_text())
    return {c["core_category"]: c for c in data["categories"]}


def load_pros():
    data = json.loads((FIXTURES / "thumbtack_pros.json").read_text())
    return data["pros"]


def load_requests():
    data = json.loads((FIXTURES / "thumbtack_requests.json").read_text())
    return {r["request_id"]: r for r in data["requests"]}


def public_pro(pro: dict) -> dict:
    out = json.loads(json.dumps(pro))
    # Claims travel verbatim; provenance says whose claim it is and
    # that Compass does not vouch for it (spec 8.3/8.4).
    out["license_claims_provenance"] = {
        "claimed_by": "the pro's Thumbtack profile (fixture record)",
        "surfaced": "verbatim",
        "verified_by_compass": False,
        "note": "Compass surfaces license claims as data with "
                "provenance; it never asserts a claim is valid, "
                "current, or sufficient. Verification is a link-out "
                "to the issuing authority, recorded as "
                "owner-performed (spec 8.3).",
    }
    out["badges_basis"] = "platform-issued only, verbatim (fixture)"
    return out


# --------------------------------------------------------------------- tools
def t_tt_capability_probe(state, args):
    return {
        "adapter": "Eclipse Compass (Thumbtack)",
        "checked": "2026-10-25",
        "grade": "Split A/B — Partner Platform documented (A as a "
                 "surface); partner credentials + production access "
                 "via Thumbtack onboarding (B) [verify at G1]",
        "modes": {
            "REQUEST_API": "PARTNER_GATED — owner G1 step; v0.1 "
                           "builds previews only, submits nothing",
            "READ_API": "FIXTURE — pro search, request lifecycle, and "
                        "quotes read from shipped fixtures",
            "HIRE_API": "MANDATE_ONLY — a hire runs only inside an "
                        "Eclipse Procure / Agent Wallet mandate, "
                        "evaluated by the gig core hire gate; Compass "
                        "holds no independent hire power",
            "MESSAGE_API": "NOT IN v0.1 [marketplace-side messaging "
                           "scope to verify at build, spec ch.10]",
            "PRO_API": "NOT IN v0.1 (pro-side pilot is a later phase)",
        },
        "live_calls": "none — no network code path exists in v0.1",
        "kill_switch": "family-level adapter_kill_switch per spec 5.2; "
                       "hire capability freezes first",
    }


def map_category(core_category: str) -> dict:
    categories = load_categories()
    category = categories.get(core_category)
    if not category:
        raise ToolError(
            f"no Thumbtack category mapping for {core_category!r}: "
            "category mapping is a diff, never a silent nearest-match "
            "(spec 5.4)")
    return category


def t_tt_category_map(state, args):
    category = map_category(str(args.get("core_category") or ""))
    return {
        "core_category": category["core_category"],
        "thumbtack": {"category_id": category["tt_category_id"],
                      "name": category["name"],
                      "model": category["model"]},
        "licensed": category["licensed"],
        "license_type": category["license_type"],
        "diffs": [{"class": "CATEGORY_MAP",
                   "detail": f"core {category['core_category']} -> "
                             f"Thumbtack {category['name']} "
                             f"({category['tt_category_id']}); mapping "
                             "is explicit, never a silent nearest-match"}],
        "provenance": {"source": "thumbtack",
                       "feed_file": "thumbtack_categories.json",
                       "basis": "local fixture shaped like the Partner "
                                "Platform Categories responses; no live "
                                "call"},
    }


def t_tt_form_preview(state, args):
    brief = args.get("brief") or {}
    core_category = str(brief.get("category") or "")
    category = map_category(core_category)
    details = brief.get("details") or {}
    answers, omissions = {}, []
    for field in category["request_form"]:
        key = field["key"]
        if key in details:
            answers[key] = {"question": field["question"],
                            "answer": details[key],
                            "source": "brief details"}
        else:
            # Unanswered form fields are diffs, never invented
            # answers (spec ch.10 native adaptation).
            omissions.append(key)
            answers[key] = {"question": field["question"],
                            "answer": None,
                            "source": "UNANSWERED — FORMAT_OMISSION diff"}
    diffs = [{"class": "CATEGORY_MAP",
              "detail": f"core {core_category} -> Thumbtack "
                        f"{category['name']} ({category['tt_category_id']})"},
             {"class": "BUDGET_FORM", "form": "hidden",
              "detail": "Thumbtack's classic lead flow shows the buyer "
                        "no price to state — pros price the job. The "
                        "brief ceiling is not presented; it governs "
                        "at quote time (spec 5.3/5.4)."},
             {"class": "FEE_FORM", "form": "pro_pays_lead_fee",
              "detail": "On the lead model the platform charges the "
                        "PRO per lead; buyer-side platform fee: none "
                        "in the classic flow [verify at G1]. The "
                        "pro-side fee is itemized on quotes because "
                        "it explains quote levels (spec 5.3)."},
             {"class": "LOCATION_PRECISION", "form": "zip",
              "detail": "Request anchored to the brief's ZIP tier; "
                        "precision never increases in adaptation "
                        "(spec 5.4)."}]
    for key in omissions:
        field = next(f for f in category["request_form"]
                     if f["key"] == key)
        diffs.append({"class": "FORMAT_OMISSION", "field": key,
                      "required": bool(field["required"]),
                      "detail": "form field unanswered by the brief; "
                                "never invented"})
    blocked = False
    if category["licensed"]:
        posture = str(brief.get("license_required") or "unknown")
        diff = {"class": "LICENSE_FIELD",
                "license_type": category["license_type"],
                "brief_license_required": posture,
                "detail": "Category implies licensed work; the "
                          "brief's license posture travels with the "
                          "variant (spec 8.3)."}
        if posture == "unknown":
            blocked = True
            diff["detail"] += (" BLOCKED: the brief must declare its "
                                "license posture before this variant "
                                "can be approved (spec 5.4/8.3).")
        diffs.append(diff)
    safety = brief.get("safety_access") or {}
    if safety:
        diffs.append({"class": "SAFETY_ACCESS_CARRIED",
                      "detail": "Safety + access block carried into "
                                "the variant notes; an adapter may not "
                                "drop presence/pet/access facts for "
                                "form convenience (spec 8.4)."})
    variant = {
        "platform": "thumbtack",
        "tt_category_id": category["tt_category_id"],
        "tt_category_name": category["name"],
        "model": category["model"],
        "zip": (brief.get("location") or {}).get("zip"),
        "scope_statement": (brief.get("scope") or {}).get("statement"),
        "form_answers": answers,
        "safety_access": safety,
        "photos": [{"ref": p.get("ref"),
                    "exif_stripped": p.get("exif_stripped")}
                   for p in brief.get("photos") or []],
        "ceiling_presentation": "hidden (governs at quote time)",
        "source_brief_hash": brief.get("hash"),
    }
    variant["variant_hash"] = sha(canon(variant))
    variant_id = "ttvar_" + variant["variant_hash"][:12]
    variant["variant_id"] = variant_id
    out = {"variant": variant, "diffs": diffs, "blocked": blocked,
           "approval_note": "The variant hash joins the brief hash in "
                            "the owner's approval record; any later "
                            "brief edit invalidates both (spec 5.1)."}
    if variant_id not in state["previews"]:
        state["previews"][variant_id] = variant
        emit_receipt(state, "variant_previewed", {
            "variant_id": variant_id, "variant_hash": variant["variant_hash"],
            "tt_category_id": category["tt_category_id"],
            "source_brief_hash": brief.get("hash"), "blocked": blocked,
            "diff_classes": sorted({d["class"] for d in diffs})})
    return out


def t_tt_pro_search(state, args):
    core_category = str(args.get("core_category") or "")
    if core_category:
        map_category(core_category)  # unknown category = named error
    pros = [public_pro(p) for p in load_pros()
            if not core_category or p["core_category"] == core_category]
    return {"pros": pros, "count": len(pros),
            "feed_mode": "local_fixture_only",
            "note": "Ratings, hire counts, badges, and license claims "
                    "are the platform's/pro's own words, surfaced "
                    "verbatim with provenance. Compass points; it "
                    "does not vouch (spec ch.10 naming test)."}


def t_tt_request_lifecycle(state, args):
    request = load_requests().get(str(args.get("request_id") or ""))
    if not request:
        raise ToolError(f"unknown fixture request: {args.get('request_id')}")
    return {"request_id": request["request_id"],
            "core_category": request["core_category"],
            "zip": request["zip"],
            "lifecycle": request["lifecycle"],
            "lifecycle_basis": "platform states recorded verbatim, "
                               "never smoothed (spec 5.2 job_track)",
            "feed_mode": "local_fixture_only"}


def t_tt_quotes_read(state, args):
    request = load_requests().get(str(args.get("request_id") or ""))
    if not request:
        raise ToolError(f"unknown fixture request: {args.get('request_id')}")
    pros = {p["platform_id"]: p for p in load_pros()}
    quotes = []
    for raw in request["quotes"]:
        pro = pros.get(raw["pro_id"]) or {}
        normalized = CORE.normalize_quote({
            "platform": "thumbtack",
            "pro": {"platform_id": raw["pro_id"],
                    "display_name": pro.get("display_name"),
                    "rating": pro.get("rating"),
                    "hires": pro.get("hires"),
                    "license_claims": pro.get("license_claims") or [],
                    "badges": pro.get("badges") or []},
            "model": raw["model"], "job_price": raw["job_price"],
            "fees": raw["fees"], "fees_exposed": raw["fees_exposed"],
            "tax": raw.get("tax", 0),
            "valid_until": raw.get("valid_until"),
            "raw_quote_ref": raw["raw_ref"],
        })
        entry = {"quote": normalized,
                 "raw_quote": raw,
                 "raw_preserved": True}
        if args.get("ceiling_all_in") is not None:
            entry["ceiling_test"] = CORE.ceiling_test(
                normalized, args["ceiling_all_in"])
        quotes.append(entry)
    emit_receipt(state, "quotes_read", {
        "request_id": request["request_id"], "count": len(quotes),
        "quote_ids": [q["quote"]["quote_id"] for q in quotes]})
    return {"request_id": request["request_id"], "quotes": quotes,
            "count": len(quotes), "feed_mode": "local_fixture_only"}


def t_receipt_list(state, args):
    limit = args.get("limit")
    receipts = state["receipts"]
    if limit is not None:
        receipts = receipts[-int(limit):]
    return {"receipts": receipts, "count": len(state["receipts"]),
            "chain_valid": verify_receipt_chain(state["receipts"])}


TOOLS = {
    "tt_capability_probe": (
        t_tt_capability_probe,
        "Dated capability record for the Thumbtack adapter: sanction "
        "grade, mode matrix, and the G1 partner gate. v0.1 makes no "
        "live call.",
        {}, []),
    "tt_category_map": (
        t_tt_category_map,
        "Map a gig-core taxonomy category to its Thumbtack category. "
        "Mapping is an explicit CATEGORY_MAP diff; an unknown core "
        "category is a named error, never a silent nearest-match.",
        {"core_category": {"type": "string"}}, ["core_category"]),
    "tt_form_preview": (
        t_tt_form_preview,
        "Build the native Thumbtack request variant from a Task "
        "Brief object: the category's own form answered from the "
        "brief, plus classified diffs (CATEGORY_MAP, BUDGET_FORM: "
        "hidden, FEE_FORM: pro-pays-lead-fee, LICENSE_FIELD, "
        "FORMAT_OMISSION, LOCATION_PRECISION). Unanswered form "
        "fields are diffs, never invented answers. Licensed "
        "categories with an undeclared brief posture are BLOCKED.",
        {"brief": {"type": "object"}}, ["brief"]),
    "tt_pro_search": (
        t_tt_pro_search,
        "Read fixture pro search results for a category. Ratings, "
        "hire counts, badges, and license claims are surfaced "
        "verbatim with provenance; Compass never asserts a license "
        "claim is valid.",
        {"core_category": {"type": "string"}}, []),
    "tt_request_lifecycle": (
        t_tt_request_lifecycle,
        "Read a fixture request's lifecycle states, recorded "
        "verbatim (submitted -> matched -> quotes_received).",
        {"request_id": {"type": "string"}}, ["request_id"]),
    "tt_quotes_read": (
        t_tt_quotes_read,
        "Read a fixture request's quotes, normalized by the gig "
        "core engine (face + itemized fees + all-in), raw form "
        "preserved alongside. Optional ceiling_all_in runs the "
        "core ceiling test — UNEXPOSED-fee quotes cannot pass it.",
        {"request_id": {"type": "string"},
         "ceiling_all_in": {"type": "number"}}, ["request_id"]),
    "receipt_list": (
        t_receipt_list,
        "List the append-only, hash-chained Compass receipts and "
        "verify the chain.",
        {"limit": {"type": "integer"}}, []),
}

# Capability denylist, stated in code: no session, cookie, scraping,
# proxy, or direct-hire route exists at any tier (spec 8.6). Live
# request submission is an owner G1 partner step, not a v0.1 tool.
FORBIDDEN_TOOL_NAMES = {
    "tt_request_submit", "tt_direct_hire", "session_login",
    "cookie_reuse", "scrape_search", "scrape_profiles",
    "residential_proxy", "contact_harvest",
}


def tool_list():
    return [{"name": name, "description": description,
             "inputSchema": {"type": "object", "properties": props,
                             "required": required}}
            for name, (_, description, props, required) in TOOLS.items()]


def handle(req: dict):
    method, rid = req.get("method", ""), req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": req.get("params", {}).get(
                "protocolVersion", "2025-03-26"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "eclipse-compass", "version": "0.1.0"}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid,
                "result": {"tools": tool_list()}}
    if method == "tools/call":
        name = req["params"]["name"]
        args = req["params"].get("arguments", {})
        if name in FORBIDDEN_TOOL_NAMES or name not in TOOLS:
            return {"jsonrpc": "2.0", "id": rid, "error": {
                "code": -32602,
                "message": f"unknown or G0-forbidden tool {name} "
                           "(live submission is owner-gated G1; "
                           "session/scraping routes are prohibited)"}}
        state = load_state()
        try:
            out = TOOLS[name][0](state, args)
            save_state(state)
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": json.dumps(out, indent=1)}]}}
        except ToolError as exc:
            return {"jsonrpc": "2.0", "id": rid, "result": {
                "content": [{"type": "text",
                             "text": json.dumps({"error": str(exc)})}],
                "isError": True}}
    if rid is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": {
            "code": -32601, "message": f"method not found: {method}"}}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            response = handle(json.loads(line))
        except Exception as exc:  # never crash the transport
            response = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32603, "message": str(exc)}}
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
