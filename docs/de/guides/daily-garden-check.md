---
title: Tägliche Gartenprüfung
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Tägliche Gartenprüfung

Ein Garten hält viele kleine Fragen zugleich: Was ist fällig, was sieht falsch aus, was braucht nichts. `daily-garden-check` ist der tägliche Blick. Er liest einen Kamerplanter-Garten, führt die Nährstoff-, Schädlings-, Bewässerungs- und Düngeprüfung für die Pflanzen aus, die du nennst, und ordnet alles in einer Liste danach, was zuerst Aufmerksamkeit verdient. Jeder Eintrag sagt, ob er eine Beobachtung oder eine Empfehlung ist, worauf er ruht, wie sicher er ist und was ihn ändern würde. Was keine Handlung ergibt, weil der Beleg fehlt, steht ebenfalls dabei, mit der Beobachtung, die ihn liefern würde.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz, plant nichts ein und hat kein Anwendungsrezept. „Nichts zu tun“ ist ein zulässiges Ergebnis, und die Prüfung füllt die Liste nicht auf, damit sie nützlich aussieht.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und seine Skills wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `plant-context-collect`, `diary-measurements-read`, `nutrient-imbalance-assess`, `pest-pressure-assess`, `watering-decision`, `fertilization-decision`, `decision-policy` und `care-planning` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe daily-garden-check \
  --params tenant=my-garden \
  --params plants="plant-1,plant-2"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `plants` | nein | nur die Gartenebene: fällige Aufgaben und Pflanzdurchläufe. Die Prüfungen je Pflanze laufen nicht |

`plants` ist eine durch Kommas getrennte Liste von Pflanzenschlüsseln. **Höchstens fünf werden geprüft**, in der Reihenfolge, in der du sie nennst; jeder weitere Schlüssel wird als nicht geprüft gemeldet. Die Grenze hält die Zahl der Aufrufe je Pflanze klein: Die Prüfung liest nie jede Pflanze eines Gartens.

## Was sie ansieht

| Domäne | Status |
|--------|--------|
| Nährstoffe | für die genannten Pflanzen geprüft |
| Schädlinge | für die genannten Pflanzen geprüft |
| Bewässerung | für die genannten Pflanzen geprüft |
| Düngung | für die genannten Pflanzen geprüft |
| Pflanzengesundheit und Schädlingsmanagement | **nicht verfügbar** (`plant-health-assessment`, `pest-ipm-planning`, [#48](https://github.com/nolte/kamerplanter-goose/issues/48)) |
| Wachstumsstadium und Wetter | **nicht verfügbar** (`growth-stage-assessment`, `weather-impact-analysis`, [#49](https://github.com/nolte/kamerplanter-goose/issues/49)) |

Die Bewässerungs- und die Düngeprüfung fügen keine eigenen Aufrufe hinzu: Sie arbeiten auf dem, was die anderen Prüfungen schon gesammelt haben, und liefern ihre Befunde in der eigenen Form des Pflegeplans. **Rechne damit, dass die Bewässerung bei `insufficient evidence` endet**, wenn für eine Pflanze kein Feuchtewert vorliegt; das ist das gewöhnliche Ergebnis (siehe die [Bewässerungsentscheidung](watering-decision.md) und die [Düngeentscheidung](fertilization-decision.md)). Eine nicht verfügbare Domäne wird im Bericht genannt und nie durch eine andere ersetzt. Sobald einer dieser Skills existiert, klinkt er sich hier ein, ohne dass sich die Regeln des Pflegeplans ändern.

## Was die Liste bedeutet

- **Eine Beobachtung** ist, was ein Tool oder ein Dokument gesagt hat, mit Quelle und Zeit. **Eine Empfehlung** ist ein Vorschlag an dich, mit Beleg, Konfidenz, Unsicherheit und fehlenden Daten. Eine **Mutation** wird nur benannt: Die Prüfung sagt, welches zustandsändernde Tool ein späterer Anwendungsschritt aufrufen würde, und ruft nichts auf.
- **Reihenfolge.** Die Einträge sind nach Dringlichkeit geordnet (`now`, `soon`, `routine`, `watch`), dann nach Konfidenz, dann nach Pflanze und Domäne. Die Dringlichkeit kommt nur daraus, was eine Domäne selbst über die Folge des Nichtstuns gesagt hat. Eine fällige Pflegeaufgabe ist höchstens `routine`.
- **Eine fällige Aufgabe ist kein Grund zu handeln.** Sie ist eine Anfrage des Zeitplans, keine Messung der Pflanze, und die Prüfung empfiehlt nie Gießen oder Düngen, nur weil eine Erinnerung fällig ist.
- **Ein Verdacht ist eine Beobachtung.** Lässt die Nährstoff- oder Schädlingsprüfung eine Richtung oder einen Kandidaten unbestimmt, bekommst du genau das, keine Empfehlung.
- **Kein Beleg, keine Handlung.** Ein Zustand, zu dem der Datenbestand nichts sagt, steht unter *keine Handlung, Beleg unzureichend*, mit der Beobachtung, die ihn klären würde.

## Das Ergebnis lesen

Der Bericht ist der Pflegeplan in fünf Blöcken: der Kopf, die Einträge, die benannten Mutationen, die Einträge ohne Handlung und der Status jeder Domäne. Danach je Pflanze eine Zeile, die sagt, wie viele Tagebucheinträge aufgelistet, geöffnet und ohne Messwerte gefunden wurden; diese Zeile zeigt dir, ob das Tagebuch überhaupt gelesen wurde.

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `APPLY: none — this check reports and applies nothing` | hier lässt sich nichts anwenden |
| `CARE: <a> actions, <n> no action — <slug>` (immer die letzte Zeile) | wie viele Empfehlungen gemacht wurden und wie viele Einträge ohne Handlung sind |

Ein Bericht ohne Handlungen und mit einer langen Liste von Einträgen ohne Handlung ist das ehrliche Ergebnis, wenn die Eingaben des Gartens dünn sind.

## Wie weit „deterministisch“ reicht

Die Fakten des Pflegeplans sind eine Funktion der Blöcke, die den Skills übergeben wurden: die Eintragskennungen, Arten, Dringlichkeiten, die Reihenfolge, die Konfidenzstufen, die benannten Mutationen und die Einträge ohne Handlung. Zwei Läufe über dieselben Blöcke ergeben dieselben Fakten; der Wortlaut drumherum kann abweichen. Das ist festgelegt, aber noch nicht an einer festen Vorlage geprüft.

## Quellen

- [`recipes/daily-garden-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/daily-garden-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/care-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/care-planning/SKILL.md) — die Einträge, die Dringlichkeitsregeln und die Reihenfolge
- [`.claude/skills/diary-measurements-read/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/diary-measurements-read/SKILL.md) — das Lesen des Tagebuchs hinter der Nährstoffprüfung
- [`spec/process/care-planning-and-daily-check/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/care-planning-and-daily-check/de.md) — der Prozess, den dieses Rezept umsetzt
