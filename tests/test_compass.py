#!/usr/bin/env python3
"""Eclipse Compass v0.1 (G0 fixture adapter) tests.
Run: python3 -m unittest discover tests"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import server as S  # noqa: E402


def cleaning_brief(**overrides):
    brief = {
        "category": "house_cleaning",
        "service": "Deep clean, 2 bed / 1 bath",
        "scope": {"statement": "Kitchen, bathroom, floors done.",
                  "items": ["kitchen", "bathroom", "floors"]},
        "location": {"precision": "zip", "zip": "94110"},
        "ceiling_all_in": 250,
        "license_required": "no",
        "safety_access": {"adult_present": True, "pets": "one dog"},
        "photos": [{"ref": "kitchen.jpg", "exif_stripped": True}],
        "details": {"bedrooms": 2, "bathrooms": 1,
                    "frequency": "one_time"},
        "hash": "briefhash-fixture-1",
    }
    brief.update(overrides)
    return brief


class TestCapabilityAndMapping(unittest.TestCase):
    def test_probe_declares_partner_gate_and_no_live_calls(self):
        out = S.t_tt_capability_probe(S.empty_state(), {})
        self.assertIn("PARTNER_GATED", out["modes"]["REQUEST_API"])
        self.assertIn("none", out["live_calls"])
        self.assertIn("Split A/B", out["grade"])

    def test_category_map_is_explicit_diff(self):
        out = S.t_tt_category_map(
            S.empty_state(), {"core_category": "house_cleaning"})
        self.assertEqual(out["thumbtack"]["category_id"],
                         "tt-cat-house-cleaning")
        self.assertEqual(out["diffs"][0]["class"], "CATEGORY_MAP")

    def test_unknown_category_is_named_error_not_nearest_match(self):
        with self.assertRaises(S.ToolError) as ctx:
            S.t_tt_category_map(
                S.empty_state(), {"core_category": "roofing"})
        self.assertIn("never a silent nearest-match",
                      str(ctx.exception))


class TestFormPreview(unittest.TestCase):
    def test_preview_answers_form_and_classifies_diffs(self):
        state = S.empty_state()
        brief = cleaning_brief()
        del brief["details"]["frequency"]  # leave one field unanswered
        out = S.t_tt_form_preview(state, {"brief": brief})
        variant = out["variant"]
        self.assertEqual(
            variant["form_answers"]["bedrooms"]["answer"], 2)
        self.assertIsNone(
            variant["form_answers"]["frequency"]["answer"])
        classes = {d["class"] for d in out["diffs"]}
        self.assertIn("CATEGORY_MAP", classes)
        self.assertIn("BUDGET_FORM", classes)
        self.assertIn("FEE_FORM", classes)
        self.assertIn("FORMAT_OMISSION", classes)
        self.assertIn("LOCATION_PRECISION", classes)
        budget = next(d for d in out["diffs"]
                      if d["class"] == "BUDGET_FORM")
        self.assertEqual(budget["form"], "hidden")
        self.assertEqual(variant["zip"], "94110")
        self.assertFalse(out["blocked"])

    def test_variant_hash_is_deterministic(self):
        brief = cleaning_brief()
        first = S.t_tt_form_preview(S.empty_state(), {"brief": brief})
        second = S.t_tt_form_preview(S.empty_state(), {"brief": brief})
        self.assertEqual(first["variant"]["variant_hash"],
                         second["variant"]["variant_hash"])
        changed = cleaning_brief()
        changed["details"] = dict(changed["details"], bedrooms=3)
        third = S.t_tt_form_preview(S.empty_state(), {"brief": changed})
        self.assertNotEqual(first["variant"]["variant_hash"],
                            third["variant"]["variant_hash"])

    def test_licensed_category_blocks_unknown_posture(self):
        brief = cleaning_brief(
            category="plumbing_repair", license_required="unknown",
            details={"fixture_type": "bathroom sink",
                     "problem": "leak", "active_leak": True})
        out = S.t_tt_form_preview(S.empty_state(), {"brief": brief})
        self.assertTrue(out["blocked"])
        license_diff = next(d for d in out["diffs"]
                            if d["class"] == "LICENSE_FIELD")
        self.assertIn("BLOCKED", license_diff["detail"])
        self.assertEqual(license_diff["license_type"],
                         "plumbing contractor")

    def test_licensed_category_passes_with_declared_posture(self):
        brief = cleaning_brief(
            category="plumbing_repair",
            license_required="yes:plumbing contractor",
            details={"fixture_type": "bathroom sink",
                     "problem": "leak", "active_leak": True})
        out = S.t_tt_form_preview(S.empty_state(), {"brief": brief})
        self.assertFalse(out["blocked"])

    def test_safety_block_is_carried_not_dropped(self):
        out = S.t_tt_form_preview(
            S.empty_state(), {"brief": cleaning_brief()})
        self.assertEqual(
            out["variant"]["safety_access"]["pets"], "one dog")
        classes = {d["class"] for d in out["diffs"]}
        self.assertIn("SAFETY_ACCESS_CARRIED", classes)


class TestProsAndQuotes(unittest.TestCase):
    def test_pro_search_surfaces_claims_verbatim_unverified(self):
        out = S.t_tt_pro_search(
            S.empty_state(), {"core_category": "plumbing_repair"})
        self.assertEqual(out["count"], 2)
        pro = next(p for p in out["pros"]
                   if p["platform_id"] == "tt-pro-3")
        self.assertIn("C-36", pro["license_claims"][0])
        prov = pro["license_claims_provenance"]
        self.assertEqual(prov["surfaced"], "verbatim")
        self.assertFalse(prov["verified_by_compass"])

    def test_lifecycle_states_verbatim(self):
        out = S.t_tt_request_lifecycle(
            S.empty_state(), {"request_id": "tt-req-fixture-1"})
        states = [e["state"] for e in out["lifecycle"]]
        self.assertEqual(states, ["submitted", "matched",
                                  "quotes_received"])

    def test_quotes_normalized_pro_fee_itemized_not_charged(self):
        out = S.t_tt_quotes_read(S.empty_state(), {
            "request_id": "tt-req-fixture-1", "ceiling_all_in": 250})
        self.assertEqual(out["count"], 2)
        first = out["quotes"][0]
        self.assertTrue(first["raw_preserved"])
        quote = first["quote"]
        self.assertEqual(quote["all_in_total"], 180.0)
        self.assertEqual(quote["fees"][0]["bearer"], "pro")
        self.assertEqual(quote["pro"]["display_name"], "Sparkle Co")
        self.assertTrue(first["ceiling_test"]["hireable_under_ceiling"])

    def test_unexposed_fixture_quote_fails_ceiling_test(self):
        out = S.t_tt_quotes_read(S.empty_state(), {
            "request_id": "tt-req-fixture-1", "ceiling_all_in": 250})
        second = out["quotes"][1]["quote"]
        self.assertEqual(second["fees_status"], "UNEXPOSED")
        self.assertIsNone(second["all_in_total"])
        self.assertFalse(
            out["quotes"][1]["ceiling_test"]["hireable_under_ceiling"])


class TestReceiptsAndDenylist(unittest.TestCase):
    def test_chain_valid_and_tamper_detected(self):
        state = S.empty_state()
        S.t_tt_form_preview(state, {"brief": cleaning_brief()})
        S.t_tt_quotes_read(state, {"request_id": "tt-req-fixture-1"})
        out = S.t_receipt_list(state, {})
        self.assertTrue(out["chain_valid"])
        self.assertGreaterEqual(out["count"], 2)
        tampered = copy.deepcopy(state["receipts"])
        tampered[0]["detail"]["blocked"] = "forged"
        self.assertFalse(S.verify_receipt_chain(tampered))

    def test_session_and_scraping_routes_absent_by_construction(self):
        for name in ("tt_request_submit", "session_login",
                     "cookie_reuse", "scrape_profiles",
                     "residential_proxy", "contact_harvest"):
            resp = S.handle({"jsonrpc": "2.0", "id": 1,
                             "method": "tools/call",
                             "params": {"name": name, "arguments": {}}})
            self.assertIn("error", resp)
            self.assertIn("G0-forbidden", resp["error"]["message"])
        listed = {t["name"] for t in S.tool_list()}
        self.assertTrue(listed.isdisjoint(S.FORBIDDEN_TOOL_NAMES))


if __name__ == "__main__":
    unittest.main()
