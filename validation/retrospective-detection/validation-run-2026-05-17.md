---
type: validation-run
project: master-thesis
date: 2026-05-17
status: completed
dataset: 10 hand-picked ministerial letters — 5 positive (signal) + 5 negative (non-signal)
tags:
  - validation
  - experiments
---

# Retrospective Signal Detection — Validation Run 2026-05-17

## Goal

Provide empirical evidence for the **feasibility half of RQ6**: *"To what extent is the proposed pipeline design feasible, and aligned with expert expectations for horizon scanning in the legal domain?"*

This run addresses feasibility only. The "aligned with expert expectations" dimension of RQ6 requires a separate expert evaluation (not yet done). This run also surfaces technical assumptions and risks relevant to **RQ5**: *"What assumptions, risks, and ethical considerations affect the validity of using LLMs for early-signal detection in legislative documents?"*

Ten documents were selected from five laws that have already entered into force. For each law, one *positive case* (the earliest ministerial letter with a clear legislative commitment) and one *negative case* (a letter from the same dossier without any commitment) were identified manually. The pipeline was run on all ten letters as if operating in real time.

**Evaluation criteria (maps to Chapter 6 in thesis):**
1. **Recall** — does the pipeline classify the 5 signal letters as relevant?
2. **Precision** — does the pipeline discard the 5 non-signal letters?
3. **Element completeness** — how fully does it populate the 8-element Van Kralingen norm frame on the positive cases?
4. **Certainty calibration** — does the assigned certainty level match the nature of the signal?
5. **Lead time** — what is the gap between signal detection and the MvT date?
6. **Operational feasibility** — runtime per document and token cost per document (separate task — see below)

> **Gap vs. RQ6:** Expert alignment is not assessed here. To fully answer RQ6, a structured expert review of the 5 positive outputs is still needed.
> **Gap vs. RQ5:** Ethical considerations (automation bias, accountability, transparency) are not tested by this run and must be addressed separately in Chapter 6.

---

## Dataset

**10 documents — 5 positive (signal) + 5 negative (non-signal) — manually curated**

Full selection methodology, backtracking chains, and signal text: `Code sprint/validation_cases.md`

### Positive cases (expected: relevant = true)

| # | Law | Signal letter | Signal date | MvT date | Lead (months) | MvT |
|---|-----|--------------|-------------|----------|---------------|-----|
| P1 | Wet goed verhuurderschap | 27 926, nr. 337 — "Uitkomst aanpak goed verhuurderschap" | 2021-02-22 | 2022-06-07 | 16 | [36 130 nr. 3](https://zoek.officielebekendmakingen.nl/kst-36130-3.html) |
| P2 | Wet toekomst pensioenen | 32 043, nr. 457 — "Principeakkoord vernieuwing pensioenstelsel" | 2019-06-05 | 2022-03-29 | 33 | [36 067 nr. 3](https://zoek.officielebekendmakingen.nl/kst-36067-3.html) |
| P3 | Wet inburgering 2021 | 32 824, nr. 223 — "Hoofdlijnen veranderopgave inburgering" | 2018-07-02 | 2020-06-03 | 23 | [35 483 nr. 3](https://zoek.officielebekendmakingen.nl/kst-35483-3.html) |
| P4 | Wet Wtta | 29 544, nr. 1021 — "Technische uitwerking advies Commissie Regulering van werk" | 2020-07-15 | 2023-10-06 | 39 | [36 446 nr. 3](https://zoek.officielebekendmakingen.nl/kst-36446-3.html) |
| P5 | Wet franchise | 31 311, nr. 206 — "Stand van zaken regelgeving Franchise" | 2018-05-23 | 2020-02-10 | 21 | [35 392 nr. 3](https://zoek.officielebekendmakingen.nl/kst-35392-3.html) |

Document IDs:
- P1: `088132e5-f6bd-4124-a5ce-f1705be36e9a`
- P2: `f072ca19-05b9-4af1-a895-d5020876fe78`
- P3: `9dac5c86-862b-4e00-962a-4e5168218a3e`
- P4: `3b7e0412-8e5a-4b81-902e-b17e01657627`
- P5: `911c7082-b68b-4d73-9c80-16c2419a3259`

### Negative cases (expected: relevant = false)

Hard negatives drawn from the same dossiers — same document type, same policy domain, no legislative commitment.

| # | Dossier | Letter | Date | Why negative |
|---|---------|--------|------|--------------|
| N1 | 27 926 | nr. 326 — "Stand van zaken bij de Huurcommissie" | 2020-07-02 | Operational update on rent tribunal; no legislative intent |
| N2 | 29 544 | nr. 970 — "Rapport Commissie Borstlap" | 2020-01-23 | Transmits third-party report; no government intent |
| N3 | 29 544 | nr. 1002 — "Uitkomsten uitzendonderzoeken" | 2020-04-06 | Sends research studies; defers response |
| N4 | 31 311 | nr. 186 — "Evaluatie fiscale ondernemerschapsregelingen" | 2017-05-18 | Transmits evaluation report; caretaker cabinet, no response given |
| N5 | 32 824 | nr. 50 — "Ontwikkelingen op het gebied van de inburgeringsexamens" | 2014-03-11 | Exam procurement and administration; no regulatory commitment |

Document IDs:
- N1: `552b83c2-67ac-4f4c-8ae5-96abb482cbdf`
- N2: `349df7ce-d2a8-405d-a099-5ed5c6c5cdf3`
- N3: `6b96d047-d7f5-4909-9597-360f6a527a95`
- N4: `bf392419-e4be-4725-8580-b83d775a787b`
- N5: `9858d519-158f-4497-8652-c3a9c24d4d70`

All documents verified on 2026-05-17.

**Note on negative case selection:** Selecting clean negatives from the same dossiers turned out to be non-trivial. Several initial candidates were discarded after reading them: the original selections for N1, N4, and N5 all contained forward-looking language that meets the signal criteria (explicit statutory anchoring announcements). The final five were chosen only after text verification.

---

## Configuration

| Parameter | Value |
|-----------|-------|
| LLM model (all stages) | `claude-sonnet-4-6` (via AWS Bedrock, region `eu`) |
| Profile version | `v1-2026-04-20` |
| Provider | AWS Bedrock (`LLM_PROVIDER=bedrock`) |
| Chunking | Fixed-size text split (no overlap) |
| Gold completeness threshold | ≥ 5 (chunks below discarded) |
| Stages run | classifier → silver → gold → synthesis |
| DB | PostgreSQL 16 (Docker, clean slate) |
| Run date | 2026-05-17 |

---

## Results

### Headline metrics

| Metric | Value |
|--------|-------|
| Recall (TP / P) | **1.00** (5/5) |
| Precision (TP / TP+FP) | **0.62** (5/8) |
| TP | 5 |
| FP | 3 |
| TN | 2 |
| FN | 0 |

### Per-document results

| # | Label | Expected | Classifier | Match | Silver | Gold | Discarded | Elements |
|---|-------|----------|------------|-------|--------|------|-----------|----------|
| 1 | P1 | signal | signal | ✓ | 9 | 9 | 0 | 8/8 |
| 2 | P2 | signal | signal | ✓ | 33 | 33 | 0 | 8/8 |
| 3 | P3 | signal | signal | ✓ | 24 | 22 | 1 | 8/8 |
| 4 | P4 | signal | signal | ✓ | 2 | 1 | 1 | 7/8 |
| 5 | P5 | signal | signal | ✓ | 2 | 1 | 1 | 7/8 |
| 6 | N1 | discard | signal | ✗ | — | — | — | — |
| 7 | N2 | discard | signal | ✗ | — | — | — | — |
| 8 | N3 | discard | signal | ✗ | — | — | — | — |
| 9 | N4 | discard | discard | ✓ | 0 | 0 | 0 | — |
| 10 | N5 | discard | discard | ✓ | 0 | 0 | 0 | — |

Note on N3: the classifier returned `relevant = true` (FP), but the gold stage discarded every chunk (completeness score < 5). No synthesis record was produced. This is counted as a classifier-level FP even though the pipeline produced no output signal.

---

### Relevance detection

All 5 positive documents were correctly classified as relevant. **Recall = 5/5 (100%).**

Three of the five negative documents were incorrectly classified as relevant. **Precision = 5/8 (62%).**

The three false positives are each caused by a different mechanism — see analysis below.

### Element completeness (Van Kralingen norm frame, 8 elements)

| # | Law | norm_identifier | norm_type | promulgation | scope | conditions | subject | legal_modality | act_identifier | Total |
|---|-----|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:---:|
| 1 | Wet goed verhuurderschap | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **8/8** |
| 2 | Wet toekomst pensioenen | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **8/8** |
| 3 | Wet inburgering 2021 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **8/8** |
| 4 | Wet Wtta | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | **7/8** |
| 5 | Wet franchise | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | **7/8** |

Cases 4 and 5 both missing `act_identifier`: neither letter had a bill number at the time of writing. The bill numbers (36 446 and 35 392) only existed years later. This is correct pipeline behaviour — it cannot fabricate a number that did not yet exist.

### Signal certainty

| # | Law | Certainty | Justification |
|---|-----|-----------|---------------|
| 1 | Wet goed verhuurderschap | `proposed` | Minister announces bill and consultation |
| 2 | Wet toekomst pensioenen | `committed` | Binding tripartite agreement (kabinet + sociale partners) |
| 3 | Wet inburgering 2021 | `proposed` | Hoofdlijnen letter with explicit bill announcement and 2020 target |
| 4 | Wet Wtta | `advisory` | Letter explicitly disclaims government preference; 39 variants transmitted |
| 5 | Wet franchise | `proposed` | Staatssecretaris announces wettelijke regeling and autumn 2018 consultation |

Certainty calibration is correct in all five cases. Case 4 receiving `advisory` despite being a signal is the sharpest test: the pipeline correctly distinguishes an elaboration of policy variants from a legislative commitment.

### Pipeline throughput

| # | Silver chunks | Gold written | Gold discarded | Source type |
|---|:---:|:---:|:---:|:---:|
| 1 | 9 | 9 | 0 | statutory |
| 2 | 33 | 33 | 0 | policy_intent |
| 3 | 24 | 22 | 1 | policy_intent |
| 4 | 2 | 1 | 1 | policy_intent |
| 5 | 2 | 1 | 1 | policy_intent |

Cases 4 and 5 have very short documents (2 silver chunks each). The single kept gold chunk in each case was sufficient for synthesis.

### Token usage (classifier + synthesis)

| # | Classifier tokens | Synthesis tokens | Notes |
|---|---:|---:|---|
| 1 | 6,111 | 6,221 | |
| 2 | 6,827 | 18,478 | Long document (33 chunks) |
| 3 | 6,796 | 12,636 | |
| 4 | 1,792 | 2,009 | Short cover letter |
| 5 | 1,147 | 2,145 | Short letter |

Full token accounting (including gold stage) and cost analysis: **pending — see feasibility task**.

---

## Analysis of false positives

### N1 — "Stand van zaken bij de Huurcommissie" (27 926, nr. 326)

**Why it was chosen as a negative:** This letter is an operational status update on the Huurcommissie (rent tribunal): processing times, backlogs, staffing. It does not announce any new law and contains no explicit legislative commitment.

**Why the classifier flagged it:** The letter contains forward-looking language about digitising the Huurcommissie's intake process and simplifying procedural rules. The classifier interpreted this as signalling a planned regulatory change, which is a plausible reading of the language in isolation. In context, the language describes administrative modernisation within an existing statutory framework, not a new law.

**Type of error:** Sensitivity to procedural modernisation language. The classifier cannot distinguish "we are updating internal procedures under existing law" from "we are preparing new primary legislation."

---

### N2 — "Rapport Commissie Borstlap" (29 544, nr. 970)

**Why it was chosen as a negative:** The letter is a short transmittal: the minister attaches the Borstlap commission report and says the cabinet will respond by 1 April 2020. The letter itself contains no government position or legislative intent.

**Why the classifier flagged it:** The Borstlap report — transmitted as an attachment — is dense with legislative recommendations: new legal categories for workers, restructuring of employment law, and mandatory contributions. The pipeline processes the full extracted text of the document, which includes the report body. The classifier read the report's recommendations as if they were government commitments.

**Type of error:** Content bleed from attached documents. The classifier has no way to distinguish the minister's own words from the content of documents transmitted to parliament. This is a structural limitation: fixing it would require pre-processing to isolate the cover letter from its attachments.

---

### N3 — "Uitkomsten uitzendonderzoeken" (29 544, nr. 1002)

**Why it was chosen as a negative:** The letter transmits enforcement research findings on temp-work agencies. The minister explicitly defers a government response to a later stage. No legislative commitment is made.

**Why the classifier flagged it:** The letter concerns the regulation of temp-work agencies (uitzendonderzoeken), which is precisely the domain that became the Wtta. The classifier detected the normative domain and the implied regulatory gap without a legislative commitment being stated.

**What happened next:** The gold completeness filter discarded every chunk (all scored below the threshold of 5). No synthesis record was produced. This means the pipeline emitted no output signal for N3 despite the classifier false positive. This demonstrates the value of the two-stage filter: the gold stage catches what the classifier passes.

**Type of error:** Domain association without commitment. The classifier is sensitive to normatively loaded domains (temp-work regulation) even when the letter defers rather than commits. Whether this is a "true" false positive depends on where the pipeline's output boundary is drawn. At the synthesis level, N3 was correctly handled.

---

## Backtracking chains

### P1 — Wet goed verhuurderschap

```
Wet goed verhuurderschap (in force 1 July 2023, Stb. 2023, 227)
  → Bill dossier 36 130
    → MvT (36 130 nr. 3, 2022-06-07)
      https://zoek.officielebekendmakingen.nl/kst-36130-3.html
      → cites "brief van 22 februari 2021" in dossier 27 926
        → 27 926 nr. 337 (2021-02-22) "Uitkomst aanpak goed verhuurderschap" ← SELECTED
          https://zoek.officielebekendmakingen.nl/kst-27926-337.html
          OData ID: 088132e5-f6bd-4124-a5ce-f1705be36e9a
```

**Why this letter:** It is the first letter in dossier 27 926 that commits explicitly to a *wettelijke regeling* with a landelijk geüniformeerd vergunningsstelsel for landlords. The MvT cites it by date. Earlier letters in the dossier discuss the problem (malafide verhuurders) without committing to a statutory solution.

Key signal passages:
> *"Daarnaast geven de resultaten van de pilots aanleiding om met een wetsvoorstel te komen."*

> *"Bij het ontwerpen van een nieuwe wettelijke regeling beoog ik een grondslag te introduceren voor gemeenten om landelijk geüniformeerde voorschriften te kunnen instellen in het kader van goed verhuurderschap."*

---

### P2 — Wet toekomst pensioenen

```
Wet toekomst pensioenen (in force 1 July 2023)
  → Bill dossier 36 067
    → MvT (36 067 nr. 3, 2022-03-29)
      https://zoek.officielebekendmakingen.nl/kst-36067-3.html
      → cites "principeakkoord" of June 2019 in dossier 32 043
        → 32 043 nr. 457 (2019-06-05) "Principeakkoord vernieuwing pensioenstelsel" ← SELECTED
          https://zoek.officielebekendmakingen.nl/kst-32043-457.html
          OData ID: f072ca19-05b9-4af1-a895-d5020876fe78
```

**Why this letter:** The principeakkoord is the binding tripartite agreement between the cabinet, employers, and trade unions on the direction of the pension reform. It is the earliest document in dossier 32 043 that transforms policy ambition into a concrete legislative trajectory. The certainty level `committed` reflects the binding nature of the agreement.

Key signal passages:
> *"Het kabinet heeft de ambitie om met ingang van 2022 een wettelijk kader gereed te hebben."*

> *"Er komt een wettelijke verzekeringsplicht voor zelfstandigen tegen het arbeidsongeschiktheidsrisico."*

No use of "wetsvoorstel" in this letter — the pipeline detects the signal from normative framing alone.

---

### P3 — Wet inburgering 2021

```
Wet inburgering 2021 (in force 1 January 2022)
  → Bill dossier 35 483
    → MvT (35 483 nr. 3, 2020-06-03)
      https://zoek.officielebekendmakingen.nl/kst-35483-3.html
      → cites "brief van 2 juli 2018" in dossier 32 824
        → 32 824 nr. 222 (2018-06-27) "Evaluatie van de Wet inburgering 2013"
            Excluded: evaluation report, no legislative direction
        → 32 824 nr. 223 (2018-07-02) "Hoofdlijnen veranderopgave inburgering" ← SELECTED
          https://zoek.officielebekendmakingen.nl/kst-32824-223.html
          OData ID: 9dac5c86-862b-4e00-962a-4e5168218a3e
```

**Why this letter:** Nr. 222 (sent five days earlier) contains the evaluation findings that triggered the reform but makes no legislative commitment. Nr. 223 is the minister's own hauptlijnen letter that directly commits to a new inburgeringsstelsel and names a 2020 target date for the wetsvoorstel. The MvT cites the 2 July 2018 date, which corresponds to nr. 223.

Key signal passages:
> *"Na bespreking van deze hoofdlijnen met de Tweede Kamer zal ik samen met de belangrijkste stakeholders deze verder uitwerken en komen met een wetsvoorstel. In de huidige planning is voorzien dat inwerkingtreding in 2020 haalbaar moet zijn."*

> *"Zowel door wettelijke verankering van belangrijke elementen als door de wijze van bekostiging zal gegarandeerd worden dat gemeenten deze opdracht oppakken."*

---

### P4 — Wet toelating terbeschikkingstelling van arbeidskrachten (Wtta)

This case required a two-step trace: the MvT does not directly cite the signal letter, so the policy dossier was searched chronologically.

**Step 1 — Identify the policy dossier from MvT footnotes:**

```
Wet Wtta (in force 1 January 2025)
  → Bill dossier 36 446
    → MvT (36 446 nr. 3, 2023-10-06)
      https://zoek.officielebekendmakingen.nl/kst-36446-3.html
      → cites documents in dossier 29 544 (Arbeidsmarktbeleid):
          29 544 nr. 1112 (2022-07-05) "Hoofdlijnen Arbeidsmarkt"
          29 544 nr. 1160 (2022-11-25) "Onderzoek naar effectuering van arbeidsrecht"
```

**Step 2 — Chronological search of dossier 29 544 from January 2020 forward:**

```
  → nr. 970 (2020-01-23) "Rapport Commissie Borstlap"
      Excluded: transmits the report, no government intent
  → nr. 1002 (2020-04-06) "Uitkomsten uitzendonderzoeken"
      Excluded: enforcement findings only
  → nr. 1021 (2020-07-15) "Technische uitwerking advies Commissie Regulering van werk" ← SELECTED
      OData ID: 3b7e0412-8e5a-4b81-902e-b17e01657627
      Not indexed on zoek.officielebekendmakingen.nl; retrieved via OData only
      First letter elaborating the Borstlap recommendations into 39 detailed
      regulatory variants for driehoeksrelaties (temp-work). Predates the MvT-cited
      documents by 24–28 months.
```

**Why this letter:** It is the first government document in the dossier that moves from reporting (the Borstlap report) to active elaboration of regulatory options for the temp-work sector. The letter contains 39 worked-out policy variants — detailed enough to constitute active legislative preparation. The certainty level `advisory` is correct: the letter explicitly does not commit to any specific variant.

Key signal passages:
> *"De bundel bevat 39 uitgewerkte beleidsvarianten op het terrein van de regulering van werk [...] op het terrein van driehoeksrelaties."*

No use of "wetsvoorstel". The pipeline detects the signal from the normative domain and the density of regulatory elaboration — a keyword search would not find this document.

---

### P5 — Wet franchise

```
Wet franchise (in force 1 January 2021)
  → Bill dossier 35 392
    → MvT (35 392 nr. 3, 2020-02-10)
      https://zoek.officielebekendmakingen.nl/kst-35392-3.html
      → references franchise policy in dossier 31 311 (Zelfstandig ondernemerschap)
        → nr. 149 (2015-04-02) "Voortgang versterking van zelfregulering franchisesector"
            Excluded: self-regulation approach, no statutory commitment
        → nr. 150 (2015-06-19) "Consultatie Nederlandse Franchise Code"
            Excluded: consultation on voluntary code
        → nr. 153 (2015-09-25) "Uitkomst consultatie Nederlandse Franchise Code"
            Excluded: outcome of consultation, still self-regulation only
        → nr. 165 (2016-02-17) "Presentatie Nederlandse Franchise Code"
            Excluded: launch of voluntary franchise code, no statutory commitment
        → nr. 206 (2018-05-23) "Stand van zaken regelgeving Franchise" ← SELECTED
          https://zoek.officielebekendmakingen.nl/kst-31311-206.html
          OData ID: 911c7082-b68b-4d73-9c80-16c2419a3259
          First letter announcing the shift from voluntary self-regulation to statutory
          regulation. No further franchise-specific letters before the MvT.
```

**Why this letter:** The government had pursued voluntary self-regulation via the Nederlandse Franchise Code from 2015. Nr. 165 launched that code. Nr. 206 is the moment the Staatssecretaris announced it had not worked and a statutory route was needed. The backtracking chain shows four excluded earlier letters, all in the self-regulation phase. Nr. 206 is the pivot point.

Key signal passages:
> *"Om invulling te geven aan dit voornemen zal het kabinet een wettelijke regeling voorbereiden die een kader schept voor vier deelgebieden van de samenwerking tussen franchisegevers en franchisenemers."*

> *"Ik streef ernaar dit najaar een wetsvoorstel te publiceren voor consultatie."*

> *"Op basis van de huidige inzichten lijkt het opportuun in regelgeving de genoemde deelgebieden van de nodige kaders te voorzien, in plaats van verankering via een gedragscode."* — The key framing decision: statutory over self-regulation.

---

## Negative case selection rationale

### N1 — "Stand van zaken bij de Huurcommissie" (27 926 nr. 326, 2020-07-02)

Chosen from the same dossier as P1 (Wet goed verhuurderschap). The letter reports on Huurcommissie operational performance: caseload, processing times, and a pilot for digital intake. It predates the signal letter (P1, February 2021) by seven months.

**Why it should be discarded:** There is no legislative commitment. The minister discusses the functioning of an existing body under existing law. The digital intake pilot is an administrative change, not a statutory one.

**Caveat:** The classifier flagged it as relevant (FP). The forward-looking language about digitalisation and process simplification was read as signalling regulatory intent. In retrospect, a cleaner negative from this dossier would be a letter with no procedural modernisation language at all — but dossier 27 926 was active throughout 2017–2021 with the minister consistently preparing Wet goed verhuurderschap, making clean negatives scarce.

---

### N2 — "Rapport Commissie Borstlap" (29 544 nr. 970, 2020-01-23)

Chosen from the same dossier as P4 (Wet Wtta). The letter is a short transmittal attaching the Borstlap commission report on the future of labour market regulation.

**Why it should be discarded:** The letter itself contains no government position. The transmittal says the cabinet will respond by 1 April 2020. All normative content belongs to the independent commission, not the government.

**Caveat:** The classifier flagged it (FP) because the transmitted report is dense with legislative recommendations. This is a structural limitation of text-based approaches: the pipeline processes the full document including attachments and cannot separate the cover letter from attached content. The letter is a genuine negative but the document-as-processed is not.

---

### N3 — "Uitkomsten uitzendonderzoeken" (29 544 nr. 1002, 2020-04-06)

Also from dossier 29 544. The letter transmits three enforcement research reports on temp-work agencies and explicitly defers a government response.

**Why it should be discarded:** No government position is stated. The letter defers: *"Op de bevindingen uit de onderzoeken kom ik in een volgende brief terug."*

**Caveat:** The classifier flagged it (FP) because the domain — temp-work regulation — is normatively loaded and directly related to the eventual Wtta. The gold stage filtered all chunks out (no synthesis produced), so the pipeline's final output was correct even though the classifier was not.

---

### N4 — "Evaluatie fiscale ondernemerschapsregelingen" (31 311 nr. 186, 2017-05-18)

From the same dossier as P5 (Wet franchise). A caretaker-cabinet (*demissionair kabinet*) transmittal of an evaluation report on fiscal entrepreneur schemes.

**Why it was discarded:** Two independent reasons. First, caretaker cabinet language: the minister explicitly states the incoming cabinet will have to take a position. Second, the letter concerns fiscal self-employment schemes (ZZP taxation), not franchise regulation — it is in the same dossier (31 311 "Zelfstandig ondernemerschap") but addresses a different sub-topic. Zero silver chunks were produced, confirming the pipeline found nothing normatively relevant.

---

### N5 — "Ontwikkelingen op het gebied van de inburgeringsexamens" (32 824 nr. 50, 2014-03-11)

From the same dossier as P3 (Wet inburgering 2021). Written four years before the signal letter. Covers exam procurement, passing rates by demographic group, and administrative adjustments to the inburgering exam.

**Why it was discarded:** Purely administrative and operational content. No legislative intent. The document predates the reform trigger (the 2018 evaluation of the 2013 Wet inburgering) by four years. Zero silver chunks were produced.

**Note on earlier rejected candidates from dossier 32 824:** Nr. 176 (2016) contained explicit wetsvoorstel references (civic integration exam reform). Nr. 118 (2014) referenced upcoming legislative adjustments. Nr. 50 (2014) was the cleanest negative found in this dossier.

---

## Conclusions

**Recall is perfect.** All 5 signal letters were correctly detected, including two cases without any "wetsvoorstel" keyword (P2, P4). This demonstrates that semantic understanding adds value over text-based keyword search.

**Precision is moderate.** 3 of 5 negative cases were incorrectly flagged as relevant at the classifier stage. The three false positives have different root causes:
- N1: sensitivity to administrative modernisation language
- N2: content bleed from transmitted third-party report
- N3: domain sensitivity without explicit commitment (mitigated by gold-stage filtering)

**The gold stage provides a meaningful second filter.** N3 was a classifier FP but produced no synthesis output. The two-stage design (classifier + gold completeness threshold) reduced the effective false-positive rate at the output level.

**Lead time is strong.** The pipeline detects signals 16–39 months before the MvT in all 5 positive cases.

**Element completeness is high.** Cases 1–3 achieve 8/8. Cases 4–5 achieve 7/8, with the missing element (`act_identifier`) structurally absent because no bill existed at the time of writing.

**Certainty calibration is correct** across all cases, including the hard case (P4: `advisory` for a variants letter without direct commitment language).

---

## Replication

All commands run from `Code sprint/` (the directory containing `docker-compose.yml`).

### 1 — Wipe the database and start fresh

```bash
docker-compose down -v
docker-compose up -d db
```

`-v` drops all volumes (the postgres data directory). Wait a few seconds for the DB to initialise before continuing.

### 2 — Build the pipeline image

```bash
docker-compose build pipeline
```

Only needed if source files changed since the last build.

### 3 — Seed all 10 validation documents

```bash
docker-compose run --rm pipeline python seed_validation_docs.py
```

Runs migrations, fetches metadata from the Tweede Kamer OData API, downloads the PDFs, extracts text, and inserts all 10 records into bronze. Expect ~60 seconds.

### 4 — Run the pipeline on each document

```bash
# Positive cases
docker-compose run --rm pipeline python run_pipeline.py --doc-id 088132e5-f6bd-4124-a5ce-f1705be36e9a
docker-compose run --rm pipeline python run_pipeline.py --doc-id f072ca19-05b9-4af1-a895-d5020876fe78
docker-compose run --rm pipeline python run_pipeline.py --doc-id 9dac5c86-862b-4e00-962a-4e5168218a3e
docker-compose run --rm pipeline python run_pipeline.py --doc-id 3b7e0412-8e5a-4b81-902e-b17e01657627
docker-compose run --rm pipeline python run_pipeline.py --doc-id 911c7082-b68b-4d73-9c80-16c2419a3259

# Negative cases
docker-compose run --rm pipeline python run_pipeline.py --doc-id 552b83c2-67ac-4f4c-8ae5-96abb482cbdf
docker-compose run --rm pipeline python run_pipeline.py --doc-id 349df7ce-d2a8-405d-a099-5ed5c6c5cdf3
docker-compose run --rm pipeline python run_pipeline.py --doc-id 6b96d047-d7f5-4909-9597-360f6a527a95
docker-compose run --rm pipeline python run_pipeline.py --doc-id bf392419-e4be-4725-8580-b83d775a787b
docker-compose run --rm pipeline python run_pipeline.py --doc-id 9858d519-158f-4497-8652-c3a9c24d4d70
```

These can be run in parallel (each run is scoped to its own `doc_id`).

### 5 — Export results

```bash
docker-compose run --rm pipeline python export_validation_data.py
```

Writes `src/data/validation_results.json` and prints the summary table with TP/FP/TN/FN counts and precision/recall to stdout.

### 6 — Dump the database

```bash
docker-compose exec db pg_dump -U postgres horizon_scanning \
  > ../Validation/Retrospective\ detection/validation_db_dump_$(date +%Y-%m-%d).sql
```

---

## Next actions

- [ ] Feasibility analysis: measure wall-clock runtimes and full token costs (including gold stage) per document — planned as separate task
- [ ] Write validation section in thesis Chapter 6 using this data
- [ ] Expert evaluation component for RQ6 "aligned with expert expectations" — not yet done
- [ ] Address ethical considerations for RQ5 in Chapter 6
- [ ] Requirements traceability matrix (R1–R8 ↔ pipeline components) — Task 31
- [ ] DB dump: `docker-compose exec db pg_dump -U postgres horizon_scanning > validation_db_dump_2026-05-17.sql`
