---
title: Ernteplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Ernteplan

`harvest-plan` bringt die Ernten von bis zu fünf Pflanzen in eine Reihenfolge: **welche zuerst kommt, in welchen Monat die Arbeit fällt und was sie sperrt oder begrenzt.** Für jede Pflanze gibt es dieselbe Reife-Antwort wie [`harvest-readiness-check`](harvest-readiness-check.md) — reif, nahe der Reife, nicht reif, nicht erntbar oder zu wenig Beleg — dazu ihr Erntefenster und ihre Sperre durch die Wartezeit, und ordnet die Pflanzen dann nach Fensterbeginn, dann nach Reife, dann nach Pflanzenschlüssel.

Der Lauf **liest nur**. Er erntet nichts und plant nichts ein, erfasst keine Ernte und keinen Ertrag, hat kein Anwendungsrezept und ruft kein Home-Assistant-Tool auf.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Was der Plan nicht wissen kann

Der Datenbestand hat **kein Feld für Ertrag, Lagerung oder Aufwand**. Der Plan zählt daher, was er zählen kann — Pflanzen je Monat des Fensterbeginns und Pflanzen, die reif oder nahe der Reife sind — und nennt Lagerung und Kapazität nur aus dem, was du lieferst. „Über der Kapazität“ erscheint nur, wenn deine Kapazität in derselben Einheit wie die Zählungen angegeben ist, etwa `3 plants per week`. Ohne deine Beobachtungen kommen die meisten Pflanzen als `insufficient evidence` zurück; das ist ehrlich, kein Fehlschlag.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` und `harvest-planning` aus `.claude/skills/`. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren.
- **Du brauchst die `plant_key`s der Pflanzen.** [plant-master-data-check](plant-master-data-check.md) gibt sie aus.

## Ausführen

```sh
goose run --recipe harvest-plan \
  --params tenant=my-garden \
  --params plants=42,43,44 \
  --params observations="42: Schoten trocken; 43: erste Früchte färben sich" \
  --params storage="kühler Keller, Platz für zwei Kisten" \
  --params capacity="3 plants per week" \
  --params treatments=43:neem-oil:2026-08-20 \
  --params as_of=2026-09-01
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `plants` | nein | nichts wird geplant; die Kulturen und Pflanzläufe des Gartens werden als Kontext gezeigt |
| `observations` | nein | je Pflanze nichts von dir dazu, wie die Kultur jetzt aussieht |
| `intended_use` | nein | die Reife wird ohne Verwendungszweck beurteilt |
| `storage` | nein | die Lagerung ist `not modeled in the measured catalog` |
| `capacity` | nein | die Arbeitslast besteht nur aus Zählungen |
| `weather` | nein | das Wetterrisiko ist `no source` |
| `treatments` | nein | jede Sperre ist `unknown (no treatment date supplied)` |
| `as_of` | nein | das Datum des Wachstumsstadiums je Pflanze; ohne eines keine Zeitrechnung und keine Sperre für diese Pflanze |

Höchstens fünf Pflanzen werden geplant, in der angegebenen Reihenfolge; die übrigen werden als nicht geplant aufgeführt. Eine Pflanze, die eine Wartezeit sperrt, wird mit ihrem Sperrdatum aufgeführt und nie davor eingeordnet.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `HARVEST PLAN: <n> planned, <m> not planned — <slug>` | `<n>` Pflanzen stehen in der Reihenfolge; `<m>` wurden über die Grenze hinaus genannt oder konnten nicht gelesen werden |
| `HARVEST PLAN: not planned — <slug>` | jeder Schritt ist fehlgeschlagen |

## Quellen

- [`recipes/harvest-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/harvest-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/harvest-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/harvest-planning/SKILL.md) — die Reihenfolge, die Arbeitslast und die Lagerregel
- [`spec/process/harvest-readiness-and-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/harvest-readiness-and-planning/de.md) — der Prozess, den dieses Rezept umsetzt
