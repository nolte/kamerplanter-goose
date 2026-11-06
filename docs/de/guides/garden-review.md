---
title: Gartenrückschau
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-06
---

# Gartenrückschau

`garden-review` blickt mitten in einer Saison auf einen Garten zurück, bis zu einem Datum: **was für jede Pflanze erfasst wurde, was du dazu sagst, was die Saison lehrt und was der nächste Plan beibehalten oder überdenken sollte.** Sie endet in einem Block für den nächsten Zyklus, den du an [`garden-plan`](garden-plan.md) oder [`crop-selection`](crop-selection.md) übergeben kannst. Für eine ganze, abgeschlossene Saison, archivierte Pflanzen eingeschlossen, setze `season` — siehe die [Saisonrückschau](season-review.md).

Der Lauf **liest nur**. Er schreibt die Rückschau nirgendwohin — keine Datei, kein Tagebucheintrag —, hat kein Anwendungsrezept und ruft kein Home-Assistant-Tool auf.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Was eine Rückschau sagt und was nicht

- **Ertrag kommt nur von dir.** Der Datenbestand hat kein Ertragsfeld, und ein Tagebuch-Messwert wird nie als Ertrag gelesen. Gib ihn als `plant_key:amount unit` an.
- **Pflege ist nie die Ursache.** Ein Muster im Pflegeprotokoll wird mit einem Ergebnis nur als „passt zu“ verknüpft, als Verdacht, nie als Grund, warum etwas geschah.
- **Sorten stehen nebeneinander.** Keine Punktzahl, keine Rangfolge, kein Durchschnitt; zwei Sorten werden nur auf demselben Feld in derselben Einheit verglichen.
- **Pflanzengesundheit wird hier nicht beurteilt.** Die Rückschau führt keine Gesundheitsbeurteilung aus und meldet die Pflanzengesundheit als nicht geliefert; für den gegenwärtigen Zustand einer Pflanze läuft plant-health-assessment eigens. Die Schädlingsgeschichte stammt nur aus den erfassten Inspektionen; die Rückschau führt keine Beurteilung des gegenwärtigen Zustands einer Pflanze aus.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `decision-policy` und `garden-review` aus `.claude/skills/`. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren.

## Ausführen

```sh
goose run --recipe garden-review \
  --params tenant=my-garden \
  --params plants=42,43 \
  --params yields="42:1.2 kg,43:14 fruit" \
  --params notes="43: Blütenendfäule im Juli; Schnecken überall nach dem nassen Juni" \
  --params as_of=2026-08-15
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `plants` | nein | nur die Gartenebene: Kulturen, Pflanzläufe und fällige Aufgaben |
| `yields` | nein | jeder Ertrag fehlt |
| `harvest_results` | nein | jedes Ernteergebnis fehlt; gib `plant_key:result[:YYYY-MM-DD]` an, etwa aus Schlusszeilen von `harvest-readiness-check` übernommen |
| `notes` | nein | nichts von dir zu Pflanzen oder zum Garten |
| `weather` | nein | das Wetter der Saison fehlt; es ist in jedem Fall nur Kontext |
| `as_of` | nein | das Datum des jüngsten gelesenen Tagebucheintrags |
| `season` | nein | die Rückschau mitten in der Saison auf dieser Seite; ein Jahr oder eine Spanne macht daraus die [Saisonrückschau](season-review.md) |

Höchstens fünf Pflanzen werden betrachtet: die ersten fünf nach Pflanzenschlüssel, als Text sortiert. `;` und `:` trennen die Einträge von `yields`, `harvest_results` und `notes`; ein Freitextteil, der sie enthält, wird wörtlich gezeigt und nicht weiter geparst. Das Tagebuch jeder Pflanze wird für höchstens acht Einträge gelesen, und die Rückschau sagt, wie weit zurück das reichte.

## Das Ergebnis lesen

Der Bericht zeigt sechs Blöcke: den Kopf, einen Verlaufsdatensatz je Pflanze, die Leistung der Sorten, die Lehren (jede eine Beobachtung oder eine Empfehlung mit Beleg, Konfidenz, Unsicherheit und fehlenden Daten), den Block für den nächsten Zyklus und den Domänenstatus. Jede Kultur im Block für den nächsten Zyklus ist mit `reconsider` gekennzeichnet, wenn ein Datensatz oder deine Notiz ein Problem mit ihr nennt, was allem anderen vorgeht; mit `keep` nur, wenn du einen Erfolg meldest (eine Notiz oder einen Ertrag, den du als Erfolg bezeichnest) und kein Problem festgehalten ist; sonst mit `no evidence`. Eine bloße Ertragszahl ist `no evidence`. `constraints` trägt nur Beobachtungen zu Standort und Umgebung; Lehren gehen in `goals`.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `GARDEN REVIEW: <n> reviewed, <m> not reviewed — <slug>` | `<n>` Pflanzen haben einen Verlaufsdatensatz; `<m>` wurden über die Grenze hinaus genannt oder konnten nicht gelesen werden |

## Quellen

- [`recipes/garden-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-review.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/garden-review/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-review/SKILL.md) — der Verlaufsdatensatz, die Lehren und der Block für den nächsten Zyklus
- [`spec/process/garden-and-season-review/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-and-season-review/de.md) — der Prozess, den dieses Rezept umsetzt
