# SPACECARE: Phase 3 NASA Data Authenticity & Provenance Audit Report

**Date of Audit:** 2026-11-11  
**Project:** SPACECARE – NASA Astronaut Health Monitoring & Early Warning System  
**Auditor:** Quality & Scientific Data Integrity Engineering  
**Scope:** Review and independent verification of all NASA datasets, reference files, API integrations, measurement units, regulatory limits, and database provenance flags.

---

## Executive Summary Table

| Dataset | ID | Source Verified | Real Downloaded Records | Units Verified | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NASA OSDR Mars500 Epigenetics** | OSD-140 (GLDS-140) | Yes (`osdr.nasa.gov`) | No (Curated reference metadata) | Yes (Methylation $\beta$, timepoints) | **VERIFIED** |
| **NASA OSDR Cosmonaut IgM Repertoire** | OSD-316 (GLDS-316) | Yes (`osdr.nasa.gov`) | No (Curated reference metadata) | Yes (Clonotype counts, VDJ usage) | **VERIFIED** |
| **NASA OSDR Astronaut Hair Follicles** | OSD-174 (GLDS-174) | Yes (`osdr.nasa.gov`) | No (Curated reference metadata) | Yes (Microarray expression, qPCR) | **VERIFIED** |
| **NASA OSDR SANS Translaminar Model** | OSD-816 | Yes (`osdr.nasa.gov`) | No (Curated reference metadata) | Yes (RT-PCR, ERG amplitudes) | **VERIFIED** |
| **NASA OSDR Commercial Astronaut Blood** | OSD-943 (Ax-1) | Yes (`osdr.nasa.gov`) | No (Curated reference metadata) | Yes (DNA methylation $\beta$-values) | **VERIFIED** |
| **NASA RadLab ISS Live API Client** | `radlab/api` | Yes (`visualization.osdr.nasa.gov`) | Yes (When live API query succeeds) | Yes ($\mu\text{Gy/h}$, $\mu\text{Sv/h}$, flux) | **VERIFIED** |
| **NASA RadLab Local Reference Fixture**| `radlab_iss_dosimetry.json` | Yes (Calibrated to Liulin-5/DOSTEL) | No (Synthesized test fixture) | Yes ($\mu\text{Gy/h}$, $\mu\text{Sv/h}$, $\text{cm}^{-2}\text{sr}^{-1}\text{s}^{-1}$) | **PARTIALLY VERIFIED** |
| **NASA EDA Flight Environmental CSV** | `eda_iss_environment.csv` | Yes (ISS ECLSS engineering specs) | No (Synthesized test fixture) | Yes ($\text{psi}$, $\text{mmHg}$, $\%$, $^\circ\text{C}$) | **UNVERIFIED** *(as raw flight download)* |

---

## 1. Audit of NASA Reference Files

### A. `data/sample_nasa/osdr_human_studies.json`
- **Authenticity Assessment**: The studies listed represent real, verified NASA human spaceflight research investigations.
- **Data Origin**: These entries are **curated reference metadata profiles** summarizing peer-reviewed spaceflight publications and NASA OSDR repository records. They are **not raw sequencing data or unedited API payloads**.
- **Corrections Applied**:
  - Replaced provisional working DOIs with exact peer-reviewed journal DOIs (e.g. *iScience* `10.1016/j.isci.2022.104493` for OSD-140; *The FASEB Journal* `10.1096/fj.202001403RR` for OSD-316; *PLOS ONE* `10.1371/journal.pone.0150801` for OSD-174).
  - Explicitly updated `provenance_type` to `"CURATED_NASA_REFERENCE_METADATA"` and `verification_status` to `"VERIFIED"`.

### B. `data/sample_nasa/radlab_iss_dosimetry.json`
- **Authenticity Assessment**: The instrument names (Liulin-5, DOSTEL, TEPC), modules (US Lab, Columbus), and units ($\mu\text{Gy/h}$, $\mu\text{Sv/h}$) match official NASA RadLab documentation.
- **Data Origin**: The individual 4-hour interval records in this file were **not directly exported from the RadLab API**. They were constructed as a calibrated reference test fixture matching published Liulin-5 and DOSTEL observation ranges.
- **Corrections Applied**:
  - Changed classification to **PARTIALLY VERIFIED** (provenance: `REFERENCE_FIXTURE_DERIVED_FROM_PUBLISHED_DATA`).
  - Added explicit header metadata indicating that the file is an offline reference fixture rather than an official downloaded archive.

### C. `data/sample_nasa/eda_iss_environment.csv`
- **Authenticity Assessment**: The atmospheric parameters ($\text{CO}_2$ partial pressure in $\text{mmHg}$, total pressure in $\text{psi}$, temperature in $^\circ\text{C}$, relative humidity in $\%$) align with International Space Station Environmental Control and Life Support System (ECLSS) operational ranges.
- **Data Origin**: This CSV was **not downloaded from the official NASA EDA Data Tables portal**. It is a synthesized reference baseline fixture derived from published aerospace engineering specifications (NASA-STD-3001).
- **Corrections Applied**:
  - Status classified as **UNVERIFIED** as raw flight data.
  - Relabeled in code and UI as `"NASA ECLSS Engineering Baseline Reference Fixture"`.

---

## 2. Independent Audit of NASA OSDR Studies

Each of the five human spaceflight studies was independently verified against NASA repository records:

1. **OSD-140 (GLDS-140)**:
   - *Confirmed Title*: "Dynamic nature of epigenetic patterns observed during the Mars 520-d mission simulation"
   - *Subjects*: 6 healthy human volunteers during the 520-day Mars500 ground isolation mission.
   - *Assay*: Illumina HumanMethylation450 BeadChip.
   - *Publication*: Hou et al., *iScience* (2022), DOI: [10.1016/j.isci.2022.104493](https://doi.org/10.1016/j.isci.2022.104493).
   - *Public Access*: Fully public metadata and methylation matrix.

2. **OSD-316 (GLDS-316)**:
   - *Confirmed Title*: "Plasticity of the human IgM repertoire in response to a long-term spaceflight"
   - *Subjects*: Cosmonauts aboard the International Space Station (Expeditions 64 and 129 days on orbit).
   - *Assay*: Illumina MiSeq high-throughput sequencing of immunoglobulin M heavy chain V(D)J repertoires.
   - *Publication*: Buchheim et al., *The FASEB Journal* (2020), DOI: [10.1096/fj.202001403RR](https://doi.org/10.1096/fj.202001403RR).
   - *Public Access*: Fully public (NCBI BioProject PRJNA627324).

3. **OSD-174 (GLDS-174)**:
   - *Confirmed Title*: "Effects of a Closed Space Environment on Gene Expression in Hair Follicles of Astronauts in the International Space Station"
   - *Subjects*: 10 astronauts across ISS Expeditions 20, 21, and 22.
   - *Assay*: Affymetrix GeneChip Human Genome U133 Plus 2.0 & real-time qPCR.
   - *Publication*: Terada et al., *PLOS ONE* (2016), DOI: [10.1371/journal.pone.0150801](https://doi.org/10.1371/journal.pone.0150801).
   - *Public Access*: Fully public omics data.

4. **OSD-816**:
   - *Confirmed Title*: "The ex vivo human translaminar autonomous system to study spaceflight associated neuro-ocular syndrome pathogenesis (Retina, RT-PCR and electroretinography)"
   - *Subjects*: Human retinal tissue under translaminar hydrostatic pressure gradient.
   - *Assay*: RT-PCR, electroretinography, tight-junction degradation assays.
   - *Public Access*: Open science repository entry.

5. **OSD-943**:
   - *Confirmed Title*: "Longitudinal transcriptomic and epigenetic analysis in astronauts reveals dynamic immune response to spaceflight [DNA methylation]"
   - *Subjects*: 4 astronauts from the Axiom Space Ax-1 commercial mission to ISS (17 days on orbit, April 2022).
   - *Assay*: Illumina Infinium Human MethylationEPIC BeadChip.
   - *Source Accession*: GSE276323, DOI: [10.26030/dtc0-6s93](https://doi.org/10.26030/dtc0-6s93).
   - *Public Access*: Processed methylation data public; raw genomic sequences gated by controlled access protocols.

---

## 3. Independent Audit of NASA RadLab & Radiation Services

### A. API Specification & Query Parameters
- Base endpoint verified: `https://visualization.osdr.nasa.gov/radlab/api`
- Query parameters verified against official NASA RadLab Data API documentation:
  - `spacecraft=ISS`, `trajectory=LEO`, `module`, `instrument`, `absorbed_dose_rate`, `dose_equivalent_rate`, `flux`.
  - Mutually exclusive syntax rule verified (simple key-value vs boolean expression).

### B. Cumulative Dose Calculation Audit
- **Previous Implementation**: Approximated cumulative dose by multiplying hourly rate by duration:
  $$\text{Cumulative Dose (mSv)} \approx \frac{\text{Rate } (\mu\text{Sv/h}) \times \text{Hours}}{1000}$$
- **Scientific Audit Finding**:
  - The quantity measured by the dosimeters (e.g. Liulin-5, DOSTEL) is **ambient dose equivalent rate** $dH^*(10)/dt$ in $\mu\text{Sv/hour}$ or **absorbed dose rate** $D$ in $\mu\text{Gy/hour}$.
  - This is an **operational ambient field measurement**, NOT a calculation of whole-body **Effective Dose ($E$)** under radiation protection standards.
  - Full effective dose ($E = \sum_T w_T H_T$) requires tissue weighting factors ($w_T$) and particle transport modeling (HZETRN).
- **Correction Applied**:
  - Documented in `src/nasa_data/radiation_service.py` that cumulative dose is an **ambient operational dose equivalent approximation $H^*(10)$**, and not a clinical effective dose calculation.

### C. Regulatory Standards & Thresholds Audit
- **600 mSv Career Limit**:
  - Cites **NASA-STD-3001 Volume 1, Rev B** (*Standard for Spaceflight Human-System Standard: Crew Health*), Section 3.2.1.
  - NASA established a universal **600 mSv career effective dose limit** designed to ensure the Risk of Exposure-Induced Death (REID) does not exceed 3% at the 95% confidence level.
- **100 mSv 30-Day Limit**:
  - Identified as an **NCRP Report No. 132** short-term guideline for preventing non-cancer deterministic risks (blood-forming organ advisory), rather than a statutory standalone career rule.
- **50 μSv/h SAA Heuristic**:
  - Identified as an **operational telemetry threshold** representing entry into the South Atlantic Anomaly, not a statutory regulatory ceiling.

### D. Database Provenance Audit
- Corrected `sync_radlab_records_to_db()`:
  - If records are verified live API responses (`is_real_nasa_data = True`), they are persisted with `is_simulated = 0`.
  - If records originate from the local calibrated reference fixture, they are persisted with `is_simulated = 1`.

---

## 4. Independent Audit of NASA Environmental Data Application (EDA)

- **Source Portal**: [https://visualization.osdr.nasa.gov/eda/](https://visualization.osdr.nasa.gov/eda/)
- **Nature of Data**: EDA hosts tabular records (CSV/TSV) for ISS habitat payloads and cabin atmosphere. It does **not** provide an open streaming JSON API.
- **Audit Finding**: `data/sample_nasa/eda_iss_environment.csv` is a **calibrated reference fixture based on published ISS ECLSS engineering specifications**, not an unedited raw download from EDA.
- **Correction Applied**:
  - Updated `src/nasa_data/eda_client.py` and `pages/2_🛰️_ISS_Environment.py` to label the data as `"NASA ECLSS Engineering Baseline Reference Fixture (NASA-STD-3001)"`.
  - Added an explicit disclaimer stating that values represent engineering tolerances rather than live-downloaded flight telemetry.

---

## 5. UI Labels & Database Provenance Verification

All user-facing views were audited for strict provenance transparency:

1. **`pages/3_🔬_NASA_OSDR_Research.py`**:
   - Curated reference cards are labeled: `[CURATED NASA OSDR STUDY METADATA]`.
   - Live query responses are labeled: `[LIVE NASA OSDR API RESPONSE]`.
   - Persistent notice clarifies that research omics data is distinct from real-time wearable vital signs.

2. **`pages/4_☢️_Space_Radiation.py`**:
   - Displays `[LIVE NASA RADLAB API RESPONSE]` only when an active API query succeeds.
   - When displaying local reference fixtures, displays `[RADLAB CALIBRATED REFERENCE DOSIMETRY FIXTURE]`.
   - Cites **NASA-STD-3001 Volume 1, Rev B** for career permissible exposure limits.

3. **`pages/2_🛰️_ISS_Environment.py`**:
   - The comparison table is badged as `[NASA ECLSS ENGINEERING BASELINE REFERENCE (NASA-STD-3001)]`.

4. **SQLite Database (`data/spacecare.db`)**:
   - `is_simulated = 0` is strictly reserved for verified live NASA API payloads.
   - All simulated telemetry and local test fixtures are flagged with `is_simulated = 1`.

---

## 6. Verification Test Results

Following the corrections, the full test suite was executed:
- **Total Tests**: 25 tests across all modules.
- **Passed**: 25 / 25 (`100%`).
- **Failures / Errors**: 0.

### Conclusion & Sign-Off
Phase 3 data assets are now fully audited, transparently attributed, and scientifically documented. Manually curated examples and reference fixtures are accurately labeled and never presented as raw downloaded flight telemetry.
