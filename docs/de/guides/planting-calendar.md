---
title: Pflanzkalender
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-14
---

# Pflanzkalender

Wann eine Kultur in den Boden kann, hängt von den Frostdaten dieses Gartens ab und davon, was der Artdatensatz zu Saat- und Erntemonaten sagt. `planting-calendar` berechnet für jede genannte Kultur und jede ihrer Wachstumsperioden die Fenster, in denen sie gesät, vorgezogen, umgepflanzt und geerntet werden kann, und sagt für jedes Fenster, welche Regel und welches Feld es ergeben haben. Es schlägt keine Pflanzung vor; dafür gibt es den [Gartenplan](garden-plan.md).

Ein Fenster, das kein festgehaltenes Feld stützt, ist **unbekannt**, samt fehlender Eingabe. Der Lauf füllt es nie mit einem typischen Datum.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine vier Skills wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `site-analysis`, `planting-calendar` und `decision-policy` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.

## Ausführen

```sh
goose run --recipe planting-calendar \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params harvest_window="summer"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `crops` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `harvest_window` | nein | die Erntepräferenz wird als unbekannt gemeldet; sie scheidet nie eine Kultur aus |

`crops` ist eine durch Kommas getrennte Liste; jeder Eintrag ist ein Artschlüssel oder ein Artschlüssel und ein Sortenschlüssel, durch einen Doppelpunkt verbunden (`species_key:cultivar_key`).

## Was es berechnet

| Fenster | Gespeist von | Was es nicht abdeckt |
|---------|--------------|----------------------|
| Aussaat (direkt) | den Saatmonaten der Wachstumsperiode; den Frostdaten des Gartens bei einer frostempfindlichen Kultur | was die Werte von `frost_sensitivity` bedeuten und das Format der Frostdaten sind nicht festgehalten: Die Frostgrenze wird nur angewendet, wo beides eindeutig lesbar ist |
| Vorkultur | den Wochen vor dem letzten Frost, die die Art festhält, und dem Datum des letzten Frosts | das Format der Frostdaten |
| Umpflanzen | dem Datum des letzten Frosts, bei einer frostempfindlichen Kultur | wie lange ein Sämling braucht: kein Feld sagt es, daher wird nur der Beginn angegeben |
| Ernte | den Erntemonaten der Wachstumsperiode | die Monate im Artdatensatz insgesamt sind die Vereinigung über die Perioden, daher wird zuerst eine Periode gewählt |
| Reife | den Tagen bis zur Reife der Sorte | ab wann sie zählen, Aussaat oder Umpflanzen, ist nicht festgehalten: Sie werden als Wert gezeigt, und daraus wird kein Erntedatum berechnet |

Eine Art mit mehreren Wachstumsperioden hat mehrere Mengen von Fenstern, jede benannt nach den Monaten, die sie trägt. Sortenwerte gelten vor Artwerten, und der Bericht sagt, welche.

## Das Ergebnis lesen

Der Bericht ist eine Tabelle mit einer Zeile je Kultur und Periode (Aussaat, Vorkultur, Umpflanzen, Ernte, Erntepräferenz, Konfidenz), gefolgt von Regel, Feldern, Quelle, Abrufzeitpunkt und Belegstufe hinter jedem bekannten Fenster, den nicht berechneten Kulturen und jedem Werkzeugfehler wörtlich.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `CALENDAR: <k> windows known, <u> unknown — <slug>` | wie viele Fenster der Datensatz stützen konnte |
| `UNKNOWN WINDOWS: <Fenster>` | jedes unbekannte Fenster mit der Eingabe, die es klären würde |

Eine Kultur ohne Fenster ist kein fehlgeschlagener Lauf. Sie ist eine Aussage darüber, was der Artdatensatz und der Saatkalender enthalten.

## Quellen

- [`recipes/planting-calendar.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/planting-calendar.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/planting-calendar/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/planting-calendar/SKILL.md) — die Fenster, die Regeln und was jedes Feld nicht abdeckt
- [`.claude/skills/site-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/site-analysis/SKILL.md) — die Frostdaten und das Standortprofil
- [`spec/process/plant-planning-and-planting-calendar/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/plant-planning-and-planting-calendar/de.md) — der Prozess, den dieses Rezept umsetzt
