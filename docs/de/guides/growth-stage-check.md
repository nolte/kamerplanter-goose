---
title: Prüfung des Wachstumsstadiums
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Prüfung des Wachstumsstadiums

Der Datenbestand sagt, dass eine Pflanze in einer Phase steht, weil jemand sie eingetragen hat, oft vor Wochen. `growth-stage-check` fragt für eine Pflanze, ob das noch zur Pflanze passt: **Das erfasste Stadium passt, es ist fraglich, oder es gibt zu wenig Beleg, um es zu sagen.** Ein fragliches Stadium sagt auch, in welche Richtung es zeigt: Die Pflanze wirkt ihrem Eintrag **voraus** (`ahead`), **hinterher** (`behind`), oder der Beleg ist **unklar** (`unclear`). Jede Antwort sagt, worauf sie ruht, wie sicher sie ist, was sie ändern würde und was fehlt.

Der Lauf **liest nur**. Er ändert keine Phase, schreibt keinen Tagebucheintrag und hat kein Anwendungsrezept. Wirkt das Stadium fraglich, nennt der Bericht den Phasenwechsel, den eine Person eintragen könnte, und nichts ruft ihn auf. Er ruft kein Home-Assistant-Tool auf.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Rechne mit „zu wenig Beleg“

Alter, Zeit in der Phase, die Tage bis zur Reife der Sorte und die Blüte- und Erntemonate der Art sagen, was **erwartet** wird. Sie sind kein Blick auf die Pflanze und verorten allein kein Stadium. Etwas muss sagen, wo die Pflanze jetzt steht: deine eigene Beobachtung (`observations`), ein Tagebuch-Messwert, der die Entwicklung eindeutig beschreibt, oder eine Fotolesung, die eine dieser Erwartungen stützt. Ohne eines davon ist die ehrliche Antwort `insufficient evidence`. **Das ist das gewöhnliche Ergebnis, kein Fehlschlag des Laufs.** Der Bericht nennt, welche Beobachtung es klären würde, meist ein Satz von dir dazu, was du siehst.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `decision-policy` und `growth-stage-assessment` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn neben der lesbaren `instance_id` aus.
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe growth-stage-check \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="erste Blütenknospen offen" \
  --params as_of=2026-06-12
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `observations` | nein | nichts von dir zur gegenwärtigen Entwicklung der Pflanze |
| `entry_key` | nein | kein Foto wird gelesen |
| `temperatures` | nein | keine Wachstumsgradtage: Der Server hat keinen Temperaturverlauf |
| `latitude` | nein | keine Tageslänge für draußen: Der Server hat dafür kein Feld |
| `light` | nein | kein Lichtplan für drinnen |
| `as_of` | nein | das Datum der jüngsten gelesenen Beobachtung wird verwendet; ohne eine wird keine Zeit berechnet |

## Was es entscheidet

| Was bekannt ist | Ergebnis |
|-----------------|----------|
| die Phase ist unaufgelöst oder fehlt | `insufficient evidence` |
| deine Beobachtung, eine Inspektion oder ein eindeutiger Messwert, der zur erfassten Phase passt | `recorded stage consistent` |
| eines davon, das der erfassten Phase widerspricht | `recorded stage questionable` |
| eine Fotolesung, passend oder widersprechend, gestützt durch eine zeitliche Erwartung | passend oder fraglich |
| nur Erwartungen, Wachstumsgradtage oder ein ungestütztes Foto | `insufficient evidence` |

- **Eine unaufgelöste Phase ist keine normale Phase.** Der Phasenstatus kann `unresolved` liefern, was wie ein Ergebnis aussieht und keines ist; der Bericht sagt, dass das erfasste Stadium fehlt.
- **Wachstumsgradtage sind Kontext.** Sie werden nur aus einer täglichen Reihe, die du lieferst, und der Basistemperatur der Art berechnet, mit genannter Methode und Spanne. Kein Ziel an Wachstumsgradtagen für ein Stadium oder für die Reife ist festgehalten, daher verorten sie allein nie ein Stadium.
- **Die Tageslänge wird berechnet, die Reaktion der Pflanze darauf ist nicht bekannt.** Draußen aus deinem Breitengrad, drinnen aus deinem Lichtplan. Kein Artfeld hält eine Empfindlichkeit für die Tageslänge fest, daher sagt der Bericht dazu `no source`.
- **Der Phasenverlauf wird so gemeldet, wie er zurückkommt.** Seine Felder sind hier nirgends festgehalten, also wird nichts über sie angenommen.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `GROWTH STAGE: recorded stage consistent — <plant_key>` | eine Beobachtung der Pflanze passt zu ihrer erfassten Phase |
| `GROWTH STAGE: recorded stage questionable (<direction>) — <plant_key>` | eine Beobachtung widerspricht ihr; sieh dir die Pflanze an und entscheide, ob du eine andere Phase einträgst |
| `GROWTH STAGE: insufficient evidence — <plant_key>` | nichts sagt, wo die Pflanze jetzt steht; der Bericht nennt, was es sagen würde |
| `GROWTH STAGE: not assessed — <plant_key>` | ein Schritt ist fehlgeschlagen, und keine Beurteilung kam zustande |

Der Bericht trägt außerdem einen Übergabeblock für die Ernteplanung: das erfasste und das geschätzte Stadium, die Tage in der Phase gegen ihre typische Dauer, die Tage seit dem Pflanzen gegen die Tage bis zur Reife der Sorte, die Wachstumsgradtage mit ihren Eingaben und die Tageslänge, jedes mit Grund als fehlend markiert, wo es fehlt.

## Quellen

- [`recipes/growth-stage-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/growth-stage-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/growth-stage-assessment/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/growth-stage-assessment/SKILL.md) — die Entscheidungstabelle, die Ableitungen und der Übergabeblock
- [`spec/process/growth-stage-and-weather-impact/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/growth-stage-and-weather-impact/de.md) — der Prozess, den dieses Rezept umsetzt
