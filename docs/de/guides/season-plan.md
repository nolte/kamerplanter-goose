---
title: Saisonplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Saisonplan

Derselbe Plan, auf ein Jahr gelegt. `season-plan` erstellt den Plan von [`garden-plan`](garden-plan.md) für die genannten Kulturen und zeigt seine Durchläufe Monat für Monat, mit den Folgesaaten, die der Plan nennt. Er entsteht nur aus dem Plan: Er fügt kein Datum hinzu.

Er wendet nichts an, und unter den Kamerplanter-Werkzeugen, die dieses Repository gemessen hat, ist keines, das es könnte ([#59](https://github.com/nolte/kamerplanter-goose/issues/59)).

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine sechs Skills wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `site-analysis`, `crop-selection`, `planting-calendar`, `plant-planning` und `decision-policy` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.

## Ausführen

```sh
goose run --recipe season-plan \
  --params tenant=my-garden \
  --params crops="allium-porrum"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `crops` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `goals` | nein | kein Ziel wird beurteilt; keines wird als erfüllt gemeldet |
| `harvest_window` | nein | die Erntepräferenz wird als unbekannt gemeldet; sie scheidet nie eine Kultur aus |
| `light`, `area_or_volume`, `water`, `constraints` | nein | der zugehörige Standortparameter ist unbekannt: Der Server hat dafür kein Feld |
| `hardiness_zone` | nein | die Härtezonen-Prüfung bleibt unentschieden: Kein Werkzeug sagt, in welcher Zone ein Garten liegt |
| `beds` | nein | für die Beetaufteilung werden keine Beete aufgeführt |
| `planting_method` | nein | jede Anbauweise mit bekanntem Aussaatfenster wird angeboten, jede als eigener Durchlauf |

`crops` ist eine durch Kommas getrennte Liste; jeder Eintrag ist ein Artschlüssel oder ein Artschlüssel und ein Sortenschlüssel, durch einen Doppelpunkt verbunden. `beds` ist eine durch Kommas getrennte Liste aus `name:area_or_volume`, zum Beispiel `bed-1:2m2,tub-1:10l`. `planting_method` ist `direct_sow` oder `indoor_then_transplant`; anderer Text ist keine Präferenz.

## Was die Monatsansicht zeigt

Eine Zeile je Durchlauf, zwölf Monatsspalten. Ein Monat ist mit **S** markiert, wo das Aussaatfenster ihn abdeckt, mit **I** für den Monat des Datums der Vorkultur, mit **T** ab dem Beginn des Umpflanzfensters und mit **H**, wo das Erntefenster ihn abdeckt. Ein unbekanntes Fenster wird nicht eingetragen, und die Ansicht sagt, dass sie unvollständig ist, und benennt es.

Die aufgeführten Folgesaaten sind die, die der Plan nennt (`precedes` und `follows`, mit beiden Durchlaufkennungen), und keine anderen.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `SEASON: <r> runs, <s> successions — <slug>` | wie viele Durchläufe die Ansicht zeigt und wie viele Folgesaaten der Plan nennt |
| `NOT PLACED: <Fenster>` | jedes Fenster, das sich nicht in den Kalender eintragen ließ, mit seinem Grund |

## Quellen

- [`recipes/season-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/season-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/plant-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-planning/SKILL.md) — die Durchläufe, ihre Kennungen und der Anwendungsvertrag
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — die Fenster hinter jedem Durchlauf
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — welche Kulturen geplant werden dürfen
- [`spec/process/plant-planning-and-planting-calendar/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/de.md) — der Prozess, den dieses Rezept umsetzt
