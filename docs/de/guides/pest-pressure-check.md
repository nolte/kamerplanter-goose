---
title: Schädlingsdruck-Prüfung
audience: [plant-owner]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Schädlingsdruck-Prüfung

Du vermutest, dass etwas an einer Pflanze frisst, und willst wissen, ob dieser Verdacht dem Datenbestand standhält, bevor du irgendetwas spritzt. `pest-pressure-check` prüft einen Verdacht gegen das, was der Garten tatsächlich hergibt — den Kontext der Pflanze, ihre Inspektionshistorie und den Schädlings- beziehungsweise Krankheitskatalog — und nennt eine Gegenmaßnahme nur, wenn die Bestimmung sie trägt.

„Nicht widerlegt“ ist ein häufiges und legitimes Ergebnis. Es ist schwächer als „bestimmt“, und das Rezept ist so geschrieben, dass beides getrennt bleibt.

Dieser Lauf **liest** deinen Garten **nur**. Er legt nie eine Inspektion an, bestätigt keine Aufgabe und schaltet nichts.

## Bevor du startest

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect` und `pest-pressure-assess` aus `.claude/skills/`, und die Skill-Auffindung erfolgt relativ zum Arbeitsverzeichnis des Goose-Prozesses. Ein anderswo gestarteter Lauf verliert den Skill stillschweigend und liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze** — den numerischen Schlüssel, nicht die lesbare `instance_id`. Die [Pflanzenstammdaten-Prüfung](plant-master-data-check.md) druckt beide.

## Ausführen

```sh
goose run --recipe pest-pressure-check \
  --params plant_key=11441519 \
  --params suspicion="klebrige Blätter, kleine weiße Fliegen an der Unterseite" \
  --params tenant=my-garden
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `suspicion` | nein | der Lauf arbeitet allein aus der erfassten Inspektionshistorie der Pflanze |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |

`suspicion` nimmt entweder ein beobachtetes Symptom oder einen vermuteten Organismus. Zu beschreiben, was du gesehen hast, ist meist die bessere Eingabe: Einen Organismus zu benennen lädt den Lauf ein, ihn zu bestätigen; ein Symptom zu beschreiben lässt ihn Kandidaten ausschließen.

## Wie entschieden wird

Jede Aussage wird danach eingeordnet, worauf sie sich stützt, und eine niedrigere Stufe hebt eine höhere nie auf.

| Stufe | Beleg | Gewicht |
|:-----:|-------|---------|
| 1 | Eine erfasste Inspektion, die den Organismus benennt, mit Befallsstärke und Befunden | Belegt das Vorhandensein allein |
| 2 | Katalogfelder — `pest_type`, `lifecycle_days`, `optimal_temp_*`, `damage_symptoms` oder die `environmental_triggers` einer Krankheit | Bestätigt oder widerlegt einen Kandidaten; belegt nie das Vorhandensein |
| 3 | Situationspassung — Artkategorie, Phase, Jahreszeit, Pflegehistorie, Abgeschlossenheit | Engt den Kandidatenkreis ein, wählt nie daraus aus |
| 4 | Sichtbare Symptome auf einem Foto | Verorten und stufen ein. Belegen Vorhandensein nur bei einem selbst sichtbaren Organismus, nie bei einem aus seinem Schaden erschlossenen |
| 5 | Allgemeines Wissen über das Taxon, das nicht im Datensatz steht | Nur Denkhilfe, und immer als „nicht erfasst“ gekennzeichnet |

**Eine Behandlung wird nur auf Stufe 1 vorgeschlagen, oder auf Stufe 4 plus einer unwidersprochenen Stufe 2.** Darunter ist das Ergebnis die Beobachtung, die es klären würde — meist eine benannte Monitoring-Methode, nicht noch ein Foto.

Der Schädlingskatalog ist dünner als der Krankheitskatalog, und das Rezept sagt das, statt die Lücke zu füllen. `get_pest` führt keine Wirtspflanzen, keine Feuchte-Ökologie, keine Monitoring-Hinweise und keine befallenen Pflanzenteile — jede Argumentation darauf läuft auf Stufe 5. `get_disease` führt `environmental_triggers`, `incubation_period_days` und `pathogen_type`, dieselbe Feuchte-Argumentation läuft für eine Krankheit also auf Stufe 2. Der Bericht sagt, in welchem der beiden Fälle er sich befindet.

## Das Ergebnis lesen

Der Bericht beginnt mit einer Feldtabelle — Kandidat, Status, Belegstufe, Zahl der Inspektionen und die Tests, die der Datenbestand nicht tragen konnte — und liefert dann die Begründung in höchstens fünf Sätzen, jeden verworfenen Kandidaten mit dem Test, der ihn verworfen hat, und die empfohlenen Maßnahmen in IPM-Reihenfolge samt Wartezeiten, geprüft gegen die Erntesituation der Pflanze.

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `PEST: identified — <Kandidat> (tier <n>)` | das Vorhandensein ist belegt, eine Maßnahme darf folgen |
| `PEST: not contradicted — <Kandidat> (tier <n>)` | der Kandidat hat jeden durchführbaren Test überstanden — was nicht heißt, dass er da ist |
| `PEST: rejected — <Kandidat> (tier <n>)` | ein Test hat den Kandidaten ausgeschlossen |
| `PEST: undetermined — none (tier <n>)` | nichts Tragfähiges; eine zweite Zeile benennt die eine klärende Beobachtung |

Alles außer `identified` schließt mit dieser zweiten Zeile. Zwei Mittel mit demselben Wirkstoff werden nie als Alternativen angeboten, weil das Resistenzen züchtet — und wo der Datensatz gar keinen Wirkstoff führt, sagt der Bericht, dass die Rotationsaussage nicht getroffen werden kann.

Einen Mangel, den der Lauf im Katalog selbst findet, meldet er als solchen, adressiert an [nolte/kamerplanter](https://github.com/nolte/kamerplanter), statt ihn stillschweigend zu umgehen.

## Quellen

- [`recipes/pest-pressure-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/pest-pressure-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/pest-pressure-assess/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/pest-pressure-assess/SKILL.md) — die Belegleiter, die Falsifikationstests und was der Datensatz nicht führt
- [`spec/process/pest-pressure-assessment/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/pest-pressure-assessment/de.md) — der Prozess, den dieses Rezept umsetzt
