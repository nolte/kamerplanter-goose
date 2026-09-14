---
title: Nährstoffbilanz-Prüfung
audience: [plant-owner]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Nährstoffbilanz-Prüfung

Eine Pflanze sieht nicht gut aus, und die Frage lautet, ob sie gedüngt werden soll. Diese Frage hat drei mögliche Antworten, und bei zweien davon ist Düngen der falsche Schritt: Die Pflanze kann unterversorgt sein, überversorgt, oder unfähig, Nährstoffe aufzunehmen, die längst da sind. `nutrient-imbalance-check` entscheidet für eine Pflanze, welcher Fall vorliegt — und schlägt eine Korrektur nur vor, wenn die Belege die Richtung tatsächlich festlegen.

Gelbe Blätter entscheiden das nicht. Das Rezept ordnet deshalb erst ein, worauf es sich stützt, und verweigert, wenn diese Einordnung zu schwach ist.

Dieser Lauf **liest** deinen Garten **nur**. `calculate_mixing_protocol` ist die eine erlaubte Ausnahme, weil es eine Mischung berechnet und nichts speichert.

## Bevor du startest

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect` und `nutrient-imbalance-assess` aus `.claude/skills/`, und die Skill-Auffindung erfolgt relativ zum Arbeitsverzeichnis des Goose-Prozesses. Ein anderswo gestarteter Lauf verliert den Skill stillschweigend und liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze** — den numerischen Schlüssel, nicht die lesbare `instance_id`. Die [Pflanzenstammdaten-Prüfung](plant-master-data-check.md) druckt beide nebeneinander.

## Ausführen

```sh
goose run --recipe nutrient-imbalance-check \
  --params plant_key=11441519 \
  --params tenant=my-garden
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |

## Wie entschieden wird

Der Lauf sammelt den Kontext der Pflanze, liest dann ihr Tagebuch nach einem gemessenen Wert und ordnet alles Vorliegende auf einer Leiter ein. Eine niedrigere Stufe stützt oder widerlegt eine höhere; sie hebt sie nie auf.

| Stufe | Beleg | Gewicht |
|:-----:|-------|---------|
| 1 | Ein gemessener Wert mit erkennbarer Einheit — EC, pH, ein Drainagewert — aus einem Tagebucheintrag | Legt die Richtung allein fest, wenn er jung genug ist |
| 2 | `target_ec_ms` und `npk_ratio` der Phase gegen bestätigte Düngefrequenz und Substrat-Basiswerte | Legt die Richtung fest, wenn Stufe 1 fehlt, mit geringerer Sicherheit |
| 3 | Nur das Muster im Pflegeprotokoll — häufig, selten oder verschoben gedüngt; Umtopfen überfällig | Stützt eine Richtung, begründet sie nie |
| 4 | Sichtbare Symptome | Grenzen ein, welcher Nährstoff und wie weit fortgeschritten — nie die Richtung |
| 5 | `nutrient_demand_level` der Art und Phasenerwartung | Setzt nur die Vorannahme |

**Ab Stufe 3 abwärts schlägt der Lauf keine Dosierung vor.** Er benennt stattdessen die Messung, die die Richtung klären würde. Diese Verweigerung ist das Ergebnis, kein fehlgeschlagener Lauf.

Stufe 1 ist der Grund, warum das Rezept das Tagebuch selbst liest: Es listet die Einträge der Pflanze, öffnet bis zu den acht jüngsten und hält beim ersten `measurements`-Wert an, der eine eindeutige Einheit und ein Datum innerhalb der aktuellen Phase trägt. Werte, die sich nicht festnageln lassen, werden verworfen — und als verworfen berichtet: Ein nacktes `ec: 1.8` kann Millisiemens oder Mikrosiemens sein, aus dem Tank oder aus der Drainage, und Raten macht aus einem Stufe-1-Beleg eine selbstbewusst falsche Antwort.

## Das Ergebnis lesen

Der Bericht beginnt mit einer Feldtabelle — Richtung, Belegstufe, zugewiesene Planphase mit ihrem `target_ec_ms`, Substrat und was die Tagebuchlektüre ergab — und liefert dann die Begründung in höchstens fünf Sätzen, jede verworfene Messung mit ihrem Grund, die empfohlenen Maßnahmen und die Zeit, die eine Korrektur bis zur Wirkung braucht.

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `DIRECTION: undersupply (tier <n>)` | der Pflanze fehlt, womit sie wachsen soll |
| `DIRECTION: oversupply (tier <n>)` | weiteres Düngen verschlimmert es |
| `DIRECTION: unavailable-at-adequate-supply (tier <n>)` | die Nährstoffe sind da und die Pflanze kommt nicht heran — pH, Wurzelschaden oder Substrat |
| `DIRECTION: undetermined (tier <n>)` | gefolgt von einer zweiten Zeile, die die eine klärende Messung benennt |

## Wenn nichts Brauchbares herauskommt

`undetermined` auf Stufe 3 ist das gewöhnliche Ergebnis für eine Pflanze, deren Tagebuch keine Messung enthält — und es ist ehrlich, nicht faul. In einem Garten, in dem Erinnerungen bestätigt, aber nie Mengen protokolliert werden, steht Stufe 2 auf nichts, und die Antwort ist die Bitte zu messen.

Zwei Dinge holen dieselbe Pflanze da heraus, und beide passieren außerhalb dieses Laufs:

- **Halte einen EC- oder pH-Wert in einem Tagebucheintrag fest.** Das ist ein Stufe-1-Wert und legt die Richtung allein fest.
- **Protokolliere die Düngung selbst mit `record_feeding_event`**, das Menge sowie EC und pH vor und nach der Gabe trägt. Dieses Rezept darf es nicht aufrufen — es schreibt —, aber ein Garten, der Fertigationen erfasst, gibt Stufe 2 die Düngefrequenz, die sie braucht.

## Quellen

- [`recipes/nutrient-imbalance-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/nutrient-imbalance-check.yaml) — die Parameter, die Tagebuchlektüre und das Berichtsformat
- [`.claude/skills/nutrient-imbalance-assess/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/nutrient-imbalance-assess/SKILL.md) — die Belegleiter und die Verweigerungsregel
- [`spec/process/nutrient-imbalance-detection/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/nutrient-imbalance-detection/de.md) — der Prozess, den dieses Rezept umsetzt
