---
title: IPM-Plan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# IPM-Plan

Sobald ein Schädling oder eine Krankheit vermutet wird, liegt die Spritze nahe. `pest-ipm-plan` ordnet für eine Pflanze, was getan werden könnte, so wie integrierter Pflanzenschutz es tut: **erst bestätigen und überwachen, dann die Umwelt korrigieren, dann kulturelle und mechanische Maßnahmen, und eine gezielte Behandlung nur, wenn sie gerechtfertigt ist.** Es führt zuerst dieselbe Beurteilung wie die [Schädlingsdruck-Prüfung](pest-pressure-check.md) für den Verdacht aus und plant nur für den Kandidaten, den diese Prüfung nennt, genau so, wie sie ihn hinterließ.

Der Lauf **liest nur**. Er behandelt nichts, setzt nichts frei und hält nichts fest, nicht einmal eine Inspektion; er hat kein Anwendungsrezept. Ein Überwachungsschritt nennt die Inspektion, die ein späterer Anwendungsschritt festhalten würde, und nichts ruft ihn auf. Er ruft kein Home-Assistant-Tool auf.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-07 und am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Rechne mit „Behandlung nicht gerechtfertigt“

Eine Behandlung wird nur an der eigenen Schwelle der Schädlingsprüfung erreicht: eine erfasste Inspektion, die den Organismus nennt, oder ein Foto, das ihn zeigt, zusammen mit Katalogdaten, die nicht widersprechen. Dieses Rezept liest kein Foto, daher erreicht hier nur eine erfasste Inspektion die Schwelle; für Fotobelege führe die [Beurteilung der Pflanzengesundheit](plant-health-assessment.md) mit `entry_key` aus. Ein beschriebenes Symptom allein erreicht sie nicht. **Unterhalb der Schwelle endet der Plan nach der Stufe der kulturellen und mechanischen Maßnahmen** und nennt die Überwachungsmethode, die den Beleg anheben würde — eine Gelbtafel, dein eigener Blick mit der Lupe auf die Blattunterseiten, eine Inspektion des befallenen Teils. Das ist das gewöhnliche Ergebnis, und der Überwachungsschritt ist der nützliche Teil.

Überwachungsmethoden und die Vorliebe eines Schädlings für trockene oder feuchte Luft sind im Schädlingskatalog **nicht festgehalten**; der Plan kennzeichnet sie als Allgemeinwissen. Eine Krankheit ist besser bedient: Ihr Datensatz nennt die Umweltauslöser, und die Umweltkorrektur zitiert sie. **Eine nicht beurteilte Umweltseite sperrt jede Behandlung**: Erst die Umwelt korrigieren, dann die Pflanze behandeln. Dieses Rezept führt keine Gesundheitsbeurteilung aus, daher ist bei einem Schädling die Umweltseite hier immer nicht beurteilt, und eine Schädlingsbehandlung ist aus diesem Rezept allein nie empfehlbar; der Bericht sagt, was sie beurteilen würde.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect`, `pest-pressure-assess`, `growth-stage-assessment`, `decision-policy` und `pest-ipm-planning` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn neben der lesbaren `instance_id` aus.
- **Für eine Pflanze, die du ernten wirst, gib `harvest_date` und `as_of` an.** Ohne eine Zeit bis zur Ernte kann keine Behandlung an ihr empfohlen werden (siehe unten).
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe pest-ipm-plan \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params suspicion="fine webbing and stippling on the leaf undersides" \
  --params placement="greenhouse" \
  --params harvest_date=2026-07-20 \
  --params as_of=2026-06-12
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `suspicion` | nein | der Plan arbeitet nur aus dem erfassten Inspektionsverlauf der Pflanze |
| `placement` | nein | geschlossen oder offen wird als erschlossen genannt; Nützlinge einsetzen und sie schonen sind verschiedene Ratschläge |
| `harvest_date` | nein | die Zeit bis zur Ernte kommt aus den Tagen bis zur Reife der Sorte oder steht nicht fest |
| `as_of` | nein | keine Zeit bis zur Ernte kann berechnet werden |

## Wartezeit und Erntedatum

Jede Behandlung im Plan trägt einen festen Block:

- **Voraussetzungen**: Die Bestimmung erreicht die Schwelle, mit ihrer Stufe; die früheren Stufen sind erledigt oder nicht verfügbar, mit dem Grund; ob die Pflanze geerntet werden darf, und die Zeit bis zur Ernte; und das Produktetikett sowie die örtlichen Pflanzenschutzregeln, die **nicht im Datenbestand stehen**: immer als „vor der Anwendung bestätigen“ aufgeführt und von dir zu prüfen. Sie entscheiden nicht, ob eine Behandlung empfehlbar ist; das tun die anderen Voraussetzungen.
- **Sicherheitsauflagen**, genau so aus dem Datenbestand zitiert, wie er sie hält, nie skaliert oder umgerechnet: die Wartezeit in Tagen, die Schutzausrüstung, die Dosierung je Liter, die Anwendungsart und der Wirkstoff.
- **Ausschlüsse**: Eine Behandlung, deren Wartezeit länger ist als die Zeit bis zur Ernte, wird **ausgeschlossen**. An einer Pflanze, die geerntet werden darf, ist eine Behandlung **nicht empfehlbar**, wenn die Zeit bis zur Ernte nicht bekannt ist oder der Datenbestand für sie keine Wartezeit trägt, weil sich ihre Wartezeit nicht prüfen lässt. Eine fehlende Wartezeit wird nie als null gelesen. Zwei Behandlungen mit demselben Wirkstoff werden nie als Alternativen angeboten.

Die Zeit bis zur Ernte ist dein `harvest_date` minus `as_of` oder, ohne Erntedatum, die Tage bis zur Reife der Sorte minus die Tage seit dem Pflanzen. Dieser Ersatzweg setzt eine Ernte bei Reife voraus und übergeht eine frühe oder fortlaufende Ernte — Babyleaf, Kräuter, Schnittsalat —, gib für solche `harvest_date` an. Sie wird nie aus dem Erntereife-Tool des Servers genommen, dessen Antwort hier nirgends festgehalten ist.

Biologische Maßnahmen kommen vor chemischen, und ein Nützling wird gegen das geprüft, was er tatsächlich frisst. Dass ein breit wirkendes Mittel eine Nützlingsfreilassung zunichtemacht, ist Allgemeinwissen, das der Datenbestand nicht trägt; der Plan nennt es als solches.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `IPM: <n> steps, treatment justified — <plant_key>` | mindestens eine Behandlung erreicht die Schwelle, und jede Voraussetzung gilt; lies ihren Sicherheitsblock, bevor du handelst |
| `IPM: <n> steps, treatment not justified — <plant_key>` | das übliche Ergebnis: Der Kandidat liegt unter der Schwelle, oder jede Behandlung ist ausgeschlossen oder nicht prüfbar |
| `IPM: <n> steps, treatment not applicable — <plant_key>` | die Schädlingsprüfung nennt keinen Schädlings- oder Krankheitskandidaten |
| `IPM: not planned — <plant_key>` | ein Schritt schlug fehl, und kein Plan kam zustande |

## Quellen

- [`recipes/pest-ipm-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/pest-ipm-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/pest-ipm-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/pest-ipm-planning/SKILL.md) — die vier Stufen, die Schwelle und der Behandlungsblock
- [`spec/process/plant-health-and-ipm-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-health-and-ipm-planning/de.md) — der Prozess, den dieses Rezept umsetzt
