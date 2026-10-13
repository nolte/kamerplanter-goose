---
title: Gartenkontext-Prüfung
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-10-13
---

# Gartenkontext-Prüfung

Bevor irgendetwas einen Garten berät, sollte es wissen, was der Garten enthält und was nicht. `garden-context-check` sammelt den Kontext eines Kamerplanter-Gartens und berichtet ihn Feld für Feld: was gelesen wurde und aus welchem Werkzeug, und was **fehlt**, samt Grund. Es empfiehlt nichts.

Entscheidend ist die Spalte der fehlenden Felder. Ein Feld, für das der Server keine Quelle hat, kommt als fehlend zurück und wird nicht mit einem typischen Wert gefüllt, sodass ein späterer Schritt eine Vermutung nicht für einen Datensatz hält.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und sein Skill wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Antwortfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und einer früheren Messung, nicht aus einem Lauf dieses Rezepts. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt den Projekt-Skill `garden-context` aus `.claude/skills/`, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, geht der Skill still verloren, und der Lauf liefert trotzdem eine plausible Antwort.

## Ausführen

```sh
goose run --recipe garden-context-check \
  --params tenant=my-garden
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants`; ein Schlüssel, der mehrere Gärten abdeckt, braucht ihn |
| `goals` | nein | das Feld „Ziele und Einschränkungen“ wird als fehlend gemeldet: Der Server hat dafür keine Quelle, es erscheint nur, wenn Sie es angeben |

## Was es sammelt

Elf Felder, jedes als `present` oder `absent` gemeldet.

| Feld | Woher es kommt |
|------|----------------|
| Standort und Ort | die Standort- und Ortsschlüssel an jeder Pflanze; die Eigenschaften des Standorts selbst haben im gemessenen Katalog kein lesendes Werkzeug |
| Kulturen und Sorten | die Arten der Pflanzen, dann der Artdatensatz einmal je verschiedener Art, und die Sorte, wo eine Pflanze eine hat |
| Pflanzdurchläufe | die Liste der Pflanzdurchläufe |
| Wachstumsstadium | der Phasenschlüssel an jeder Pflanze |
| Boden und Substrat | das Substrat, auf das jede Pflanze verweist, abgeglichen mit der Substratliste |
| Gieß- und Düngezustand | die fälligen Pflegeaufgaben, und nur diese: eine leere Liste ist kein Beleg für kürzliche Pflege, weil das Pflegeprotokoll je Pflanze gelesen wird |
| Beete und Gefäße | **keine Quelle gemessen** |
| Wetter | **keine Quelle gemessen** |
| Aktuelle Messungen, historische Beobachtungen | Belege je Pflanze, für die von Ihnen genannten Pflanzen gesammelt, nicht auf Gartenebene |
| Ziele und Einschränkungen | nur von Ihnen |

Eine fällige Pflegeaufgabe wird als Anforderung des Plans geführt, nicht als Messung der Pflanze. Der Lauf zählt Pflanzen nach `matched`, nicht nach `total_in_tenant`, das archivierte Pflanzen einschließt.

## Das Ergebnis lesen

Der Bericht ist eine Tabelle der elf Felder mit Status, Abrufzeitpunkt und Quelle oder Grund, gefolgt von der Pflanzenzahl, der Artenliste, der Angabe, ob der Garten-Slug vorgegeben oder ermittelt wurde, und jedem Werkzeugfehler wörtlich.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `GARDEN CONTEXT: <n> of 11 present — <tenant>` | wie viel vom Kontext der Server liefern konnte |
| `ABSENT: <Felder>` | die Felder, um die jede spätere Analyse herum eingegrenzt wird, je mit `no source` (der gemessene Katalog bietet keine Quelle) oder `not collected` (eine Quelle existiert, wird aber je Pflanze gelesen) |

Eine niedrige Zahl ist kein Fehlschlag des Laufs. Sie ist eine Aussage darüber, was der Garten und der Server enthalten, und der spätere Schritt grenzt seine Frage entsprechend ein.

## Quellen

- [`recipes/garden-context-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/garden-context-check.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/garden-context/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/garden-context/SKILL.md) — die Sammelschritte und was von vornherein fehlt
- [`spec/process/garden-decision-policy/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/garden-decision-policy/de.md) — der Kontextvertrag, §D
