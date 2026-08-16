---
title: Artdaten-Prüfung
audience: [plant-owner, maintainer]
content_mode: how-to
track: user-docs
last_updated: 2026-08-16
---

# Artdaten-Prüfung

Jede Beurteilung einer Pflanze steht auf ihrem Artdatensatz: Keimtemperatur, Saattiefe, Winterhärte, die Zeitfenster. Ist einer dieser Werte falsch, ist alles falsch, was darauf aufbaut — und kein späterer Lauf wird es bemerken. `species-baseline-check` liest einen Artdatensatz, prüft ihn auf agronomische Plausibilität, ermittelt den Lebenszyklus, wo der Datensatz ihn nicht nennt, und schlägt eine Korrektur nur vor, wenn drei unabhängige Quellen übereinstimmen.

Viele zweifelhafte Werte zu finden und keine Korrektur vorzuschlagen ist das erwartete Ergebnis, kein schwaches.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz — eine vorgeschlagene Korrektur richtet sich an [nolte/kamerplanter](https://github.com/nolte/kamerplanter), damit ein Mensch sie umsetzt.

## Bevor du startest

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `species-baseline-verify` und `plant-lifecycle-resolve` aus `.claude/skills/`, und die Skill-Auffindung erfolgt relativ zum Arbeitsverzeichnis des Goose-Prozesses. Ein anderswo gestarteter Lauf verliert den Skill stillschweigend und liefert trotzdem eine plausible Antwort.
- **Der Lauf recherchiert im Web.** Er ist das einzige Rezept hier, das Quellen außerhalb deiner beiden Server liest, weil ein Wert gegen irgendetwas geprüft werden muss. Nichts, was er behauptet, darf aus dem Gedächtnis des Modells stammen.

## Ausführen

```sh
goose run --recipe species-baseline-check \
  --params species_key=allium-porrum \
  --params tenant=my-garden
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `species_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |

`tenant` ist hier keine Zierde: Die Frostdaten des Aussaatkalenders gelten je Garten, und Zeitprüfungen hängen an deinem eigenen letzten Frost, den Eisheiligen und dem ersten Frost — nicht an einer Faustregel.

## Was geprüft wird

Der Artdatensatz liefert nur seine befüllten Felder zurück. Ein fehlender Schlüssel heißt deshalb „für diese Art nicht befüllt“ — nie „trifft nicht zu“. Der Lauf listet daher **vor** jeder Prüfung auf, welche Felder vorhanden und welche abwesend sind, und hält Prüfungen, die nicht laufen konnten, getrennt von Prüfungen, die liefen und bestanden. Beides zusammenzuwerfen machte aus einer Lücke eine falsche Sicherheit.

Danach ermittelt er den Lebenszyklus und hält beim ersten Schritt an, der ihn festlegt: die Zuordnung der Instanz selbst, dann Wachstumsperioden und Monatsfelder, dann das Überwinterungsprofil, dann Recherche unter der Drei-Quellen-Regel. Botanischer und kultivierter Zyklus werden getrennt genannt, wo sie sich unterscheiden — Lauch ist zweijährig und wird einjährig kultiviert, und nur eines davon beantwortet eine Erntefrage.

## Was eine Korrektur erlaubt

| Sicherheit | Grundlage | Erlaubt |
|------------|-----------|---------|
| **Established** | Drei oder mehr unabhängige Quellen stimmen überein | Eine vorgeschlagene Korrektur, mit ihren Quellen |
| **Probable** | Zwei stimmen überein, oder drei mit kleinen Abweichungen | Einen Befund. Der erfasste Wert bleibt stehen |
| **Uncertain** | Quellen widersprechen sich, oder es gab nur eine | Einen Befund, der den Widerspruch benennt. Der Wert bleibt stehen |
| **Unverifiable** | Keine brauchbare Quelle | Eine benannte Lücke. Der Wert bleibt stehen |

Unabhängig heißt: einander nicht zitierend. Drei Seiten, die den Katalogtext einer Gärtnerei wiederholen, sind eine Quelle. Universitäre Beratungsdienste, RHS und ISTA stehen am höchsten; Saatguthäuser zählen speziell für Zeitangaben; Foren stützen, tragen aber nie eine Aussage. Wikipedia, KI-generierter Text und Blogbeiträge ohne Autorenschaft reichen nie allein.

## Das Ergebnis lesen

Der Bericht beginnt mit einer Feldtabelle — Art, vorhandene Felder, abwesende Felder, Zyklus, Frostanker, Befunde nach Schweregrad — und listet dann jeden Befund mit Sicherheit und Quellen, die Prüfungen, die nicht laufen konnten, und jede vorgeschlagene Korrektur mit ihren drei Quellen.

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `BASELINE: plausible` | nichts im Datensatz widerspricht dem, was die Quellen sagen |
| `BASELINE: findings:<n>` | gefolgt von einer zweiten Zeile, die den folgenreichsten Befund benennt |

Ein Befund ist kein Mangel dieses Repositorys. Er ist eine Aussage über den Artdatensatz in Kamerplanter, und der Bericht ist so geschrieben, dass er dort unverändert eingereicht werden kann.

## Quellen

- [`recipes/species-baseline-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/species-baseline-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/species-baseline-verify/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/species-baseline-verify/SKILL.md) — die Plausibilitätsprüfungen, die Quellenrangfolge und die Drei-Quellen-Regel
- [`.claude/skills/plant-lifecycle-resolve/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/plant-lifecycle-resolve/SKILL.md) — die Auflösungsreihenfolge und die zwei Zyklen
- [`spec/process/species-baseline-verification/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md) — der Prozess, den dieses Rezept umsetzt
