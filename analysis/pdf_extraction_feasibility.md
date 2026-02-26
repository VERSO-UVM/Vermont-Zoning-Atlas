# PDF → XML → GeoJSON Extraction Pipeline: Feasibility Study

**Date:** 2026-02-26
**Analyst:** Claude Code
**Scope:** Automated extraction of zoning regulations from `data/Town_Bylaw_Text/` PDFs into structured XML, with downstream update of `data/State_of_Vermont/` GeoJSON files.

---

## Context

Each Vermont municipality's zoning bylaw PDF (e.g., `Addison_Bridport_Text_eff08222006.pdf`) is the source document from which the corresponding GeoJSON (e.g., `Addison_Bridport.geojson`) was manually coded. The goal is to automate or semi-automate that translation using text extraction + regex + LLM assistance.

**Reference PDF examined in depth:** `Addison_Bridport_Text_eff08222006.pdf`
**Reference GeoJSON:** `data/State_of_Vermont/Addison_Bridport.geojson`

---

## Dataset Overview

Audited all 208 files in `data/Town_Bylaw_Text/` using `pypdf`:

| Category | Count | % |
|----------|-------|---|
| Text-based PDFs (directly extractable) | 189 | 91% |
| Scanned/image PDFs (need OCR) | 17 | 8% |
| DOC files (need conversion) | 1 | <1% |
| Errors | 1 | <1% |
| **Total** | **208** | |

### Scanned PDFs requiring OCR
```
Addison_Addison_Text_eff11272007.pdf
Addison_Ferrisburgh_Text_eff03022021.pdf
Addison_Goshen_Text_eff04112008.pdf
Addison_Salisbury_Text_eff05122015.pdf
Bennington_Readsboro_Text_eff06232021.pdf
Bennington_Stamford_Text_eff10232020.pdf
Bennington_Woodford_Text_eff07152020.pdf
Franklin_Swanton_Text_eff06262001.pdf
Lamoille_Morristown_Text_eff11062023.pdf
Orleans_NewportTown_Text_eff05032018.pdf
Orleans_Westmore_Text_eff111020.pdf
Rutland_Castleton_Text_eff06282021.pdf
Rutland_Clarendon_Text_eff02142011.pdf
Washington_Woodbury_Text_eff03242006.pdf
Windsor_Plymouth_Text_eff06112024.pdf
Windsor_Rochester_Text_eff12182023.pdf
Windsor_WoodstockVillage_Text_eff04082014.pdf
```

### DOC files
```
Addison_Orwell_Text_eff03052019.doc
```
Convert with LibreOffice CLI (`soffice --convert-to pdf`) or python-docx.

---

## Bridport PDF Structure Analysis

### File characteristics
- **Pages:** 59
- **Size:** 412 KB
- **Extractable text:** ~156,000 chars / ~22,000 words
- **Fully text-based:** Yes (no OCR needed)

### Document structure
Bridport (and most VT bylaws) follow this layout:

```
Article I   – Preamble, definitions
Article II  – Permitted uses per district (the use tables)
Article III – Administration (permits, appeals)
Article IV  – General regulations (flood hazard, signs, etc.)
Article V   – Nonconformities
...
Article IX  – ZONING DISTRICTS  ← key section
  Section 900:  Village District (V-1)
    A. Objectives
    B. Permitted Uses / Conditional Uses
    C. District Regulations → see Section 901A
  Section 901A: Specific Regulations for V-1 District
    Lot Area Minimum             1 acre
    Lot Frontage Minimum         100 feet
    Front Yard Setback           75 feet
    Rear Yard Minimum            25 feet
    Side Yard Minimum            25 feet
    Building Area Max Coverage   15 percent
  Section 902:  Residential District (R-2)
  Section 902A: Specific Regulations for R-2 District
  ... (one pair per district)
```

### Districts found in Bridport PDF vs GeoJSON

| PDF District | Code | GeoJSON Match | Min Lot | Frontage | Front Setback |
|---|---|---|---|---|---|
| Village District | V-1 | Village District | 1 ac | 100 ft | 75 ft |
| Residential District | R-2 | Residential District | 2 ac | 200 ft | 100 ft |
| Residential Agricultural District | R-5 | Residential Agricultural District | 5 ac | 400 ft | 100 ft |
| Neighborhood Commercial District | NC | Neighborhood Commercial District | 1 ac | 150 ft | 100 ft |
| Conservation District | CON-25 | Conservation District | 25 ac | 700 ft | 100 ft |
| Shoreland Planned Residential District | SPRD-2 | Shoreland Planned Residential District | 2 ac | 200 ft | 100 ft |

All values confirmed to match the existing GeoJSON — the bylaw is the correct source.

---

## Canonical Field Mapping

The following canonical fields can be extracted from the dimensional regulation tables:

| Canonical Field | PDF Source Pattern | Confidence |
|---|---|---|
| `F1F_Min_Lot_Size` | "Lot Area Minimum X acres" | High |
| `F1F_Frontage` | "Lot Frontage Minimum X feet" | High |
| `F1F_Front_Setback` | "Front Yard Setback X feet" | High |
| `F1F_Rear_Setback` | "Rear Yard Minimum X feet" | High |
| `F1F_Side_Setback` | "Side Yard Minimum X feet" | High |
| `F1F_Max_Height` | "Building Height Maximum X feet" | High |
| `F1F_Max_Lot_Building_Coverage` | "Building Area Maximum X percent" | High |
| `F1F_Allowance` | Parse "By Right Uses" / "Conditional Uses" lists | Medium (needs LLM) |
| `F2F_Allowance` | Same — look for "two-family" or "duplex" | Medium (needs LLM) |
| `F3F_Allowance` | Same — look for "multi-family" / "3-unit" | Medium (needs LLM) |
| `F4F_Allowance` | Same — look for "multi-family" / "4+ unit" | Medium (needs LLM) |
| `ADU_Allowance` | Search "accessory dwelling unit" in uses | Medium |
| `ADU_Max_Size_in_sq_ft` | "ADU maximum X square feet" | Medium |
| `ADU_Owner_Occupancy_Required` | Prose interpretation | Low (LLM) |

Fields **not** reliably extractable from bylaws alone:
- `GEO_ID`, `FIPS6`, `GIS_ID` — administrative, from external lookup
- `District_Mapped`, `Overlay_District` — from GIS file itself
- `Shape_Length`, `Shape_Area` — calculated from geometry
- Parking minimums — often in a separate general section, not district tables

---

## Recommended Pipeline Architecture

```
data/Town_Bylaw_Text/*.pdf
         │
         ├─ Text PDF (91%) ──► pypdf.PdfReader.extract_text()
         └─ Scanned (9%)  ──► pytesseract / cloud OCR (AWS Textract recommended)
                                        │
                                   Raw text string
                                        │
                          ┌─────────────┴─────────────┐
                    Regex parser                  LLM (Claude API)
                    (dimensions,                  (use classifications,
                     numbers,                      ambiguous language,
                     units)                        cross-references)
                          └─────────────┬─────────────┘
                                   Structured XML
                                        │
                              District name fuzzy-match
                              (norm: lowercase, strip spaces)
                                        │
                            Update GeoJSON null fields
                            (only fill where currently null)
```

### Proposed XML schema

```xml
<municipality name="Bridport" county="Addison"
              bylaw_date="2006-08-22" source_pdf="Addison_Bridport_Text_eff08222006.pdf">
  <district name="Village District" code="V-1">
    <uses>
      <use canonical="F1F_Allowance" status="Permitted"
           source="Section 900B: By Right Uses: 1. One- or two-family dwelling"/>
      <use canonical="F2F_Allowance" status="Permitted"
           source="Section 900B: By Right Uses: 1. One- or two-family dwelling"/>
      <use canonical="F3F_Allowance" status="Permitted"
           source="Section 900B: By Right Uses: 2. Multi-family dwelling"/>
      <use canonical="ADU_Allowance" status="Permitted"
           source="Section 900B: By Right Uses: 7. Accessory dwelling unit"/>
    </uses>
    <regulations>
      <field canonical="F1F_Min_Lot_Size"              value="1"   unit="acres"   source="Section 901A"/>
      <field canonical="F1F_Frontage"                  value="100" unit="feet"    source="Section 901A"/>
      <field canonical="F1F_Front_Setback"             value="75"  unit="feet"    source="Section 901A"/>
      <field canonical="F1F_Rear_Setback"              value="25"  unit="feet"    source="Section 901A"/>
      <field canonical="F1F_Side_Setback"              value="25"  unit="feet"    source="Section 901A"/>
      <field canonical="F1F_Max_Lot_Building_Coverage" value="15"  unit="percent" source="Section 901A"/>
    </regulations>
  </district>
</municipality>
```

---

## Challenges and Mitigations

| Challenge | Severity | Mitigation |
|---|---|---|
| Structure varies across 208 files | High | Pattern library with per-file overrides; LLM fallback |
| "Multi-family" maps ambiguously to F3F vs F4F | Medium | LLM prompt with field definitions; flag for review |
| District PDF names ≠ GIS district names | Medium | Fuzzy match (normalize + token overlap); manual override file |
| ADU rules in general sections, not district tables | Medium | Full-document search for "accessory dwelling" + surrounding context |
| Setbacks sometimes in centerline vs lot line | Medium | Extract both; flag discrepancy for review |
| Cross-references ("see Section 409") | Medium | Follow references within same document |
| Scanned PDFs (17 files) | Low | pytesseract for free; AWS Textract for higher accuracy |
| Zoning map images → spatial polygons | Very High | **Not feasible to automate** — requires manual digitization |
| Units: acres vs sq ft, feet vs stories | Low | Unit normalization in post-processing |

---

## Feasibility Summary

| Task | Feasibility | Est. Accuracy |
|---|---|---|
| Extract text from 189 text PDFs | ✅ Ready now | ~100% |
| OCR 17 scanned PDFs | ✅ Feasible | 85–95% |
| Parse dimensional standards | ✅ Feasible | 80–90% |
| Classify permitted/conditional/prohibited uses | ✅ With LLM | 85–95% |
| Extract ADU rules | ⚠️ Partial | 60–75% |
| Extract multifamily (F3F/F4F) rules | ⚠️ Partial | 65–80% |
| Match to GIS district names | ⚠️ Partial | 85–95% |
| Extract zoning map geometry | ❌ Not feasible | — |

**Overall:** A well-built pipeline could auto-populate **60–70% of canonical fields** for the 189 text-based PDFs with high confidence, flagging the rest for human review. This represents a substantial reduction in manual data entry effort.

---

## Suggested Next Steps

1. **Proof of concept on Bridport** — build `scripts/extract_bylaw.py` that extracts and validates against the known GeoJSON values (ground truth already exists).
2. **Pattern library** — test on 10–15 structurally diverse PDFs to identify the most common regulation table formats and build a reusable parser.
3. **LLM integration** — use Claude API with a structured prompt to classify uses from the "Permitted Uses" / "Conditional Uses" sections, returning canonical field values.
4. **XML output** — write validated extractions to `analysis/bylaw_xml/County_Town.xml` for review before applying to GeoJSON.
5. **GeoJSON updater** — script that reads the XML and fills null fields in the corresponding GeoJSON (never overwriting existing values without a flag).
6. **OCR pipeline** — handle the 17 scanned PDFs last, after the text pipeline is proven.

### Libraries needed
```
pip install pypdf pdfminer.six          # already installed
pip install pytesseract pillow          # for scanned PDFs
pip install anthropic                   # for LLM use classification
pip install python-docx                 # for the .doc file
```

---

## Files Referenced

| File | Role |
|---|---|
| `data/Town_Bylaw_Text/Addison_Bridport_Text_eff08222006.pdf` | Reference PDF examined |
| `data/State_of_Vermont/Addison_Bridport.geojson` | Reference GeoJSON (ground truth) |
| `analysis/canonical_fields.csv` | Target field schema |
| `data/municipal_geoid_county_rpc_fips.csv` | Municipality → county/RPC lookup |
| `scripts/merge_state_to_rpc.py` | Compiles town GeoJSON → RPC files |
