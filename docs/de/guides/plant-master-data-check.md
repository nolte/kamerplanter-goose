---
title: Pflanzenstammdaten-Prüfung
audience: [plant-owner, self-hoster]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Pflanzenstammdaten-Prüfung

Jede spätere Analyse liest dieselben vier Felder, und eine Pflanze, der eines davon fehlt, lässt sich überhaupt nicht beurteilen. `plant-master-data-check` geht jede lebende Pflanze eines Gartens durch und meldet, welche unvollständig sind — und was jede Lücke jeweils verhindert.

Geprüft wird die Buchführung, nicht die Pflanze. Nichts in diesem Bericht ist eine Aussage über den Gesundheitszustand.

Dieser Lauf **liest nur** und lädt keinen Projekt-Skill, läuft also aus jedem Arbeitsverzeichnis — auch über `GOOSE_RECIPE_GITHUB_REPO` ohne Clone.

## Ausführen

```sh
goose run --recipe plant-master-data-check --params tenant=my-garden
```

| Parameter | Pflicht | Standard | Wirkung |
|-----------|:-------:|----------|---------|
| `tenant` | nein | über `list_tenants` ermittelt | nur nötig, wenn dein Key mehrere Gärten umfasst |
| `include_archived` | nein | `false` | `true` prüft auch entfernte Pflanzen, deren Datensätze keine Entscheidung mehr tragen |

Umfasst dein Key mehrere Gärten und du nennst keinen, stoppt der Lauf, ohne irgendetwas zu prüfen, und sagt es: `NOT INSPECTED: several gardens available, none given`. Nenne den Garten, statt den Key wählen zu lassen — ein Key mit mehreren Mitgliedschaften antwortet sonst für den falschen Garten, während der Bericht weiterhin den gemeinten im Kopf trägt.

## Die vier geprüften Felder

| Feld | Fehlt es, bedeutet das |
|------|------------------------|
| `species_key` | Nichts lässt sich beurteilen. Keine Basisdaten, kein Phasenplan, keine Schädlingsplausibilität. |
| `location_key` | Kein Sensor-, Klima- oder Standortkontext lässt sich dieser Pflanze zuordnen. |
| `current_phase_key` | Kein Gießintervall, keine Stresstoleranz, kein „ist es überfällig“ — jede phasenabhängige Beurteilung entfällt. |
| `planted_on` | Das Alter ist unbekannt, also lässt sich nichts als früh oder spät bezeichnen. |

Nichts sonst zählt als Lücke — weder `plant_name` noch `cultivar_key`, `site_key`, `substrate_key` oder `slot_key`. Dieses Repository hat nicht festgestellt, dass sie erforderlich sind, und sie mitzuzählen würde die vier begraben, auf die es ankommt. Auffälliges darunter landet stattdessen in der Schlussnotiz.

## Das Ergebnis lesen

Der Bericht listet eine Zeile je unvollständiger Pflanze, sortiert nach der Zahl fehlender Felder, archivierte Zeilen zuletzt. Fehlt nichts, steht dort `No gaps.` statt der Tabelle, gefolgt von einer Schlussnotiz aus höchstens drei Sätzen und zwei Zählzeilen.

| Spalte | Inhalt |
|--------|--------|
| Plant | `instance_id` — der lesbare Bezeichner, z. B. `DRACA-0616-OWL` |
| Key | `plant_key` — z. B. `11441519`, der Wert, den jedes Folgerezept nimmt |
| Missing | die fehlenden Felder namentlich, oder `archived` |
| Prevents | die kürzeste wahre Aussage darüber, was dadurch nicht verfügbar ist |

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `INSPECTED: <n> of <m>` | geprüfte Pflanzen gegen die Zahl, die der Filter auswählt; bei einem vollständigen Durchgang sind beide Hälften gleich |
| `INCOMPLETE: <n>` | lebende Pflanzen, denen mindestens eines der vier Felder fehlt; archivierte werden hier nie mitgezählt |

Beide Bezeichner stehen absichtlich in der Tabelle. `instance_id` erkennst du wieder; `plant_key` ist das, was [Nährstoffbilanz-Prüfung](nutrient-imbalance-check.md), [Schädlingsdruck-Prüfung](pest-pressure-check.md) und jedes Pflanzenwerkzeug tatsächlich annehmen. Den lesbaren Wert nimmt keines davon.

## Kosten

Eine `list_plants`-Antwort trägt bereits jedes hier geprüfte Feld, ein Garten mit 120 Pflanzen kostet also drei paginierte Aufrufe statt 120 — ein `get_plant` je Pflanze verbietet das Rezept ausdrücklich.

## Quellen

- [`recipes/plant-master-data-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/plant-master-data-check.yaml) — die vier Felder, die Paging-Regel und das Berichtsformat
- [`spec/mcp/kamerplanter-mcp-server/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) — was `list_plants` zurückgibt und welcher Zähler was bedeutet
