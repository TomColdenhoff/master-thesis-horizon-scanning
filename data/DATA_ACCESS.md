# Data Access

## Sample documents (included)

The `sample_input/` folder contains the 10 parliamentary documents used in the retrospective detection validation (Chapter 6). These are sourced from the Tweede Kamer OData API and are publicly available without authentication.

| ID | Document | Role in validation |
|---|---|---|
| `088132e5` | 27 926, nr. 337 — "Uitkomst aanpak goed verhuurderschap" | Positive (P1) |
| `f072ca19` | 32 043, nr. 457 — "Principeakkoord vernieuwing pensioenstelsel" | Positive (P2) |
| `9dac5c86` | 32 824, nr. 223 — "Hoofdlijnen veranderopgave inburgering" | Positive (P3) |
| `3b7e0412` | 29 544, nr. 1021 — "Technische uitwerking advies Commissie Regulering van werk" | Positive (P4) |
| `911c7082` | 31 311, nr. 206 — "Stand van zaken regelgeving Franchise" | Positive (P5) |
| `349df7ce` | Hard negative — same dossier as P1, no legislative commitment | Negative (N1) |
| `552b83c2` | Hard negative — same dossier as P2 | Negative (N2) |
| `6b96d047` | Hard negative — same dossier as P3 | Negative (N3) |
| `9858d519` | Hard negative — same dossier as P4 | Negative (N4) |
| `bf392419` | Hard negative — same dossier as P5 | Negative (N5) |

## Fetching the full dataset

The pipeline's bronze stage fetches documents automatically. To retrieve the full dataset:

```bash
docker-compose run --rm pipeline python run_pipeline.py --stage bronze
```

This calls the Tweede Kamer OData API:

```
https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Document
  ?$filter=Soort in ('Brief regering','Antwoord schriftelijke vragen','EU-voorstel',
                     'Brief Europese Commissie','Lijst met EU-voorstellen')
           and Datum ge 2020-01-01T00:00:00Z
  &$orderby=Datum asc
  &$top=250
```

No API key required. Documents are downloaded as PDF or DOCX via the `/Resource(<id>)/Content` endpoint.

## License

All parliamentary documents are published by the Dutch government and are in the public domain under Dutch law (Auteurswet art. 11).
