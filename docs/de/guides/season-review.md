---
title: Saisonrückschau
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Saisonrückschau

`season-review` schließt den Kreis, den [`garden-plan`](garden-plan.md) öffnet. Sie blickt auf eine Saison eines Gartens zurück, **archivierte Pflanzen eingeschlossen, damit die Ausfälle nicht verborgen bleiben**, und endet in einem Block für den nächsten Zyklus, dessen Zeilen die Parameter des Plans für die nächste Saison sind. Sie liefert dieselben Blöcke wie [`garden-review`](garden-review.md) — Verlaufsdatensätze, Leistung der Sorten, Lehren und den Domänenstatus — über eine Saison, die du nennst.

Der Lauf **liest nur**. Er schreibt die Rückschau nirgendwohin — keine Datei, kein Tagebucheintrag —, hat kein Anwendungsrezept und ruft kein Home-Assistant-Tool auf.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Das Auflisten archivierter Pflanzen nutzt `include_archived`, das andere Rezepte hier verwenden, die [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) aber nicht festhält. Behandle den ersten echten Lauf als die Messung.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `decision-policy` und `garden-review` aus `.claude/skills/`. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren.
- **Führe es zuerst einmal ohne `plants` aus.** Dann listet es die Pflanzen der Saison auf, archivierte gekennzeichnet, sodass du bis zu fünf zur Betrachtung auswählen kannst. Archivierte Pflanzen werden bei jedem Lauf aufgelistet, auch wenn du Pflanzen nennst; betrachtet werden nur die genannten (die ersten fünf nach Pflanzenschlüssel, als Text sortiert).

## Ausführen

```sh
goose run --recipe season-review \
  --params season=2026 \
  --params tenant=my-garden \
  --params plants=42,43,51 \
  --params yields="42:1.2 kg,43:14 fruit" \
  --params harvest_results="42:ready:2026-09-20,43:ready:2026-08-10" \
  --params notes="42: best leeks so far; 43: blossom end rot in July; a wet, cool spring"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `season` | ja | — ein Jahr (`2026`) oder eine Spanne (`2026-03-01..2026-10-31`); alles andere hält den Lauf an |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `plants` | nein | keine Pflanze wird betrachtet; die Pflanzen der Saison werden aufgelistet, damit du sie nennen kannst |
| `yields` | nein | jeder Ertrag fehlt; der Datenbestand hat kein Ertragsfeld |
| `harvest_results` | nein | jedes Ernteergebnis fehlt; gib `plant_key:result[:YYYY-MM-DD]` an, etwa aus Schlusszeilen von `harvest-readiness-check` übernommen |
| `notes` | nein | nichts von dir zu Pflanzen oder zur Saison |
| `weather` | nein | das Wetter der Saison fehlt; es ist in jedem Fall nur Kontext |
| `as_of` | nein | das Wachstumsstadium wird am jüngsten gelesenen Tagebucheintrag gemessen |

Das Tagebuch jeder Pflanze wird für höchstens acht Einträge gelesen; der Verlaufsdatensatz sagt, ob das die Saison abdeckt oder wo es endet.

## Das Ergebnis an den nächsten Plan übergeben

Der Block `NEXT CYCLE` wird wörtlich gezeigt. Seine Zeilen `crops`, `goals`, `constraints` und `harvest_window` haben die Formate, die `garden-plan` und `crop-selection` annehmen, sodass die nächste Saison bei ihnen beginnt:

```text
NEXT CYCLE
  crops:            allium_porrum,solanum_lycopersicum:san_marzano,lactuca_sativa
    allium_porrum: keep — notes (caller): best leeks so far; no problem recorded
    solanum_lycopersicum:san_marzano: reconsider — notes (caller): blossom end rot in July
    lactuca_sativa: no evidence — no success or problem recorded
  goals:            fewer losses to blossom end rot
  constraints:      a wet, cool spring
  harvest_window:   August to September
  location history (location, not bed):
    bed-north:2026:allium_porrum
    bed-south:2026:solanum_lycopersicum:san_marzano
```

```sh
goose run --recipe garden-plan \
  --params tenant=my-garden \
  --params crops="allium_porrum,solanum_lycopersicum:san_marzano,lactuca_sativa" \
  --params goals="fewer losses to blossom end rot" \
  --params constraints="a wet, cool spring" \
  --params harvest_window="August to September"
```

`reconsider` geht `keep` vor; `keep` braucht einen Erfolg, den du meldest, und eine bloße Ertragszahl ist `no evidence`. `constraints` trägt nur Beobachtungen zu Standort und Umgebung; Lehren gehen in `goals`. `;` und `:` sind Trennzeichen in deinen Parametern, und freier Text, der sie enthält, wird wörtlich gezeigt und nicht geparst. Eine mit `reconsider` gekennzeichnete Kultur bleibt in der Liste: Ob du sie streichst, entscheidest du, und [`crop-selection`](crop-selection.md) prüft die Alternativen. Die Zeilen zur Standortgeschichte nennen Standorte, keine Beete: Der Datenbestand hat keine Quelle für Beete.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `SEASON REVIEW: <season> — <n> reviewed, <m> not reviewed — <slug>` | `<n>` Pflanzen haben einen Verlaufsdatensatz; `<m>` wurden über die Grenze hinaus genannt oder konnten nicht gelesen werden |
| `SEASON REVIEW: not reviewed (invalid season) — <season>` | die Saison ist weder ein Jahr noch eine gültige Spanne |

## Quellen

- [`recipes/season-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/season-review.yaml) — die Parameter, die Auflistung archivierter Pflanzen und das Berichtsformat
- [`.claude/skills/garden-review/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-review/SKILL.md) — der Verlaufsdatensatz, die Lehren und der Block für den nächsten Zyklus
- [`spec/process/garden-and-season-review/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-and-season-review/de.md) — der Prozess, den dieses Rezept umsetzt
