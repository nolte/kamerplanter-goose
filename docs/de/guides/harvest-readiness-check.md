---
title: Prüfung der Erntereife
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Prüfung der Erntereife

`harvest-readiness-check` beantwortet für eine Pflanze „Kann ich ernten?“: **reif (`ready`), nahe der Reife (`approaching`), nicht reif (`not ready`), nicht erntbar (`not harvestable`) oder zu wenig Beleg, um es zu sagen (`insufficient evidence`).** Jede Antwort sagt, worauf sie ruht, wie sicher sie ist, was sie ändern würde und was fehlt. Über der Antwort steht eine **Erntesperre**: Wenn du sagst, dass eine Behandlung ausgebracht wurde, kann ihre Wartezeit vor der Ernte (Karenz) die Ernte bis zu einem Datum sperren.

Der Lauf **liest nur**. Er erntet nichts, erfasst keine Ernte und keinen Ertrag, schreibt keinen Tagebucheintrag und hat kein Anwendungsrezept. Er ruft kein Home-Assistant-Tool auf, auch nicht den Intent `TimeTillErnte`, der wie eine Ernteantwort aussieht: Seine Wirkung ist nicht eingestuft.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Rechne mit „zu wenig Beleg“

Die Erntemonate der Art und die Tage bis zur Reife der Sorte sagen, was **erwartet** wird. Sie sind kein Blick auf die Kultur und entscheiden allein nichts. Aus den Tagen bis zur Reife wird überhaupt kein Erntedatum berechnet: Der Datenbestand sagt nicht, ob sie ab der Aussaat oder ab dem Auspflanzen zählen. Etwas muss sagen, wie die Kultur jetzt aussieht: deine eigene Beobachtung (`observations`), ein Tagebuch-Messwert, der die Reife eindeutig beschreibt, oder eine Fotolesung, die eine dieser Erwartungen stützt. Ohne eines davon ist die ehrliche Antwort `insufficient evidence`, und der Bericht nennt die Beobachtung, die es klären würde.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` und `harvest-planning` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn aus.
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe harvest-readiness-check \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="Schoten trocken und rasseln" \
  --params intended_use="Saatgutgewinnung" \
  --params treatments=neem-oil:2026-08-20 \
  --params as_of=2026-09-01
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `observations` | nein | nichts von dir dazu, wie die Kultur jetzt aussieht |
| `entry_key` | nein | kein Foto wird gelesen |
| `intended_use` | nein | die Reife wird ohne Verwendungszweck beurteilt; der Datenbestand hat dafür kein Feld |
| `weather` | nein | das Wetterrisiko ist `no source`; aus Home Assistant wird nichts gelesen |
| `temperatures` | nein | keine Wachstumsgradtage für das Wachstumsstadium |
| `treatments` | nein | die Erntesperre ist `unknown (no treatment date supplied)` |
| `as_of` | nein | das Datum, das die Beurteilung des Wachstumsstadiums festgelegt hat; ohne eines keine Zeitrechnung und keine Sperre |

## Was es entscheidet

| Was bekannt ist | Ergebnis |
|-----------------|----------|
| die Art erlaubt keine Ernte | `not harvestable` |
| deine Beobachtung, eine Inspektion oder ein eindeutiger Messwert, dass die Kultur reif ist | `ready` |
| eines davon, das eine noch nicht abgeschlossene Reifung zeigt | `approaching` |
| eines davon, das zeigt, dass die Kultur noch nicht reift | `not ready` |
| eine Fotolesung, gestützt durch die Erntemonate oder das Wachstumsstadium | eines der drei oben |
| nur der Kalender, das Alter der Pflanze, das Wachstumsstadium oder ein ungestütztes Foto | `insufficient evidence` |

- **Wetter ist ein Risiko, nie Reife.** Ein Frost oder ein Sturm, den du angibst, wird zu einem Risiko für den Erntezeitpunkt neben der Antwort; er verschiebt die Antwort nie.
- **Die Sperre braucht deine Daten.** Der Datenbestand hält keine Ausbringungsdaten fest, daher liest die Sperre nur die Behandlungen, die du aufführst, und ihre Wartezeit aus `get_treatment`.
- **Das Reife-Tool wird so gemeldet, wie es zurückkommt.** `get_harvest_readiness` wird aufgerufen, doch seine Felder sind hier nirgends festgehalten, daher trägt es kein Gewicht, und ein Fehler daraus hält den Lauf nicht an.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `HARVEST READINESS: ready (gate: clear) — <plant_key>` | eine Beobachtung sagt, dass die Kultur reif ist, und keine Behandlung sperrt sie |
| `HARVEST READINESS: ready (gate: blocked until <date>) — <plant_key>` | reif, aber warte, bis die Wartezeit abgelaufen ist |
| `HARVEST READINESS: approaching (gate: …) — <plant_key>` | reift; sieh bald wieder nach |
| `HARVEST READINESS: not ready (gate: …) — <plant_key>` | reift noch nicht |
| `HARVEST READINESS: not harvestable (gate: …) — <plant_key>` | die Art wird nicht für eine Ernte angebaut |
| `HARVEST READINESS: insufficient evidence (gate: …) — <plant_key>` | nichts sagt, wie die Kultur jetzt aussieht; der Bericht nennt, was es sagen würde |
| `HARVEST READINESS: not assessed — <plant_key>` | ein Schritt ist fehlgeschlagen, und kein Urteil kam zustande |

Um mehrere Pflanzen zu ordnen, nutze [`harvest-plan`](harvest-plan.md).

## Quellen

- [`recipes/harvest-readiness-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/harvest-readiness-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/harvest-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/harvest-planning/SKILL.md) — die Entscheidungstabelle, die Sperre und der Plan
- [`spec/process/harvest-readiness-and-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/harvest-readiness-and-planning/de.md) — der Prozess, den dieses Rezept umsetzt
