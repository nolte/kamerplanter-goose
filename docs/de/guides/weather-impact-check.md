---
title: Prüfung der Wetterwirkung
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Prüfung der Wetterwirkung

Eine Frostvorhersage ist eine Tatsache über den Garten, nicht über die Pflanze. `weather-impact-check` sagt, was das Wetter, das du angibst, für bis zu fünf Pflanzen bedeutet: je Faktor, ob die Pflanze **exponiert** ist (`exposure`), ob die Daten **keine Exposition** zeigen (`no exposure in the supplied data`) oder ob es für diesen Faktor **keine Quelle** gibt (`no source`). Jede Exposition nennt die Schwelle, an der sie gemessen wurde, und ob Pflege, Gesundheit oder Erntezeitpunkt voraussichtlich betroffen sind. Es meldet das Wetter nie als Symptom der Pflanze.

Der Lauf **liest nur**. Er schaltet nichts ein oder aus, schützt oder versetzt keine Pflanze, hält nichts fest und hat kein Anwendungsrezept.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Das Rezept und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Kamerplanter-Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16, und der [Home-Assistant-Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/home-assistant-mcp-server/de.md), gemessen am 2026-08-04. Ob dein Home Assistant eine Wetter-Entität bereitstellt, wurde nie gemessen. Behandle den ersten echten Lauf als die Messung.

## Woher das Wetter kommt

- **Von dir.** Der Kamerplanter-Server hat kein Wetter- und kein Vorhersage-Tool, daher ist der Parameter `weather` die wichtigste Quelle. Er wird so übernommen, wie er geschrieben ist, und als von dir stammend gekennzeichnet.
- **Aus Home Assistant, wenn es `GetLiveContext` anbietet.** Der Lauf liest es einmal, nur für die Domäne `weather`, und kennzeichnet die Angabe als `home_assistant (unmeasured)`. Er liest keine andere Entität und keinen Sensor: Nichts im Datenbestand ordnet einen Sensor einer Pflanze zu. Wenn du und Home Assistant euch widersprecht, stehen beide Werte nebeneinander, und nichts wird gemittelt.

## Rechne mit „keine Quelle“

Ohne `weather` und ohne Wetter-Entität in Home Assistant ist **jeder Faktor `no source`**, und der Bericht sagt, was er nicht schließen kann: ob die Pflanzen Frost, Hitze, Regen, Wind oder einem Luftfeuchte-Extrem ausgesetzt sind oder sein werden. Das ist das ehrliche Ergebnis, kein Fehlschlag des Laufs. Ein Faktor, den dein Wettertext nicht erwähnt, ist ebenfalls `no source`.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `plant-context-collect`, `decision-policy` und `weather-impact-analysis` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- Führe bei einer neuen Umgebung zuerst die [`connectivity-check`](connectivity-check.md) aus.

## Ausführen

```sh
goose run --recipe weather-impact-check \
  --params tenant=my-garden \
  --params plants="42,43" \
  --params weather="heute Nacht klar, bis -2 °C, leichter Wind; ab Donnerstag mild" \
  --params placement="42 draußen im Beet, 43 auf der Fensterbank"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `plants` | nein | keine Pflanze wird beurteilt; nur die Wetterfaktoren werden eingestuft |
| `weather` | nein | Wetter kommt nur aus Home Assistant, wenn es eine Wetter-Entität anbietet; sonst ist jeder Faktor `no source` |
| `placement` | nein | jede Wirkung wird als bedingt genannt („wenn die Pflanze draußen steht“): Der Datenbestand hat kein Feld dafür, wo eine Pflanze steht |

**Höchstens fünf Pflanzen werden beurteilt**, in der Reihenfolge, in der du sie nennst; jeder weitere Schlüssel wird als nicht geprüft gemeldet.

## Was es meldet

| Faktor | Exposition, wenn die Daten nennen |
|--------|-----------------------------------|
| Temperaturextreme | ein Minimum oder Maximum, das eine Schwelle erreicht, Frost oder eine Hitzeperiode |
| Niederschlag | Regen, Starkregen, Hagel oder eine Trockenperiode |
| Wind | starken Wind, Böen oder Sturm |
| Luftfeuchte | eine relative Luftfeuchte jenseits einer festgehaltenen oder gekennzeichneten Schwelle, Nebel, anhaltende Nässe oder sehr trockene Luft; „18 °C, 55 % rF“ allein ist keine Exposition |
| Hitze- und Kälteereignisse | eine Hitzewelle, eine Frostnacht oder einen Kälteeinbruch |
| Vorhersageänderungen | eine Änderung zwischen jetzt und der Vorhersage |

- **Eine Schwelle hat eine Quelle, oder sie wird nicht verwendet.** Die Frostempfindlichkeit oder die Winterhärtezonen der Art oder die Stresstoleranz der Phase, so gelesen, wie sie erfasst sind; Allgemeinwissen nur, wenn es als solches gekennzeichnet ist. Ohne eine ist die Wirkung `not assessed`.
- **Wetter ist kein Symptom.** Symptome kommen nur aus einer Fotolesung, einem Tagebucheintrag oder einer erfassten Inspektion und stehen in einem eigenen Block. Ein Symptom und eine Exposition werden höchstens als „consistent with“ verknüpft, was ein Verdacht ist, keine Diagnose.
- **Das Dampfdruckdefizit** wird nur aus einer Temperatur und einer Luftfeuchte von derselben Zeit und demselben Ort berechnet, mit genannter Formel, und ohne Urteil gemeldet: Für es ist kein Zielwert festgehalten.
- **Eine Empfehlung braucht eine Schwelle aus dem Datenbestand und eine Pflanze, die du draußen oder geschützt verortest.** Eine eigene Schwelle kannst du nicht setzen. Alles andere ist eine Beobachtung.

## Das Ergebnis lesen

| Schlusszeile | Bedeutet |
|--------------|----------|
| `WEATHER: <e> exposures, <s> no source — <slug>` | die Zahl der Faktoren, die als Exposition und als ohne Quelle eingestuft sind, über die beurteilten Pflanzen |
| `WEATHER: not assessed — <slug>` | jeder Schritt ist fehlgeschlagen |

Der Block jeder Pflanze trägt außerdem eine Übergabe für die Pflanzengesundheit: die Expositionen und getrennt davon die Symptome, sodass eine spätere Gesundheitsprüfung beide lesen kann, ohne sie zu vermischen.

## Quellen

- [`recipes/weather-impact-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/weather-impact-check.yaml) — die Parameter, die Home-Assistant-Sperre und das Berichtsformat
- [`.claude/skills/weather-impact-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/weather-impact-analysis/SKILL.md) — die Faktortabelle, die Schwellenregel und die Trennung von Exposition und Symptom
- [`spec/process/growth-stage-and-weather-impact/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/growth-stage-and-weather-impact/de.md) — der Prozess, den dieses Rezept umsetzt
