#!/usr/bin/env python3
"""Fold sources/download_log.jsonl into sources/manifest.csv.

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
LOG = os.path.join(SOURCES, "download_log.jsonl")

FED_WORK = "U.S. federal government work; no copyright in the U.S. (17 U.S.C. 105). Summarized, not copied from a terms page."

# id: (actual_vintage, license_or_terms, notes, status override or None)
ROW_INFO = {
    "atus_tables": ("2025", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. ATUS 2025 annual tables A-1, A-2, A-3, A-8 and A-9 (PDF; no XLSX offered).", None),
    "atus_eldercare": ("2023-24 (released 2025-09-25)", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. The full news release PDF, which holds tables 1-9.", None),
    "atus_microdata": ("2025; 2003-2025 multi-year", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. 2025 respondent, roster, activity, activity summary, who and eldercare roster files; 2003-2025 respondent, roster, activity, summary, who and ATUS-CPS files; 2025 and 2003-2025 data dictionaries, the 2025 coding lexicon and the user guide. Not taken: replicate weights (293 MB multi-year), case and call history.", None),
    "dcpc": ("2025", "Federal Reserve Bank of Atlanta public data; cite the SDCPC. Summarized; see the codebook and atlantafed.org for terms.",
             "2025 data posted (target met): public CSV zip, data codebook, tables XLSX and the 2025 results report.", None),
    "shed": ("2025", "Federal Reserve Board public data; " + FED_WORK, "2025 public-use CSV zip and the 2025 codebook PDF.", None),
    "ssa_schedule_2027": ("2027", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. Schedule of Social Security Benefit Payments 2027 (EN-05-10031).", None),
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
    "ftc_sentinel": ("2024 (no 2025 Data Book posted)", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. Consumer Sentinel Network Data Book 2024 PDF and its CSV data files. www.ftc.gov answers HTTP 404, not 403, to the script. Explore Data downloads live on FTC's Tableau Public profile, another host, so not taken.", None),
    "payday_ca_dfpi": ("2025", "California state publication. Summarized.", "2025 Annual Report of Payday Lending Activity (CDDTL), published August 2026.", None),
    "payday_title_tx_occc": ("CY2025 (plus 2026 Q1-Q2)", "Texas state publication. Summarized.",
                             "Credit Access Business reports: CY2025 annual state and MSA reports, 2025 Q1-Q4 state reports, and the newer "
                             "2026 Q1 and Q2 state reports.", None),
    "payday_cfpb": ("2014", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. CFPB Data Point: Payday Lending (March 2014).", None),
    "title_state_reports": ("2026", "Tennessee state publication. Summarized.", "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. Tennessee TDFI 2026 Report on the Title Pledge Industry (biennial). Other states not tried.", None),
    "ce_pumd": ("2025", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. CE PUMD 2025 Interview and Diary CSV zips (40 MB and 6 MB) and the Interview/Diary data dictionary XLSX. Newer than the 2024 option.", None),
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
    "nyfed_hhdc": ("2026 Q3", "Federal Reserve Bank of New York; see newyorkfed.org terms of use. Summarized.", "Paths found on the CMD Data Bank page (the HHDC page builds its links in JavaScript); fetched by script: 2026 Q3 report data XLSX, the 2026 Q3 report PDF and household debt by state (2003-2025).", None),
    "recs": ("2024 (v1)", FED_WORK, "Newer than the 2020 target: RECS 2024 public microdata v1 CSV, its codebook and the microdata guide.", None),
    "utility_disconnections": ("2024 (EIA); dashboard data not fetched", FED_WORK + " (EIA files). Dashboard: Indiana University Energy Justice Lab.",
                               "PARTIAL. The dashboard's state-month data sits inside an interactive app on another host, not as a file. "
                               "Took instead EIA's Residential Utility Disconnections Report (April 2026; about 15 million people had "
                               "electricity shut off in 2024) and its 2024 electric and natural-gas utility-level data, plus the "
                               "dashboard's technical documentation.", None),
    "eviction_lab": ("weekly 2020-2021; monthly through latest (ETS v4.0)", "Eviction Lab, Princeton University; free to use with the citation it gives (Hepburn et al., Eviction Tracking System: Version 4.0, 2026). Summarized.", "Weekly all-sites and all-states files (2020-2021) and the data dictionary fetched by script from the Lab's own download bucket (eviction-lab-data-downloads.s3.amazonaws.com); the current all-sites and all-states monthly CSVs saved in a browser (evictionlab.org refuses the script). Current weekly data is published per site only, not as one national file.", None),
    "ahs": ("2023 (v1.1)", FED_WORK, "2023 national PUF v1.1 CSV, version-control PDF and value-labels package. Codebook is an online tool only.", None),
    "oews": ("May 2025", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. OEWS May 2025 national (oesm25nat.zip) and national industry-specific (oesm25in4.zip) XLSX zips.", None),
    "ncs_benefits": ("March 2026", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. Employee Benefits in the United States, March 2026 (tables zip). Newer than the 2025 target.", None),
    "ndcp": ("2008-2022", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. National Database of Childcare Prices 2008-2022 county file (NDCP2022.xlsx) and the 2024 technical report. 2022 is the newest county-level year.", None),
    "snap_qc": ("FY2024", "USDA FNS data hosted by Mathematica; public. Summarized.", "FY2024 CSV zip (posted August 2026), FY2024 technical documentation and the FAQ.", None),
    "medicaid_renewals": ("Oct 2026 release (processing data); Oct 2024 final (renewal outcomes)",
                          "Public domain (data.medicaid.gov metadata: usa.gov/publicdomain/label/1.0).",
                          "CMS State Medicaid and CHIP Eligibility Processing Data (October 2026 release) and Updated Renewal Outcomes "
                          "(final, October 2024). Georgia Pathways enrollment reports not fetched: no Georgia Medicaid host tried this session.", None),
    "ntd": ("2025 annual; monthly through Sep 2026", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. 2025 annual database: agency information, agency mode/type of service, fare revenues; complete monthly ridership through September 2026 (with adjustments and estimates). Newer than the 2024 target.", None),
    "food_access_atlas": ("2025 (SRAM); 2019 (atlas)", FED_WORK,
                          "Renamed: ERS now publishes the 2025 SNAP Authorized Retailer Access Map (SRAM) data, and the 2019 Food Access "
                          "Research Atlas as the Large Retailer Access Map (LRAM). Took both zips and the download page.", None),
    "rucc": ("2023", FED_WORK, "2023 codes, XLSX and CSV, plus the documentation page.", None),
    "cms_dialysis": ("updated 2026-10-22", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. Dialysis Facility - Listing by Facility (DFC_FACILITY_2.csv), from the Provider Data Catalog API metadata.", None),
    "naws": ("1989-2022", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. NAWS public data in CSV (both parts: NAWS_A2E1103 and NAWS_F2Y1103), the 1989-2022 codebook and the introduction to analyzing the public data.", None),
    "h2a_disclosure": ("FY2026 Q4 and FY2025 Q4", FED_WORK, "Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. H-2A disclosure data for FY2026 (newer than the FY2025 target) and FY2025, with the FY2026 record layout. Addendum files not taken.", None),
    "nchs_vital": ("2000-2024", FED_WORK, "PARTIAL. Saved in a browser on 2026-11-19 (the publisher's server refuses scripted requests by user agent, from home too) and logged with fetch.py record. National marriage and divorce rates 2000-2024 and state marriage and divorce rates (XLSX). Natality and mortality summaries not yet located or taken.", None),
    "irs_migration": ("2022-2023", FED_WORK, "State and county inflow and outflow CSVs and the users' guide.", None),
    "noaa_storm_events": ("2015-2025 (files compiled 2026-03-23 and 2026-11-18)", FED_WORK, "StormEvents_details CSV.gz for 2015-2025 and the bulk CSV format document, fetched by script from ncei.noaa.gov (the 503s of 2026-11-18 have cleared).", None),
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
            base = r["notes"].split("Log: ")[0].rstrip(" |")   # the manifest's own note; the log part is rebuilt every run
            r["notes"] = (base + " | " if base else "") + "Log: " + notes
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
