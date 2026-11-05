---
title: Beurteilung der Pflanzengesundheit
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Beurteilung der Pflanzengesundheit

Eine Pflanze, die falsch aussieht, lädt zu einer einzigen selbstsicheren Antwort ein. `plant-health-assessment` gibt dir für eine Pflanze die ehrliche Fassung: **die Kandidaten-Erklärungen nebeneinander, welche davon überleben und was die Überlebenden unterscheiden würde.** Es führt die Prüfungen aus, die es schon gibt — Nährstoffe, Schädlinge und Krankheiten, Wachstumsstadium, Wetter — und verbindet, was sie liefern, mit deiner eigenen Beobachtung, einem optionalen Foto, den Messwerten im Tagebuch und dem Pflegeverlauf der Pflanze. Das Ergebnis nennt es nie eine Diagnose.

Der Lauf **liest nur**. Er behandelt nichts, hält nichts fest und hat kein Anwendungsrezept. Er ruft kein Home-Assistant-Tool auf: Wetter kommt nur aus dem, was du angibst.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-07 und am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Rechne mit „nur Vermutung“

Sieben Kandidatenklassen werden betrachtet: `nutrient`, `pest`, `disease`, `water`, `environment`, `development` und `abiotic handling/site`. Ein Kandidat ist nur dann **gestützt** (`supported`), wenn die Prüfung, der er gehört, ihr eigenes positives Ergebnis geliefert hat und etwas anderes, das nicht das Symptom selbst ist, ihn bekräftigt. Ein gelbes Blatt, ein Foto oder ein „das Wetter passte dazu“ ist eine **Vermutung** (`suspicion`), nie mehr. Und keine Prüfung wird überstimmt: Ein Schädling, den die Schädlingsprüfung *nicht widerlegt* ließ, bleibt hier *nicht widerlegt*.

Die meisten Läufe enden daher bei `suspicion only` oder `competing explanations`. **Das ist das nützliche Ergebnis, kein schwaches**: Der Bericht nennt für jedes Paar überlebender Kandidaten die eine Beobachtung, die sie trennen würde — oft „sieh dir die Blattunterseiten an“ oder „miss einmal die Substratfeuchte“. Ohne deine Beobachtung, ein Foto oder eine erfasste Inspektion gibt es kein Symptom zu beurteilen, und die Antwort ist `insufficient evidence`.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect`, `diary-measurements-read`, `plant-photo-read`, `nutrient-imbalance-assess`, `pest-pressure-assess`, `growth-stage-assessment`, `weather-impact-analysis`, `decision-policy` und `plant-health-assessment` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn neben der lesbaren `instance_id` aus.
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe plant-health-assessment \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params observations="lower leaves yellow between the veins, fine webbing under the leaves" \
  --params as_of=2026-06-12
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `observations` | nein | nichts von dir dazu, wie die Pflanze aussieht |
| `entry_key` | nein | kein Foto wird gelesen |
| `weather` | nein | jeder Wetterfaktor ist `no source`; der Kandidat `environment` ist nicht beurteilbar |
| `placement` | nein | jede Wetterexposition steht unter dem Vorbehalt, wo die Pflanze steht |
| `as_of` | nein | das Datum des jüngsten gelesenen Tagebucheintrags wird verwendet; ohne einen, oder mit `observations` und ohne `as_of`, wird keine Zeit berechnet |

## Was es entscheidet

| Gesamtergebnis | Bedeutet |
|----------------|----------|
| `leading explanation` | genau ein Kandidat ist gestützt; etwaige Vermutungen stehen daneben |
| `competing explanations` | zwei oder mehr Kandidaten sind gestützt, und der Bericht sagt, was sie trennen würde |
| `suspicion only` | nichts ist gestützt, aber mindestens ein Kandidat ist eine Vermutung |
| `no abnormality reported` | die gelesenen Quellen melden nichts Auffälliges |
| `insufficient evidence` | es gab gar keine Symptomquelle, keine Prüfung konnte etwas sagen, oder etwas Auffälliges wurde gemeldet, das keine Prüfung einordnen konnte |

- **Wetter ist eine Exposition, kein Symptom.** Expositionen stehen in einem eigenen Block, und ein Symptom wird mit einer nur als „consistent with“ verknüpft. Der Kandidat `environment` ist daher höchstens eine Vermutung.
- **Der Gesundheitseintrag ist eine Beobachtung.** In der [täglichen Gartenprüfung](daily-garden-check.md) steht er neben den Einträgen der anderen Prüfungen und zitiert sie; er wiederholt nie ihre Empfehlungen, damit nichts doppelt gezählt wird.
- **Ein Schädlings- oder Krankheitsverdacht geht weiter an den IPM-Plan.** Der Bericht übergibt den Kandidaten, so wie die Schädlingsprüfung ihn hinterließ, an den [IPM-Plan](pest-ipm-plan.md), der sagt, was dagegen zu tun ist und in welcher Reihenfolge.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `HEALTH: leading explanation — <plant_key>` | ein Kandidat ist durch seine eigene Prüfung und einen zweiten Beleg gestützt |
| `HEALTH: competing explanations — <plant_key>` | mehrere sind es; mach die unterscheidende Beobachtung, bevor du handelst |
| `HEALTH: suspicion only — <plant_key>` | das übliche Ergebnis; der Bericht nennt, was es klären würde |
| `HEALTH: no abnormality reported — <plant_key>` | nichts von dem, was gelesen wurde, sieht falsch aus |
| `HEALTH: insufficient evidence — <plant_key>` | nichts sagt, wie die Pflanze jetzt aussieht; gib `observations` oder ein Foto an |
| `HEALTH: not assessed — <plant_key>` | ein Schritt schlug fehl, und keine Differenzialbetrachtung kam zustande |

## Quellen

- [`recipes/plant-health-assessment.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/plant-health-assessment.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/plant-health-assessment/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-health-assessment/SKILL.md) — die Kandidatenklassen, die Status und die Gesamtergebnisse
- [`spec/process/plant-health-and-ipm-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-health-and-ipm-planning/de.md) — der Prozess, den dieses Rezept umsetzt
