---
title: Bewässerungsentscheidung
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-03
---

# Bewässerungsentscheidung

Eine Erinnerung sagt, dass die Pflanze fällig ist. Sie sagt nicht, dass die Pflanze trocken ist. `watering-decision` beantwortet die Frage, die eine Person hat, für eine Pflanze: **jetzt gießen, warten oder zu wenig Beleg, um es zu sagen.** Es sagt, worauf die Antwort ruht, wie sicher sie ist und was sie ändern würde. Es gießt nie, weil eine Erinnerung fällig ist, ein Intervall verstrichen ist oder die Pflanze vermutlich trocken ist.

Zwei Rezepte gehören zusammen und bleiben getrennt:

- **`watering-decision`** liest nur. Es gießt nichts und hält nichts fest.
- **`watering-decision-apply`** **schreibt**: Es bestätigt eine Pflegeerinnerung, weil du sagst, dass du danach gehandelt hast. Es gießt nichts und kann nicht prüfen, ob du es getan hast.

!!! note "Noch nicht an einer Live-Instanz gelaufen"
    Die Rezepte und der Skill wurden geschrieben, als der Kamerplanter-MCP-Server nicht erreichbar war. Die Tool-Namen stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md), gemessen am 2026-08-16. Behandle den ersten echten Lauf als die Messung.

## Rechne mit „zu wenig Beleg“

Der gemessene Katalog hat eine Quelle für den gegenwärtigen Zustand einer Pflanze: einen Feuchtewert, den du in einem Tagebucheintrag dieser Pflanze festgehalten hast. Eine Pflanze, die nur über Erinnerungen betreut wird, hat keinen, und dann ist die ehrliche Antwort `insufficient evidence`. **Das ist das gewöhnliche Ergebnis, kein Fehlschlag des Laufs.** Das Ergebnis nennt, welche Beobachtung fehlt, meist ein Feuchtewert in einem Tagebucheintrag, und mit welchem Zielwert er verglichen würde.

## Bevor du beginnst

- **Starte den Lauf aus diesem Repository-Checkout.** Das Entscheidungsrezept lädt die Projekt-Skills `plant-context-collect`, `diary-measurements-read`, `decision-policy` und `watering-decision` aus `.claude/skills/`, und die Skill-Erkennung hängt vom Arbeitsverzeichnis des Goose-Prozesses ab. Aus einem anderen Verzeichnis gestartet, gehen die Skills stillschweigend verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Du brauchst den `plant_key` der Pflanze**, den numerischen Schlüssel. [plant-master-data-check](plant-master-data-check.md) gibt ihn neben der lesbaren `instance_id` aus.

## Entscheiden

```sh
goose run --recipe watering-decision \
  --params plant_key=42 \
  --params tenant=my-garden \
  --params constraints="Substratfeuchte zwischen 30 und 50 % halten"
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `plant_key` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |
| `weather` | nein | Wetter und Vorhersage sind unbekannt; der Server hat dafür keine Quelle |
| `container` | nein | das Gefäß oder Beet ist unbekannt; der Server hat dafür kein Feld |
| `constraints` | nein | kein Feuchte-Zielwert ist genannt, ein Messwert hat also nichts zum Vergleichen, (der gemessene Datenbestand trägt keinen) |

## Was es entscheidet

| Was über den gegenwärtigen Zustand bekannt ist | Entscheidung |
|------------------------------------------------|--------------|
| ein junger, eindeutiger Feuchtewert dieser Pflanze auf der trockenen Seite eines genannten Zielwerts | `water now` |
| ein junger, eindeutiger Wert innerhalb des Zielwerts oder auf der feuchten Seite | `wait` |
| ein Wert ohne Zielwert, ein mehrdeutiger Schlüssel oder eine mehrdeutige Einheit, oder ein zu alter Wert | `insufficient evidence` |
| gar kein Wert | `insufficient evidence` |

- **Das Gießintervall einer Phase, die Artdaten und die Phasenanforderungen sind Vorannahmen.** Sie sagen, was normal ist, und entscheiden nichts allein; der Bericht führt sie als Vorannahmen auf.
- **Wetter, das du angibst, kann ändern, wie sicher die Antwort ist, nie die Antwort allein.**
- **Kein Sensor dient als Beleg.** Der Datenbestand hält keine Zuordnung von einem Home-Assistant-Sensor zu einer Pflanze, und ein Feuchtewert aus einem mehrdeutigen Tagebuchschlüssel wird verworfen, nicht geraten.

## Eine Erinnerung bestätigen

Wenn du gegossen hast, kannst du die Erinnerung bestätigen lassen:

```sh
goose run --recipe watering-decision-apply \
  --params plant_key=42 \
  --params decision="water now" \
  --params reminder_type=<der Typ, wie dein Pflegeprotokoll ihn festhält> \
  --params run_id=2026-11-03-a
```

| Parameter | Pflicht | Bedeutung |
|-----------|:-------:|-----------|
| `plant_key` | ja | die Pflanze, deren Erinnerung du befolgt hast |
| `decision` | ja | die Entscheidung, die du genehmigt hast; nur `water now` wird angenommen |
| `reminder_type` | ja | der Typ der zu bestätigenden Erinnerung, genau wie dein Pflegeprotokoll ihn für eine bestätigte Erinnerung festhält |
| `run_id` | ja | macht einen Wiederholungslauf nachvollziehbar und verhindert doppeltes Schreiben |
| `tenant` | nein | der Garten-Slug; nötig, wenn dein Schlüssel mehrere Gärten abdeckt |

- **Du nennst den Erinnerungstyp.** In diesem Repository ist keine Liste der Erinnerungstypen festgehalten, also rät oder setzt das Rezept nie einen.
- **Es verweigert ohne genehmigte `water now`-Entscheidung oder ohne Erinnerungstyp** und sagt, welches von beiden. Es schreibt keine Bestätigung, die der Entscheidung widerspricht. Der Erinnerungstyp wird so festgehalten, wie du ihn angibst, und der Lauf kann ihn nicht prüfen.
- **Es ruft zuerst einen Probelauf auf**, meldet, was geschrieben würde, und schreibt erst dann, mit einem Idempotenzschlüssel aus der Pflanze und der `run_id`. Ein erfolgreicher Probelauf beweist nicht, dass das Schreiben gelingt; das Ergebnis des echten Aufrufs wird so gemeldet, wie es zurückkam.
- **Geschrieben wird ein Eintrag: die Bestätigung einer Pflegeerinnerung.** Der Lauf hat nichts gegossen und nicht geprüft, ob die Pflanze gegossen wurde.
- Es ruft kein anderes Tool auf als das, das eine Pflegeerinnerung bestätigt, und kein Home-Assistant-Tool.

## Das Ergebnis lesen

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `WATERING: <decision> — <plant_key>` | das Ergebnis des Entscheidungsrezepts |
| `CONFIRMED: care task for <plant_key>` | die Bestätigung wurde geschrieben |
| `NOT CONFIRMED: <reason>` | nichts wurde geschrieben, und warum |
| `WATERING: not decided — <plant_key>` | ein Schritt ist fehlgeschlagen, und es kam keine Entscheidung zustande |

Der Entscheidungsbericht trägt die Entscheidung, den gegenwärtigen Zustand, auf dem sie ruht, oder `unknown`, den Beleg, die Vorannahmen, die Konfidenz, was sie ändern würde und was fehlt. Die Tagebuch-Lesezeile sagt, wie viele Einträge aufgelistet, geöffnet und ohne Messwerte gefunden wurden.

## Quellen

- [`recipes/watering-decision.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/watering-decision.yaml) und [`recipes/watering-decision-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/watering-decision-apply.yaml) — die Parameter und die Berichtsformate
- [`.claude/skills/watering-decision/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/watering-decision/SKILL.md) — die Entscheidungstabelle und die Belegregeln
- [`spec/process/watering-and-fertilization-decisions/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/watering-and-fertilization-decisions/de.md) — der Prozess, den diese Rezepte umsetzen
