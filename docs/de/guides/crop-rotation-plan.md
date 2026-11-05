---
title: Fruchtfolgeplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Fruchtfolgeplan

Eine Fruchtfolge hält eine Pflanzenfamilie einige Saisons aus einem Beet fern, nachdem sie dort stand. `crop-rotation-plan` nimmt die Kulturen, die Sie anbauen wollen, Ihre Beete und was vorher darin stand, und schlägt für die genannten Saisons eine Familie je Beet und Saison vor. Jede Kultur, die es für ein Beet betrachtet hat, erhält ein Urteil mit der Regel dahinter; jeder Konflikt wird aufgeführt, auch einer, den Ihre eigene Festlegung verursacht; jede ausgelassene Kultur wird mit dem Grund aufgeführt.

Der Plan ist ein **Dokument zur Prüfung**. Er hält nichts fest, und unter den Kamerplanter-Werkzeugen, die dieses Repository gemessen hat, ist keines, das eine Beetzuordnung, eine Fruchtfolge oder einen Pflanzdurchlauf festhält. Das Rezept, das einen Plan festhalten würde, wird blockiert in [#68](https://github.com/nolte/kamerplanter-goose/issues/68) geführt und existiert noch nicht.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine beiden neuen Skills, `rotation-history-collect` und `crop-rotation-planning`, wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Ob jede Art eine Familie trägt und was eine archivierte Pflanze trägt, ist nicht gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `rotation-history-collect`, `crop-rotation-planning` und `decision-policy` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Wissen Sie, was der Katalog dem Lauf nicht sagen kann.** Die Familie einer Kultur stammt aus dem `family_key` des Artdatensatzes und aus nichts anderem. Der Katalog hat keine Beete, keine Beetvorgeschichte, keinen Fruchtfolgeabstand und keine Reihenfolge des Nährstoffbedarfs. Diese kommen von Ihnen, oder sie bleiben unbekannt.

## Ausführen

```sh
goose run --recipe crop-rotation-plan \
  --params tenant=my-garden \
  --params crops="solanum-lycopersicum,phaseolus-vulgaris,brassica-oleracea" \
  --params seasons="2027,2028,2029" \
  --params beds="bed-1,bed-2,bed-3" \
  --params bed_history="bed-1:2026:solanum-lycopersicum,bed-2:2026:none" \
  --params rotation_years=4
```

Die Schlüssel oben sind Beispiele; verwenden Sie die Artschlüssel, die der Katalog Ihres Gartens trägt.

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `crops` | ja | — |
| `seasons` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `beds` | nein | nur die in `bed_history` oder in einer Festlegung genannten Beete werden geplant |
| `bed_history` | nein | die Vorgeschichte eines Beets stammt nur aus dem Katalog, und ein Beet, das der Katalog nicht abdeckt, bleibt unbekannt |
| `rotation_years` | nein | eine Wiederholung derselben Familie wird als `repeat — interval unknown` gemeldet, nie als Konflikt; jede andere Kultur ist bestenfalls `unknown`, weil der Lauf ohne Abstand die ganze Vorgeschichte des Beets bräuchte |
| `demand_sequence` | nein | die Bedarfsreihenfolge wird nicht ausgewertet |
| `constraints` | nein | keine Festlegung und kein Ausschluss |

`crops` ist eine durch Kommas getrennte Liste; jeder Eintrag ist ein Artschlüssel oder ein Artschlüssel und ein Sortenschlüssel, durch einen Doppelpunkt verbunden. `seasons` müssen aufeinanderfolgende Jahre sein; eine Lücke hält den Lauf an. `beds` ist eine durch Kommas getrennte Liste von Namen, jeder wahlweise gefolgt von `:area_or_volume`.

## Beetvorgeschichte und Abstand liefern

- **Die Beetvorgeschichte** ist `bed:season:crop`, durch Kommas getrennt, zum Beispiel `bed-1:2026:solanum-lycopersicum`. Schreiben Sie `bed:season:none` für eine Saison, in der das Beet leer stand. Die Vorgeschichte eines Beets zählt ab seinem frühesten Eintrag: Ab dieser Saison nimmt der Lauf, was Sie geschrieben haben, als vollständig, eine Saison, die Sie nicht genannt haben, trug also keine Kultur. Saisons vor Ihrem frühesten Eintrag bleiben unbekannt, `bed-2:2026:none` deckt also 2026 und danach ab und nichts davor. Ein Beet ganz ohne Vorgeschichte bleibt `unknown`, wo der Abstand vor die geplanten Saisons reicht.
- **Die Vorgeschichte aus dem Katalog** wird auch verwendet, aber nur, wo der Standortschlüssel einer Pflanze genau dem Beetnamen entspricht. Jeder andere Standort wird als Kontext aufgeführt. Die Saison einer Katalogpflanze ist das Jahr, in dem sie gepflanzt wurde. Ein gescheitertes oder unvollständiges Lesen wird gemeldet und nie als „hier wuchs nichts“ gelesen.
- **`rotation_years`** ist der kleinste Abstand in Saisons, in dem eine Familie wieder in einem Beet stehen darf. Mit `4` ist eine Familie, die 2026 gepflanzt wurde, 2027, 2028 und 2029 ein Konflikt und 2030 erlaubt. Keine Zahl ist eingebaut, weil der Katalog keine enthält.
- **`demand_sequence`** ist eine Reihenfolge von Bedarfsklassen, als Text mit dem `nutrient_demand_level` des Katalogs verglichen, zum Beispiel `heavy_feeder,medium_feeder,light_feeder,green_manure`. Nach einer Kultur einer Klasse wird die nächste Klasse der Reihenfolge bevorzugt; `green_manure` passt auch zu einer Kultur, die der Katalog als für Gründüngung geeignet kennzeichnet. Sie ordnet nur und ergibt nie einen Konflikt.
- **`constraints`** werden durch Semikolons getrennt. `pin=bed-1:2027:solanum-tuberosum` setzt diese Kultur dorthin, was auch immer ihr Urteil ist, und führt jede Regel auf, die sie bricht. `exclude=bed-3:brassica-oleracea` hält diese Kultur aus diesem Beet heraus. Jeder andere Text wird als nicht ausgewertet aufgeführt.

## Was die Urteile bedeuten

| Urteil | Bedeutet |
|--------|----------|
| `clear` | keine Kultur derselben Familie stand innerhalb des Abstands im Beet, und die Vorgeschichte deckt diese Spanne ab |
| `conflict` | eine Kultur derselben Familie stand innerhalb des von Ihnen angegebenen Abstands im Beet |
| `repeat — interval unknown` | eine Kultur derselben Familie stand früher im Beet, und Sie haben keinen Abstand angegeben, um es zu beurteilen |
| `caution` | nichts anderes trifft zu, und eine Pflanze an diesem Beet hat eine festgehaltene Inspektion; der Katalog hält keinen Wirtskreis fest, daher lässt sich ein Schädling nicht an eine Familie binden |
| `unknown` | die Kultur hat keine festgehaltene Familie, eine Kultur im Fenster hat keine, das Beet hat einen Eintrag mit unbekannter Saison, die Vorgeschichte des Beets reicht nicht weit genug zurück, oder ein Lesen der Inspektionen für das Beet ist gescheitert |

Je Beet und Saison wählt der Lauf eine Familie, bevorzugt `clear`, dann `caution`, dann `unknown`, dann eine Familie, die in dieser Saison weniger Beete schon tragen, dann die Bedarfsreihenfolge. Eine Familie mit `conflict` oder `repeat — interval unknown` wird nie gewählt, außer Sie haben sie festgelegt. Ein Beet in einer Saison ohne wählbare Familie ist `open`.

## Was der Plan nicht tut

- **Er hält nichts fest.** Es gibt kein Werkzeug, um ihn festzuhalten.
- **Er teilt kein Beet auf.** Er nennt eine Familie und ihre Kulturen je Beet und Saison. Fläche, Abstände, Nachbarn und Folgesaaten sind Aufgabe des [Beetplans](bed-layout-plan.md) und des [Folgesaatplans](succession-plan.md), die diesen Plan lesen.
- **Er nennt keine Termine.** Aussaat- und Erntefenster kommen aus dem [Gartenplan](garden-plan.md). Jede Kultur ist als `species_key/cultivar_key` geschlüsselt, dasselbe Präfix wie ein Durchlauf des Gartenplans, sodass beide nebeneinander gelesen werden können.
- **Er erinnert sich nicht.** Keine Familie, kein Abstand und keine Bedarfsreihenfolge stammt aus Allgemeinwissen, und Nachbarn werden nicht als Fruchtfolgeregel gelesen.

## Das Ergebnis lesen

Der Bericht zeigt, welche Skills geladen wurden, dann eine Tabelle der Beete und Saisons, dann die Konflikte, die nicht platzierten Kulturen, den Kopf des Fruchtfolgeplans und die Beetvorgeschichte und den Anwendungsvertrag.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `ROTATION: <p> placements, <c> conflicts, <u> unknown — <slug>` | wie viele Stellen (Beet, Saison) eine gewählte oder festgelegte Familie tragen, wie viele Konflikte der Plan enthält und wie viele Urteile über Kulturen unbekannt waren |
| `APPLY: no write tool measured (nolte/kamerplanter-goose#68)` | der Plan lässt sich von hier aus nicht festhalten |

Ein Plan voller `unknown` ist das ehrliche Ergebnis, solange die Familien im Katalog nicht befüllt sind oder Ihre Beetvorgeschichte fehlt. `bed_history` und `rotation_years` zu liefern macht daraus Urteile.

## Wie weit „deterministisch“ reicht

Die Plan-Fakten sind eine Funktion dessen, was Sie liefern: die Platzierungen, die Urteile mit ihren Regeln, die Konflikte, die Gründe für *nicht platziert* und die Belegstufen. Zwei Läufe über dieselben Eingaben sollten dieselben Plan-Fakten ergeben; der Text drumherum kann abweichen. Die Reihenfolge, in der Sie Kulturen oder Beete aufführen, ändert sie nicht. Geprüft wurde das dreimal an einem erfundenen, als Text ausgeschriebenen Beispiel — vier Beete, drei Saisons, eine Kultur ohne Familie, eine widersprechende Festlegung, eine Wiederholung derselben Familie und eine Inspektion, einmal mit und einmal ohne Abstand —, nicht an einem laufenden Garten. In einer ersten Reihe stimmten Platzierungen, Urteile und nicht platzierte Kulturen überein, die aufgeführten Konflikte und die Stufen der Urteile nicht. Nachdem der Skill in beiden Punkten eindeutig gemacht wurde, stimmte eine zweite Reihe aus drei Läufen bei den Konflikten und bei jeder Stufe überein; zwei ihrer Läufe waren in jedem Plan-Fakt gleich, und einer ordnete in der Variante ohne Abstand ein Beet anders, worauf die Reihenfolge der Ordnungsschlüssel strenger formuliert wurde. Diese letzte Änderung wurde nicht erneut gemessen. Das Beispiel liegt nicht in diesem Repository.

## Quellen

- [`recipes/crop-rotation-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/crop-rotation-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/crop-rotation-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-rotation-planning/SKILL.md) — die Urteile, die Auswahl und der Anwendungsvertrag
- [`.claude/skills/rotation-history-collect/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/rotation-history-collect/SKILL.md) — was aus dem Katalog gelesen wird
- [`spec/process/crop-rotation-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/crop-rotation-planning/de.md) — der Prozess, den dieses Rezept umsetzt
