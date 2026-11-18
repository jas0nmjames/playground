#!/usr/bin/env python3
"""Fold sources/raw/_downloads.jsonl into sources/manifest.csv.

    python3 -I sources/tools/finalize.py

For every row with downloads, fills downloaded_on, files, bytes (total) and sha256 (one per file, in
the same order as `files`), and sets status to `fetched`. ROW_INFO below holds what a person has to
judge: the vintage actually found, the terms of use, and notes (including why a row could not be
fetched). Rows not in the log keep status `to_fetch` unless ROW_INFO says otherwise.
"""
import csv
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES = os.path.dirname(HERE)
MANIFEST = os.path.join(SOURCES, "manifest.csv")
LOG = os.path.join(SOURCES, "raw", "_downloads.jsonl")

FED_WORK = "U.S. federal government work; no copyright in the U.S. (17 U.S.C. 105). Summarized, not copied from a terms page."
CLOUD_BLOCK = ("Publisher refuses requests from this cloud session (HTTP 403 'Access Denied' from the publisher's own server, "
               "tried 2026-11-18). Fetch from a home connection; not a sign-in or a form.")

# id: (actual_vintage, license_or_terms, notes, status override or None)
ROW_INFO = {
    "atus_tables": ("", FED_WORK, "BLS. " + CLOUD_BLOCK, None),
    "atus_eldercare": ("", FED_WORK, "BLS. " + CLOUD_BLOCK, None),
    "atus_microdata": ("", FED_WORK, "BLS. " + CLOUD_BLOCK, None),
    "dcpc": ("2025", "Federal Reserve Bank of Atlanta public data; cite the SDCPC. Summarized; see the codebook and atlantafed.org for terms.",
             "2025 data posted (target met): public CSV zip, data codebook, tables XLSX and the 2025 results report.", None),
    "shed": ("2025", "Federal Reserve Board public data; " + FED_WORK, "2025 public-use CSV zip and the 2025 codebook PDF.", None),
    "ssa_schedule_2027": ("", FED_WORK, "SSA. " + CLOUD_BLOCK, None),
    "federal_holidays_2027": ("2027", FED_WORK, "OPM page, the 2027 tab page and OPM's iCalendar file. Compiled to sources/derived/federal_holidays_2027.csv "
                              "by sources/tools/compile_holidays.py. Juneteenth, Independence Day, Christmas and New Year's Day 2028 all move; "
                              "New Year's Day 2028 is observed Friday 2027-12-31.", None),
    "snap_issuance": ("current (retrieved 2026-11-18)", "State agency pages; public information. Summarized.",
                      "Compiled to sources/derived/snap_issuance.csv: 8 states (ND all on the 1st; MO birth month and last name; IA last name; "
                      "GA client ID; MN and CA case number; IL individual ID; AR SSN). FNS's site now redirects to www.fna.usda.gov and its state "
                      "directory is built in JavaScript, so no national file. Tried and not used: TX and RI (403), NY (connection closed), "
                      "FL and VT (pages give no schedule), IN (page redirects to plain http), PA (page gives no schedule). "
                      "AR and CA state the rule but not the full digit-to-day map.", None),
    "irs_refund_timing": ("2026", FED_WORK, "2026 filing-season announcement and opening release (EITC/ACTC refunds available by March 2, 2026; "
                          "Where's My Refund dates by Feb. 21), the /refunds page (PATH hold to mid-February) and the 'get ready for 2027' "
                          "reminder. The 2027 opening announcement is not posted yet (normally early January).", None),
    "ftc_sentinel": ("", FED_WORK, "www.ftc.gov answers HTTP 404 to every page from this cloud session, the home page included; "
                     "looks like a block on cloud clients rather than a moved page. Fetch from a home connection.", None),
    "payday_ca_dfpi": ("2025", "California state publication. Summarized.", "2025 Annual Report of Payday Lending Activity (CDDTL), published August 2026.", None),
    "payday_title_tx_occc": ("CY2025 (plus 2026 Q1-Q2)", "Texas state publication. Summarized.",
                             "Credit Access Business reports: CY2025 annual state and MSA reports, 2025 Q1-Q4 state reports, and the newer "
                             "2026 Q1 and Q2 state reports.", None),
    "payday_cfpb": ("", FED_WORK, "consumerfinance.gov. " + CLOUD_BLOCK, None),
    "title_state_reports": ("", "Tennessee state publication.", "www.tn.gov. " + CLOUD_BLOCK, None),
    "ce_pumd": ("", FED_WORK, "BLS. " + CLOUD_BLOCK + " Check sizes before downloading: the Interview files can pass 1 GB unzipped.", None),
    "scf": ("2025", "Federal Reserve Board public data; " + FED_WORK,
            "2025 summary extract (CSV zip), full codebook (codebk2025.txt), the summary-extract program (bulletin.macro.txt) "
            "and the public historical tables XLSX.", None),
    "meps": ("2024", FED_WORK + " AHRQ asks users not to attempt to identify respondents.",
             "2024 full-year consolidated file (HC-256, released August 2026) and 2024 event files: prescribed medicines (HC-254A), "
             "ER visits (HC-254E), office-based visits (HC-254G), home health (HC-254H). MEPS offers no CSV; Stata (.dta) taken, "
             "with each file's documentation and codebook PDF.", None),
    "cbp": ("2023", FED_WORK, "2023 U.S. file (cbp23us.zip) and the record-layouts page. 2023 is the newest posted; no 2024 dataset page yet.", None),
    "fdic_unbanked": ("2023", FED_WORK, "2023 household-level analysis CSV (205 MB), the data dictionary (publisher's name 'metadata-2023', "
                      "a CSV) and the technical notes (PDF).", None),
    "irs_soi_eitc": ("TY2023 (SOI tables); TY2024 (EITC by state)", FED_WORK,
                     "SOI Table 2.5 (EITC by AGI) and Table 1.4 for TY2023; EITC Central's TY2024 claims by state (page moved to "
                     "irs.gov/tax-professionals/eitc-central/...); the 2026 filing-season statistics (tax professional vs self-prepared "
                     "e-file counts, all returns). No published table found on EITC returns by paid-preparer use.", None),
    "ffiec_call_reports": ("2025Q4-2026Q3", FED_WORK, "Call Reports, single period, tab delimited: 12/31/2025, 3/31/2026, 6/30/2026, "
                           "9/30/2026. Each zip holds every schedule including RI and RI-E. Fetched through the page's download form "
                           "(no sign-in).", None),
    "nyfed_hhdc": ("", "Federal Reserve Bank of New York; see newyorkfed.org terms of use.",
                   "The page builds its data links in JavaScript; the file path could not be found from this session. Download the "
                   "latest quarter's XLSX by hand.", None),
    "recs": ("2024 (v1)", FED_WORK, "Newer than the 2020 target: RECS 2024 public microdata v1 CSV, its codebook and the microdata guide.", None),
    "utility_disconnections": ("2024 (EIA); dashboard data not fetched", FED_WORK + " (EIA files). Dashboard: Indiana University Energy Justice Lab.",
                               "PARTIAL. The dashboard's state-month data sits inside an interactive app on another host, not as a file. "
                               "Took instead EIA's Residential Utility Disconnections Report (April 2026; about 15 million people had "
                               "electricity shut off in 2024) and its 2024 electric and natural-gas utility-level data, plus the "
                               "dashboard's technical documentation.", None),
    "eviction_lab": ("", "Eviction Lab terms (see evictionlab.org).", "evictionlab.org answers HTTP 403 to this session's client. Fetch from a home connection.", None),
    "ahs": ("2023 (v1.1)", FED_WORK, "2023 national PUF v1.1 CSV, version-control PDF and value-labels package. Codebook is an online tool only.", None),
    "oews": ("", FED_WORK, "BLS. " + CLOUD_BLOCK, None),
    "ncs_benefits": ("", FED_WORK, "BLS. " + CLOUD_BLOCK, None),
    "ndcp": ("", FED_WORK, "www.dol.gov. " + CLOUD_BLOCK, None),
    "snap_qc": ("FY2024", "USDA FNS data hosted by Mathematica; public. Summarized.", "FY2024 CSV zip (posted August 2026), FY2024 technical documentation and the FAQ.", None),
    "medicaid_renewals": ("Oct 2026 release (processing data); Oct 2024 final (renewal outcomes)",
                          "Public domain (data.medicaid.gov metadata: usa.gov/publicdomain/label/1.0).",
                          "CMS State Medicaid and CHIP Eligibility Processing Data (October 2026 release) and Updated Renewal Outcomes "
                          "(final, October 2024). Georgia Pathways enrollment reports not fetched: no Georgia Medicaid host tried this session.", None),
    "ntd": ("", FED_WORK, "www.transit.dot.gov. " + CLOUD_BLOCK, None),
    "food_access_atlas": ("2025 (SRAM); 2019 (atlas)", FED_WORK,
                          "Renamed: ERS now publishes the 2025 SNAP Authorized Retailer Access Map (SRAM) data, and the 2019 Food Access "
                          "Research Atlas as the Large Retailer Access Map (LRAM). Took both zips and the download page.", None),
    "rucc": ("2023", FED_WORK, "2023 codes, XLSX and CSV, plus the documentation page.", None),
    "cms_dialysis": ("", FED_WORK, "data.cms.gov. " + CLOUD_BLOCK, None),
    "naws": ("", FED_WORK, "www.dol.gov. " + CLOUD_BLOCK, None),
    "h2a_disclosure": ("", FED_WORK, "www.dol.gov. " + CLOUD_BLOCK, None),
    "nchs_vital": ("", FED_WORK, "www.cdc.gov. " + CLOUD_BLOCK, None),
    "irs_migration": ("2022-2023", FED_WORK, "State and county inflow and outflow CSVs and the users' guide.", None),
    "noaa_storm_events": ("", FED_WORK, "The bulk CSV directory (ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/) answered HTTP 503 on "
                          "every try on 2026-11-18. Retry later.", None),
    "ic3_elder": ("2025 (annual); 2023 (elder report)", FED_WORK,
                  "IC3 stopped the separate Elder Fraud Report after 2023; 2024-2025 elder figures are in the annual report and the "
                  "state pages. Took the 2025 annual report and the 2023 Elder Fraud Report.", None),
}


def main():
    log = OrderedDict()
    if os.path.exists(LOG):
        with open(LOG) as f:
            for line in f:
                e = json.loads(line)
                log.setdefault(e["id"], OrderedDict())[e["file"]] = e  # a re-download replaces the earlier entry
    with open(MANIFEST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    for r in rows:
        info = ROW_INFO.get(r["id"])
        got = log.get(r["id"])
        if got:
            entries = list(got.values())
            r["downloaded_on"] = max(e["downloaded_on"] for e in entries)
            r["files"] = ";".join(e["file"] for e in entries)
            r["bytes"] = str(sum(e["bytes"] for e in entries))
            r["sha256"] = ";".join(e["sha256"] for e in entries)
            r["status"] = "fetched"
        if info:
            vintage, terms, notes, status = info
            r["actual_vintage"], r["license_or_terms"] = vintage, terms
            if notes not in r["notes"]:
                r["notes"] = (r["notes"] + " | " if r["notes"] else "") + notes
            if status:
                r["status"] = status
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    by = {}
    for r in rows:
        by.setdefault(r["status"], []).append(r["id"])
    for k, v in sorted(by.items()):
        print("%-14s %2d  %s" % (k, len(v), ", ".join(v)))
    print("total bytes fetched: %s" % sum(int(r["bytes"] or 0) for r in rows))


if __name__ == "__main__":
    main()
