---
title: Düngeentscheidung
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Düngeentscheidung

Eine Pflanze sieht blass aus, und der erste Gedanke ist, sie zu düngen. Genau das macht eine überversorgte oder an der Aufnahme gehinderte Pflanze schlimmer. `fertilization-decision` nimmt die [Nährstoffprüfung](nutrient-imbalance-check.md) für eine Pflanze und beantwortet die Frage, die eine Person hat: **düngen, nicht düngen oder zu wenig Beleg, um es zu sagen.** Es sagt, worauf die Antwort ruht, wie sicher sie ist und was sie ändern würde.

Über die Nährstoffrichtung entscheidet es nichts. Die kommt aus der Nährstoffprüfung, und dieses Rezept übernimmt sie, wie sie ist. „Nicht düngen“ ist ein gewöhnliches Ergebnis, kein Fehlschlag.

Zwei Rezepte gehören zusammen und bleiben getrennt:

- **`fertilization-decision`** liest nur. Es düngt nichts und hält nichts fest.
- **`fertilization-decision-apply`** **schreibt**: Es hält eine Düngung fest, die du ausgeführt hast. Es düngt, dosiert und misst nichts.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Die Rezepte und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Entscheidungsrezept lädt die Projekt-Skills `plant-context-collect`, `diary-measurements-read`, `nutrient-imbalance-assess`, `decision-policy` und `fertilization-decision` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn neben der lesbaren `instance_id` aus.

## Entscheiden

```sh
goose run --recipe fertilization-decision \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params water_source_ec="0.3 mS/cm"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `water_source_ec` | nein | es wird kein Basiswasser-Wert übergeben: Eine Dosis, falls überhaupt eine genannt wird, gilt für ein unbekanntes Basiswasser |
| `tank_state` | nein | der Tank- und Dosierzustand ist unbekannt; der Server hat dafür kein Feld |

## Was es entscheidet

| Die Nährstoffprüfung sagt | Entscheidung | Beruht auf |
|---------------------------|--------------|------------|
| Unterversorgung, als Richtung festgestellt, und keine Umweltursache genannt | `feed` | unzureichender Ernährung |
| Überversorgung | `do not feed` | unzureichende Ernährung ist ausgeschlossen |
| Nichtverfügbarkeit bei ausreichender Versorgung oder eine genannte Umweltursache | `do not feed` | einer Umweltursache: Behebe zuerst diese |
| Richtung unbestimmt, ein Verdacht oder eine schwache Belegstufe | `insufficient evidence` | einer unsicheren Diagnose |

- **Ist der Beleg dünn, bevorzugt es die vorsichtige Antwort.** Eine Pflanze ohne Nährstoffplan, ohne Tagebuchmessung und nur mit bestätigten Düngeerinnerungen endet bei `insufficient evidence`. Die Erinnerungen sagen, dass gedüngt wurde, nicht wie viel, und die Nährstoffprüfung behandelt eine Häufigkeit ohne Mengen als schwachen Beleg.
- **Eine Dosis erscheint nur, wenn das Mischprotokoll eine geliefert hat**, und dann mit der Annahme, die es zu deinem Basiswasser getroffen hat. Ohne dieses Ergebnis ist die Dosis `unknown`; das Rezept nennt nie eine Konzentration, eine Mischreihenfolge oder eine Menge aus Allgemeinwissen.
- **Kein Sensor dient als Beleg.** Der Datenbestand hält keine Zuordnung von einem Home-Assistant-Sensor zu einer Pflanze.

## Eine Düngung festhalten

Wenn du die Pflanze gedüngt hast, kannst du die Düngung aufschreiben lassen:

```sh
goose run --recipe fertilization-decision-apply \
  --params plant_key=42 \
  --params decision=feed \
  --params volume_applied_liters=2 \
  --params ec_before=1.4 \
  --params run_id=2026-11-03-a
```

| Parameter | Pflicht | Bedeutung |
|-----------|:-------:|-----------|
| `plant_key` | ja | die Pflanze, die gedüngt wurde |
| `decision` | ja | die Entscheidung, die du genehmigt hast; nur `feed` wird angenommen |
| `volume_applied_liters` | ja | das Volumen, das du ausgebracht hast, in Litern, als Zahl |
| `ec_before`, `ph_before`, `ec_after`, `ph_after`, `runoff` | nein | nur, was du gemessen hast; leere werden nicht übergeben |
| `run_id` | ja | macht einen Wiederholungslauf nachvollziehbar und verhindert doppeltes Schreiben |
| `tenant` | nein | der Garten-Slug; nötig, wenn dein Schlüssel mehrere Gärten abdeckt |

- **Es verweigert ohne genehmigte `feed`-Entscheidung, ohne Menge oder mit einer Menge, die keine schlichte Zahl ist**, und sagt, was davon zutrifft. Ein Wert mit Einheit wie ml wird verweigert und nie umgerechnet. Die Menge ist die Düngung, die du ausgeführt hast: Sie wird so festgehalten, wie du sie angibst, und der Lauf kann sie nicht prüfen. Es schreibt keinen Eintrag, der der Entscheidung widerspricht.
- **Es ruft zuerst einen Probelauf auf**, meldet, was geschrieben würde, und schreibt erst dann, mit einem Idempotenzschlüssel aus der Pflanze und der `run_id`. Ein erfolgreicher Probelauf beweist nicht, dass das Schreiben gelingt; das Ergebnis des echten Aufrufs wird so gemeldet, wie es zurückkam.
- **Geschrieben wird ein Eintrag.** Der Lauf hat nichts gedüngt und behauptet das auch nicht. **Es ist nicht gemessen, ob irgendein Lese-Tool erfasste Düngeereignisse zurückgibt** ([#54](https://github.com/nolte/kamerplanter-goose/issues/54)), sodass eine festgehaltene Düngung die Nährstoffprüfung womöglich gar nicht erreicht.
- Es ruft kein anderes Tool auf als das, das eine Düngung festhält, und kein Home-Assistant-Tool.

## Das Ergebnis lesen

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `FERTILIZATION: <decision> — <plant_key>` | das Ergebnis des Entscheidungsrezepts |
| `RECORDED: feeding event for <plant_key>` | der Eintrag wurde geschrieben |
| `NOT RECORDED: <reason>` | nichts wurde geschrieben, und warum |

Der Entscheidungsbericht trägt die Entscheidung, worauf sie beruht, die Nährstoffrichtung und -stufe, die Dosis oder `unknown`, den Beleg, die Konfidenz, was sie ändern würde und was fehlt. Die Tagebuch-Lesezeile sagt, wie viele Einträge aufgelistet, geöffnet und ohne Messwerte gefunden wurden.

## Quellen

- [`recipes/fertilization-decision.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/fertilization-decision.yaml) und [`recipes/fertilization-decision-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/fertilization-decision-apply.yaml) — die Parameter und die Berichtsformate
- [`.claude/skills/fertilization-decision/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/fertilization-decision/SKILL.md) — die Entscheidungstabelle und die Dosisregel
- [`spec/process/watering-and-fertilization-decisions/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/watering-and-fertilization-decisions/de.md) — der Prozess, den diese Rezepte umsetzen
