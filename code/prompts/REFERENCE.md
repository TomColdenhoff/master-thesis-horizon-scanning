# Prompt Reference

This file is **not sent to any LLM**. It is documentation for developers and the thesis author.
It explains every field value, records few-shot example provenance, and maps the system to the
Dutch legislative process.

---

## Legend: field values

### norm_type

The Van Kralingen norm-type taxonomy divides legal norms into two kinds:

| Value | What it means | When to use |
|---|---|---|
| `conduct` | Regulates behaviour — tells someone what to do, not do, or that they may do something | The norm imposes an obligation, prohibition, or permission on a person or organisation |
| `competence` | Creates a legal power or institution — enables an authority to take binding decisions or establishes a new body | The norm grants a government body a power it did not previously have, or creates a new legal entity |

**The key test:** does the norm address what someone *must do / may not do / may do* (conduct), or does it address what someone *is empowered to do* (competence)?

---

### legal_modality

Legal modality describes the normative force of the conduct or competence norm.

| Value | Dutch signal phrases | Plain English |
|---|---|---|
| `ought` | *verplicht, moet, dient te, zijn gehouden* | Obligation — the subject is required to do something |
| `ought not` | *verboden, mogen niet, is niet toegestaan, verbiedt* | Prohibition — the subject is forbidden from doing something |
| `may` | *mogen, is het toegestaan, kunnen kiezen* | Permission — the subject is allowed but not required to do something |
| `can` | *kan, heeft de bevoegdheid, wordt gemachtigd* | Competence/enablement — an authority is given a power or capacity |

**Note:** `can` is almost always paired with `norm_type: competence`. `ought`, `ought not`, and `may` are almost always paired with `norm_type: conduct`.

---

### signal_certainty

Signal certainty maps the document signal to a stage in the Dutch policy and legislative process.

| Value | What it means | Typical Dutch phrases | Process stage |
|---|---|---|---|
| `committed` | Government has formally decided or committed; a bill has been submitted or a decision has been published | *heeft besloten, zal worden ingediend, treedt in werking* | Bill submitted to parliament (ingediend) or law adopted (aangenomen) |
| `proposed` | A concrete proposal exists but has not yet been decided; consultation has started or closed | *wetsvoorstel in voorbereiding, internetconsultatie, overweegt in te dienen* | Internet consultation (internetconsultatie) or advisory opinion stage (Raad van State) |
| `advisory` | An intention, ambition, or recommendation without binding commitment; early-stage exploration | *is voornemens, streeft naar, wil inzetten op, onderzoekt de mogelijkheid* | Research commissioned, policy letter, coalition agreement intention |
| `existing` | Describes a rule already in force with no new signal | *is reeds van kracht, geldt al, op grond van de huidige wet* | N/A — filter these out of the review queue |

**Dutch legislative process (simplified):**
```
Coalition agreement intention
    ↓ advisory
Research commissioned (WODC, CPB, etc.)
    ↓ advisory
Policy letter (beleidsbrief) or programme
    ↓ advisory → proposed
Internet consultation (internetconsultatie)
    ↓ proposed
Council of State advice (Raad van State)
    ↓ proposed
Bill submitted to Tweede Kamer (ingediend)
    ↓ committed
Tweede Kamer vote
    ↓ committed
Eerste Kamer vote (aangenomen)
    ↓ committed
Royal Decree / entry into force (Staatsblad)
    ↓ existing
```

---

### source_type

Source type describes the legal basis or instrument grounding the norm.

| Value | What it means | Examples |
|---|---|---|
| `statutory` | Grounded in (proposed) legislation or binding EU regulation | Wetsvoorstel, AMvB, EU Regulation, Richtlijn |
| `sector_code` | Grounded in a sector-specific code, covenant, or self-regulatory instrument | Gedragscode, convenant, NEN-norm, sector agreement |
| `case_law` | Grounded in a court ruling or jurisprudence | Uitspraak Hoge Raad, CBb, ABRvS, ECLI references |
| `policy_intent` | Grounded in a policy letter, programme, or political intention without direct legal basis | Beleidsbrief, coalitieakkoord, werkagenda |

---

## Few-shot example provenance

The examples in `fewshot_examples.md` are drawn from four real parliamentary documents.
All passages are quoted verbatim. Re-frozen 2026-05-07.

| Example | Kamerstuk | OData ID | Date | Author |
|---|---|---|---|---|
| 1, 3 | Kamerstukken II 2025–2026, 29 279, nr. 1020 | `f5424e09-a713-4c80-ab1e-daa6cb803e8a` | 2026-04-16 | Staatssecretaris van Justitie en Veiligheid (Van Bruggen) |
| 2 | Kamerstukken II 2025–2026, 36 446, nr. 90 | `d0904172-52bd-4a58-a5fc-97ec2d8e8c6c` | 2026-02-12 | Minister van Sociale Zaken en Werkgelegenheid (Paul) |
| 4 | Kamerstukken II 2025–2026, 36 800 XXII, nr. 45 | `c14434be-4a32-47ba-9b93-00d3de8c27d2` | 2026-04-24 | Minister van Volkshuisvesting en Ruimtelijke Ordening |

**Verification URLs** (confirmed live 2026-05-07):

- **Ex. 1 & 3**
  Metadata: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(f5424e09-a713-4c80-ab1e-daa6cb803e8a)
  Download: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(f5424e09-a713-4c80-ab1e-daa6cb803e8a)/resource

- **Ex. 2**
  Metadata: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(d0904172-52bd-4a58-a5fc-97ec2d8e8c6c)
  Download: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(d0904172-52bd-4a58-a5fc-97ec2d8e8c6c)/resource
  Officiële bekendmaking: https://zoek.officielebekendmakingen.nl/kst-36446-90.html

- **Ex. 4**
  Metadata: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(c14434be-4a32-47ba-9b93-00d3de8c27d2)
  Download: https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document(c14434be-4a32-47ba-9b93-00d3de8c27d2)/resource

**Coverage:**

| Example | Domain | norm_type | legal_modality | act_identifier | signal_certainty |
|---|---|---|---|---|---|
| 1 — Videoconferentie | Civil procedure | competence | can | empty | proposed |
| 2 — Wtta uitleenmarkt | Labour market | conduct | ought not | named (Wtta) | committed |
| 3 — Collectief rechtenbeheer | Copyright / IP | conduct | ought | named | proposed |
| 4 — Energieprestatie-eisen | Housing / energy | conduct | ought | empty | proposed |

**Change log:**
- 2026-04-20: Initial freeze — 3 examples from 29 279 nr. 1020 (civil procedure only); signal_summary / signal_certainty / source_type absent from output blocks
- 2026-05-07: Re-frozen — 4 examples from 4 real documents; all extra fields added; ought not coverage added; sources verified

---

## Van Kralingen framework — academic context

The Van Kralingen norm frame originates in:

> Van Kralingen, R. W. (1995). *Frame-based Conceptual Models of Statute Law*. PhD dissertation, Leiden University.

Secondary sources used in the thesis:
- Van Kralingen, R. W. & Visser, P. R. S. (1999). A Method for Conceptualising Legal Domains. *Artificial Intelligence and Law*, 7(1), 51–75. DOI: 10.1023/A:1008256322911
- JURIX '96 proceedings, p. 02 (jurix.nl/pdf/j96-02.pdf)

⚠️ The norm-type taxonomy (conduct / competence) and legal-modality values (ought / ought not / may / can) are sourced from these secondary sources, not directly verified against the 1995 dissertation. Verify before thesis submission.

---

## Key document identifiers (pipeline constants)

| Document | Kamerstuk | OData ID | Notes |
|---|---|---|---|
| Ollongren letter (validation — DO NOT USE in development) | Kamerstuk 27 926, nr. 337 | `088132e5-f6bd-4124-a5ce-f1705be36e9a` | Reserved for Phase 5 only |
| Bill explanatory memorandum (ground truth) | Kamerstuk 36 130, nr. 3 | `1ebe8099-a6db-41f9-afcc-32e61da718d7` | MvT, 2022-06-07 |
| Few-shot source (Ex. 1 & 3) | Kamerstukken II 2025–2026, 29 279, nr. 1020 | `f5424e09-a713-4c80-ab1e-daa6cb803e8a` | Van Bruggen, DOCX |
