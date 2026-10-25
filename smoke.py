#!/usr/bin/env python3
"""End-to-end stdio smoke for Eclipse Compass v0.1 (G0).

Temp state. Drives initialize -> tt_capability_probe ->
tt_category_map -> tt_form_preview -> tt_pro_search ->
tt_request_lifecycle -> tt_quotes_read (ceiling test incl. the
UNEXPOSED fixture quote) -> receipt_list.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent


def rpc(proc, rid, method, params=None):
    req = {"jsonrpc": "2.0", "id": rid, "method": method,
           "params": params or {}}
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())


def call(proc, rid, name, args):
    response = rpc(proc, rid, "tools/call", {"name": name, "arguments": args})
    return json.loads(response["result"]["content"][0]["text"])


def main():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["ECLIPSE_COMPASS_STATE"] = str(Path(tmp) / "state.json")
        proc = subprocess.Popen(
            [sys.executable, str(HERE / "server.py")],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            cwd=str(HERE), env=env)
        try:
            init = rpc(proc, 1, "initialize",
                       {"protocolVersion": "2025-03-26"})
            assert init["result"]["serverInfo"]["name"] == "eclipse-compass"
            print("initialize OK")

            probe = call(proc, 2, "tt_capability_probe", {})
            assert "PARTNER_GATED" in probe["modes"]["REQUEST_API"]
            print("capability_probe OK; partner gate stated, no live call")

            mapping = call(proc, 3, "tt_category_map",
                           {"core_category": "house_cleaning"})
            assert mapping["thumbtack"]["category_id"] == \
                "tt-cat-house-cleaning"
            print("category_map OK; explicit CATEGORY_MAP diff")

            brief = {
                "category": "house_cleaning",
                "scope": {"statement": "Kitchen, bathroom, floors done."},
                "location": {"precision": "zip", "zip": "94110"},
                "ceiling_all_in": 250, "license_required": "no",
                "safety_access": {"adult_present": True,
                                  "pets": "one dog"},
                "photos": [{"ref": "kitchen.jpg", "exif_stripped": True}],
                "details": {"bedrooms": 2, "bathrooms": 1},
                "hash": "smoke-brief-hash",
            }
            preview = call(proc, 4, "tt_form_preview", {"brief": brief})
            assert preview["blocked"] is False
            assert preview["variant"]["variant_hash"]
            classes = {d["class"] for d in preview["diffs"]}
            assert "FORMAT_OMISSION" in classes  # frequency unanswered
            assert "BUDGET_FORM" in classes
            print("form_preview OK; variant hash issued, omissions diffed")

            pros = call(proc, 5, "tt_pro_search",
                        {"core_category": "plumbing_repair"})
            claim_pro = next(p for p in pros["pros"]
                             if p["platform_id"] == "tt-pro-3")
            assert "C-36" in claim_pro["license_claims"][0]
            assert claim_pro["license_claims_provenance"][
                "verified_by_compass"] is False
            print("pro_search OK; license claim verbatim, unverified")

            life = call(proc, 6, "tt_request_lifecycle",
                        {"request_id": "tt-req-fixture-1"})
            assert [e["state"] for e in life["lifecycle"]] == \
                ["submitted", "matched", "quotes_received"]
            print("request_lifecycle OK; states verbatim")

            quotes = call(proc, 7, "tt_quotes_read", {
                "request_id": "tt-req-fixture-1", "ceiling_all_in": 250})
            assert quotes["quotes"][0]["quote"]["all_in_total"] == 180.0
            assert quotes["quotes"][1]["quote"]["fees_status"] == \
                "UNEXPOSED"
            assert quotes["quotes"][1]["ceiling_test"][
                "hireable_under_ceiling"] is False
            print("quotes_read OK; all-in 180 hireable, "
                  "UNEXPOSED quote barred by the ceiling test")

            receipts = call(proc, 8, "receipt_list", {})
            assert receipts["chain_valid"] is True
            print(f"receipts OK; {receipts['count']} entries, chain valid")
            print("SMOKE PASSED")
        finally:
            proc.stdin.close()
            proc.terminate()


if __name__ == "__main__":
    main()
