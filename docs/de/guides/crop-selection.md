---
title: Kulturwahl
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-13
---

# Kulturwahl

Ob eine Kultur zu einem Standort passt, hängt von Fakten über den Standort ab, und die Fakten, nach denen man zuerst greift — Licht, Platz, Wasser —, sind genau die, die der Kamerplanter-Katalog nicht enthält. `crop-selection` baut ein Profil dessen, was über den Standort Ihres Gartens bekannt ist, beurteilt Kandidaten aus Arten und Sorten dagegen und liefert je Kandidat ein Urteil, die Gründe und die verfehlten Bedingungen. Was es nicht weiß, sagt es.

Ein Kandidat gilt nie als geeignet auf einem Parameter, den niemand geliefert hat. Ein unbekannter Standortparameter oder ein fehlendes Artfeld lässt die Bedingung **unentschieden**: nicht erfüllt und nicht verfehlt.

Dieser Lauf **liest nur**. Er plant keine Pflanzung und ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine vier Skills wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt die Projekt-Skills `garden-context`, `site-analysis`, `crop-selection` und `decision-policy` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.

## Ausführen

```sh
goose run --recipe crop-selection \
  --params tenant=my-garden \
  --params crops="allium-porrum" \
  --params light="south-facing, about six hours of sun" \
  --params hardiness_zone=7b
```

| Parameter | Wirkung, wenn weggelassen |
|-----------|---------------------------|
| `tenant` | der Lauf ermittelt den Garten-Slug aus `list_tenants`; ein Schlüssel, der mehrere Gärten abdeckt, braucht ihn |
| `crops` | der Saatkalender kann nicht durch eine Ihrer Arten eingegrenzt werden, die Frostdaten stammen also von einer Pflanze des Gartens oder sind unbekannt; eine begrenzte Stichprobe des Artenkatalogs wird beurteilt, und der Bericht sagt, dass es eine Stichprobe ist |
| `goals` | kein Ziel wird beurteilt; keines wird als erfüllt gemeldet |
| `harvest_window` | der Zeitpunkt wird als unbekannt gemeldet |
| `light`, `area_or_volume`, `water`, `constraints` | der zugehörige Standortparameter wird als unbekannt gemeldet: Der Server hat dafür kein Feld |
| `hardiness_zone` | die Prüfung der Winterhärtezone bleibt unentschieden: Kein Werkzeug sagt, in welcher Zone ein Garten liegt |

Ihre eigenen Worte für Licht, Fläche und Wasser werden wie geschrieben übernommen und als von Ihnen stammend gekennzeichnet. Der Lauf macht aus „sonnig“ keine Stunden und aus einem Beet keine Quadratmeter.

## Was das Standortprofil enthält

Sieben Parameter, jeder `known` oder `unknown`.

| Parameter | Woher er kommt |
|-----------|----------------|
| Licht und Exposition | nur von Ihnen |
| Fläche und Gefäßvolumen | nur von Ihnen |
| Boden und Substrat | die Substrate, auf die die Pflanzen des Gartens verweisen; das eigene Substrat eines Beets ist nicht bekannt |
| Klima und Saison | die Frostdaten des Saatkalenders, eingegrenzt durch einen Artnamen; die Zone nur von Ihnen |
| Wasserverfügbarkeit | nur von Ihnen |
| Umweltbedingte Einschränkungen | nur von Ihnen, als Freitext |
| Vorhandene Beobachtungen und Messungen | je Pflanze gesammelt, auf Gartenebene also nicht gesammelt |

## Wonach ein Kandidat beurteilt wird

| Art | Was | Wenn es sich nicht beurteilen lässt |
|-----|-----|-------------------------------------|
| **Harte Bedingung** | Frostempfindlichkeit gegen die Frostdaten des Gartens; Winterhärtezone gegen Ihre Zone | unentschieden |
| **Präferenz** | Zeitpunkt gegen Ihr Erntefenster; Tage bis zur Reife gegen die frostfreie Spanne; Passung der Nachbarn; Ihre Ziele | unbekannt |

Eine verfehlte harte Bedingung lehnt den Kandidaten ab und wird mit ihren Werten und ihrer Quelle aufgelistet. Eine Präferenz ordnet nur und lehnt nie ab. Trägt eine Sorte einen Wert, wird er statt des Artwerts verwendet, und der Bericht sagt, welchen er verwendet hat.

Licht, Schattentoleranz, Staunässe-Toleranz und Boden-pH werden **nicht** geprüft: Die Artfelder dafür fehlten bei beiden geprüften Arten, sodass keine Bedingung bildbar ist. Ob andere Arten sie tragen, ist nicht belegt.

## Das Ergebnis lesen

Der Bericht beginnt mit der Tabelle des Standortprofils, sagt, ob die Kandidaten von Ihnen stammen oder eine Stichprobe sind, und gibt dann eine Zeile je Kandidat mit Urteil, verfehlten harten Bedingungen, unentschiedenen Bedingungen und Konfidenz, gefolgt von den Gründen und den Präferenzen.

| Urteil | Bedeutet |
|--------|----------|
| `eligible` | jede bildbare harte Bedingung ist erfüllt, und keine bleibt unentschieden |
| `rejected` | mindestens eine harte Bedingung wurde verfehlt |
| `undetermined` | etwas, das eine harte Bedingung braucht, ist unbekannt |

| Schlusszeile | Bedeutet |
|--------------|----------|
| `CROP SELECTION: <e> eligible, <r> rejected, <u> undetermined — <slug>` | die Anzahl der Urteile |
| `UNKNOWN SITE PARAMETERS: <Parameter>` | was zu liefern ist, damit aus „unentschieden“ eine Entscheidung wird |

Eine lange Liste unentschiedener Kandidaten ist kein fehlgeschlagener Lauf. Sie ist das ehrliche Ergebnis, wenn die Standortfakten des Gartens nicht geliefert wurden.

## Quellen

- [`recipes/crop-selection.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/crop-selection.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/site-analysis/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/site-analysis/SKILL.md) — das Standortprofil
- [`.claude/skills/crop-selection/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/crop-selection/SKILL.md) — die Bedingungen und das Urteil
- [`spec/process/site-analysis-and-crop-selection/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/site-analysis-and-crop-selection/de.md) — der Prozess, den dieses Rezept umsetzt
