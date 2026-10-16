---
title: Gartenplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Gartenplan

Ein Plan sagt, wann jede gewählte Kultur gesät wird, wann sie umgepflanzt wird, wann die Ernte erwartet wird und wohin sie kommt. `garden-plan` macht aus den genannten Kulturen Vorschläge für Pflanzdurchläufe für einen Kamerplanter-Garten: Jeder Durchlauf hat eine stabile Kennung, eine Anbauweise, Fenster mit der Regel dahinter und eine Konfidenz. Was es nicht planen kann, führt es mit dem Grund auf.

Der Plan ist ein **Dokument zur Prüfung**. Er wendet nichts an, und unter den Kamerplanter-Werkzeugen, die dieses Repository gemessen hat, ist keines, das einen Pflanzdurchlauf, eine Aussaat- oder Pflanzaufgabe oder einen Plan anlegt. Die Rezepte, die einen Plan anwenden würden, werden in [#59](https://github.com/nolte/kamerplanter-goose/issues/59) geführt und existieren noch nicht.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine sechs Skills wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `site-analysis`, `crop-selection`, `planting-calendar`, `plant-planning` und `decision-policy` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.

## Ausführen

```sh
goose run --recipe garden-plan \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params beds="bed-1:2m2" \
  --params hardiness_zone=7b
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

## Was zu einem Durchlauf wird

- **Nur eine geeignete Kultur mit bekanntem Aussaatfenster oder Datum der Vorkultur.** Jede andere Kultur steht unter *nicht geplant*: abgelehnt (mit der verfehlten Bedingung), unentschieden (mit der fehlenden Eingabe) oder Fenster unbekannt (mit der fehlenden Eingabe).
- **Ein Durchlauf je Wachstumsperiode und Anbauweise.** Eine Art mit Sommer- und Winterperiode ergibt zwei Durchläufe. Ohne Anbauweise-Präferenz erscheint eine Kultur, die für beide Anbauweisen in Frage kommt, zweimal; das sind Alternativen, zwischen denen Sie wählen.
- **Die Kennung sagt, was der Durchlauf ist**: Art, Sorte oder `none`, Anbauweise und die Monate der Periode. Sie hängt nicht von der Reihenfolge ab, in der Sie die Kulturen aufgelistet haben.
- **Es wird kein Beet zugeordnet.** Das tut die Beetaufteilung. Die von Ihnen gelieferten Beete stehen im Plankopf.
- **Die Fruchtfolge ist immer unbekannt**, weil sie noch nicht gebaut ist; Nachbarn werden nicht als Fruchtfolgeregel gelesen.
- **Eine Folgesaat wird nur genannt, wo die Daten eine zeigen**: der letzte Erntemonat einer Periode vor dem ersten Saatmonat einer anderen. Beide Durchläufe sagen es, `precedes` am früheren und `follows` am späteren.

## Wie weit „deterministisch“ reicht

Die Plan-Fakten sind eine Funktion dessen, was Sie liefern: die Durchlaufkennungen, Anbauweisen, Fenster, Orte, ob eine Folgesaat genannt ist, die Hinweise zur Fruchtfolge, die Gründe für *nicht geplant* und die Konfidenzstufen. Zwei Läufe über dieselben Eingaben ergeben dieselben Plan-Fakten; der Text drumherum kann abweichen. Geprüft wurde das einmalig an einem erfundenen Beispiel aus als Text ausgeschriebenen Eingabeblöcken, nicht an einem laufenden Garten; dieses Beispiel liegt nicht in diesem Repository, die Prüfung lässt sich von hier aus also nicht wiederholen.

## Das Ergebnis lesen

Der Bericht ist eine Tabelle der Durchläufe, dann die Kulturen, die nicht geplant wurden, dann der Plankopf, die Begründung und die Belege hinter jedem Datum und der Anwendungsvertrag: was ein späterer Anwendungsschritt anlegen würde und dass dafür kein Werkzeug gemessen ist.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `PLAN: <r> runs, <n> not planned — <slug>` | wie viele Durchläufe vorgeschlagen und wie viele Kulturen ausgelassen wurden |
| `APPLY: no write tool measured (nolte/kamerplanter-goose#59)` | der Plan lässt sich von hier aus nicht anwenden |

Ein Plan mit wenigen Durchläufen und einer langen Liste *nicht geplant* ist das ehrliche Ergebnis, wenn die Eingaben des Gartens nicht geliefert wurden.

## Quellen

- [`recipes/garden-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/plant-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-planning/SKILL.md) — die Durchläufe, ihre Kennungen und der Anwendungsvertrag
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — die Fenster hinter jedem Durchlauf
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — welche Kulturen geplant werden dürfen
- [`spec/process/plant-planning-and-planting-calendar/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/de.md) — der Prozess, den dieses Rezept umsetzt
