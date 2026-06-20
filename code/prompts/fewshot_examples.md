# Few-Shot Examples — Norm Frame Extractor

> FROZEN 2026-05-07. See prompts/REFERENCE.md for provenance, URLs, and coverage rationale.

---

## Example 1 — Competence norm / can (civil procedure, bill in preparation, unnamed act)

*Source: Kamerstukken II 2025–2026, 29 279, nr. 1020*

**Document chunk:**
"Waar mogelijk, wordt het digitaal procederen in civielrechtelijke procedures verder mogelijk gemaakt. Ik werk verder aan een wettelijke regeling voor het gebruik van videoconferentie in civiele procedures."

Reasoning: The phrase 'ik werk verder aan een wettelijke regeling' signals a bill in preparation. The framing 'verder mogelijk gemaakt' establishes an enabling context — the legislation creates the institutional legal basis for video hearings to be valid proceedings, a competence norm. The modality is 'can': the legislation enables, it does not oblige. No act name or conditions of application are stated. Signal certainty is 'proposed'. Source type is 'statutory'.

Output:
```json
{
  "signal_summary": "A bill is being prepared to enable the legal use of video conferencing as a valid form of participation in civil court proceedings.",
  "signal_certainty": "proposed",
  "source_type": "statutory",
  "norm_identifier": "signal-videoconferentie-2026-04",
  "norm_type": "competence",
  "promulgation": "State Secretary of Justice and Security (Van Bruggen)",
  "scope": "Civil court proceedings in the Netherlands",
  "conditions": "",
  "subject": "Parties to civil proceedings and civil courts",
  "legal_modality": "can",
  "act_identifier": ""
}
```

---

## Example 2 — Conduct norm / ought not (labour market, law adopted, named act)

*Source: Kamerstukken II 2025–2026, 36 446, nr. 90*

**Document chunk:**
"Op 11 november 2025 is de Wet toelating terbeschikkingstelling van arbeidskrachten (Wtta) aangenomen door de Eerste Kamer. Met de wet wordt een nieuw toelatingsstelsel tot de uitleenmarkt geïntroduceerd. Dit is conform één van de aanbevelingen van het Aanjaagteam Bescherming Arbeidsmigranten. Met de Wtta dragen we zorg voor een betere bescherming van kwetsbare arbeidskrachten en creëren we een gelijk speelveld voor uitleners. De beoogde inwerkingtredingsdatum voor het toelatingsstelsel is 1 januari 2027."

Reasoning: The Wtta establishes a mandatory authorisation (toelating) system for labour intermediaries. An authorisation system creates a prohibition by operation: from 1 January 2027, labour intermediaries (uitleners) may not provide workers without a valid toelating. This is a conduct norm with modality 'ought not'. The law is explicitly named and has been adopted by both chambers, placing this at the committed stage. Signal certainty is 'committed'. Source type is 'statutory'.

Output:
```json
{
  "signal_summary": "The Wtta — adopted by the Eerste Kamer on 11 November 2025 — prohibits labour intermediaries from providing workers without a valid authorisation from 1 January 2027.",
  "signal_certainty": "committed",
  "source_type": "statutory",
  "norm_identifier": "signal-wtta-toelating-2027",
  "norm_type": "conduct",
  "promulgation": "Minister of Social Affairs and Employment (Paul)",
  "scope": "Labour intermediary market (uitleenmarkt) in the Netherlands",
  "conditions": "From 1 January 2027, the date the toelatingsstelsel enters into force",
  "subject": "Uitleners (labour intermediaries providing workers to third parties)",
  "legal_modality": "ought not",
  "act_identifier": "Wet toelating terbeschikkingstelling van arbeidskrachten (Wtta)"
}
```

---

## Example 3 — Conduct norm / ought (copyright/IP, internet consultation closed, named act)

*Source: Kamerstukken II 2025–2026, 29 279, nr. 1020*

**Document chunk:**
"Met het wetsvoorstel Wet collectief rechtenbeheer en toezicht, waarvan de internetconsultatie onlangs is afgesloten, wil het kabinet het wettelijk kader voor collectieve beheersorganisaties, die belast zijn met de inning en verdeling van vergoedingen voor het gebruik van auteursrechtelijke werken, en het toezicht daarop door het College van Toezicht Auteursrechten (CvTA) opnieuw vormgeven."

Reasoning: The bill is explicitly named and has passed internet consultation, placing it at an advanced pre-legislative stage. The cabinet intends to redesign the legal framework governing collective rights management organisations and their supervisory relationship with the CvTA. The resulting norms will impose obligations on these organisations — a conduct norm with modality 'ought'. Signal certainty is 'proposed'. Source type is 'statutory'.

Output:
```json
{
  "signal_summary": "A bill to redesign the legal framework for collective rights management organisations and their supervision by the CvTA has recently closed its internet consultation phase.",
  "signal_certainty": "proposed",
  "source_type": "statutory",
  "norm_identifier": "signal-collectief-rechtenbeheer-2026-04",
  "norm_type": "conduct",
  "promulgation": "State Secretary of Justice and Security (Van Bruggen)",
  "scope": "Collective rights management and copyright supervision in the Netherlands",
  "conditions": "",
  "subject": "Collective rights management organisations (collectieve beheersorganisaties) and the College van Toezicht Auteursrechten (CvTA)",
  "legal_modality": "ought",
  "act_identifier": "Wet collectief rechtenbeheer en toezicht"
}
```

---

## Example 4 — Conduct norm / ought (housing/energy, internet consultation closed, unnamed act)

*Source: Kamerstukken II 2025–2026, 36 800 XXII, nr. 45*

**Document chunk:**
"Er ligt een voorstel voor minimum energieprestatie-eisen voor alle huurwoningen per 1 januari 2029. De internetconsultatie van dit voorstel is eind vorig jaar afgerond. In aanvulling daarop streeft het kabinet naar uitfasering van energielabels C en D per 2040."

Reasoning: A formal proposal for minimum energy performance requirements exists and internet consultation has been completed, placing this at the pre-legislative stage. From 1 January 2029, landlords would be required to meet minimum energy standards for all rental properties — a conduct norm with modality 'ought'. No act is yet named in this passage. Signal certainty is 'proposed'. Source type is 'statutory'.

Output:
```json
{
  "signal_summary": "A proposal for mandatory minimum energy performance requirements for all rental housing, targeting 1 January 2029, has completed its internet consultation phase.",
  "signal_certainty": "proposed",
  "source_type": "statutory",
  "norm_identifier": "signal-energieprestatie-huurwoningen-2029",
  "norm_type": "conduct",
  "promulgation": "Minister van Volkshuisvesting en Ruimtelijke Ordening",
  "scope": "Rental housing sector in the Netherlands",
  "conditions": "From 1 January 2029",
  "subject": "Verhuurders (landlords of rental properties)",
  "legal_modality": "ought",
  "act_identifier": ""
}
```
