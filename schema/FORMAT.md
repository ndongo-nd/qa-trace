# Format de feature.json

```json
{
  "slug": "oidc-regex-claim-mapping",
  "title": "Titre de la spec",
  "spec_file": "chemin/vers/spec.md",
  "release": "Horizon 2.12.0",
  "repos": ["horizon-core"],
  "explanation": {
    "summary": "...",
    "ecosystem_role": "...",
    "example": ["Etape 1", "Etape 2"],
    "limits": ["..."]
  },
  "requirements": [
    {
      "id": "FR-2",
      "type": "FR",
      "text": "Enonce atomique",
      "source": "Functional Requirements",
      "derived_from": ["US-1", "US-4"],
      "code": ["horizon-core/src/.../File.scala:120"]
    }
  ],
  "tests": [
    {
      "id": "TC-001",
      "title": "Titre court et explicite",
      "req": ["FR-2", "AC-1"],
      "type": "Functional",
      "priority": "P1",
      "automation": "Manual",
      "folder": "OIDC / Regex mapping",
      "tags": ["regex"],
      "preconditions": "Etat initial",
      "steps": [["Action", "Resultat attendu"]]
    }
  ],
  "open_questions": ["..."],
  "findings": ["Ecarts spec / code"]
}
```

## Types d'exigence

`US` (user story, tracee via ses FR, non couverte directement), `FR`, `AC`, `NFR`, `ACT`.
La validation exige au moins un test pour chaque `FR`, `AC`, `NFR` et `ACT`.

## Valeurs autorisees

- `priority` : P1, P2, P3
- `type` (test) : Functional, Regression, Security, Performance, Usability
- `automation` : Manual, Automatable, Automated
- tag reserve : `needs-clarification`
