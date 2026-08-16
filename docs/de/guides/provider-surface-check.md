---
title: Provider-Werkzeuge prüfen
audience: [maintainer, recipe-author]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Provider-Werkzeuge prüfen

Ein Rezept hier erklärt, was es nicht aufrufen darf — und diese Erklärung ist genau so viel wert wie dein Wissen darüber, was der Agent überhaupt aufrufen kann. Unter `claude-code` hält der laufende Agent `Bash`, `Write`, `Edit`, `WebFetch` und `Agent`, ganz gleich was ein Rezept sagt: **Ein nur lesendes Rezept ist Prompt-Disziplin, keine Grenze.** `provider-surface-check` inventarisiert die Werkzeugoberfläche, die ein Lauf tatsächlich hält, damit dieser Satz eine Messung bleibt und keine Erinnerung wird.

Führ es nach einem Goose-Upgrade aus, nach einem Providerwechsel, oder bevor du einer Aussage in `spec/goose/` traust, die gegen eine ältere Version gemessen wurde.

Der Lauf ruft **gar nichts** auf — kein MCP-Werkzeug, keine Shell, kein Datei-Lesen. Irgendetwas aufzurufen würde verändern, was das Inventar misst.

## Ausführen

```sh
goose run --recipe provider-surface-check
```

Es nimmt keine Parameter. Es lädt auch keinen Projekt-Skill und läuft daher aus jedem Arbeitsverzeichnis.

Um zu trennen, was Goose beigesteuert hat und was der Provider mitbrachte, führ es zweimal aus:

```sh
goose run --recipe provider-surface-check                        # mit gesetztem GOOSE_ADDITIONAL_CONFIG_FILES
env -u GOOSE_ADDITIONAL_CONFIG_FILES goose run --recipe provider-surface-check
```

Der Unterschied zwischen beiden Inventaren ist genau das, was die gemeinsame `extensions.yaml` hinzugefügt hat. Was in **beiden** auftaucht, kam vom Provider.

## Das Ergebnis lesen

Der Bericht hat vier Abschnitte und sonst nichts:

| Abschnitt | Inhalt |
|-----------|--------|
| 1. MCP tools | die Anzahl je Server, dazu bis zu fünf Namen der Form `mcp__<server>__<tool>` je Server |
| 2. Execution and file access | ja/nein plus den exakten Werkzeugnamen für Shell-Ausführung, Datei-Lesen, Datei-Schreiben und URL-Abruf |
| 3. Agent and orchestration tools | alles, was Subagents startet, Arbeit plant, Workflows ausführt, Aufgaben verwaltet oder Skills lädt |
| 4. Everything else | die übrigen Werkzeugnamen |

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `SURFACE: <n> MCP servers, <m> non-MCP tools` | `<n>` aus Abschnitt 1 gezählt, `<m>` über die Abschnitte 2 bis 4 |

Abschnitt 1 nennt höchstens fünf Werkzeuge je Server, ist also eine Stichprobe und kein Katalog — die Zahl daneben ist die vollständige Anzahl. Ein Werkzeug, das dort nicht steht, fehlt deshalb nicht; eine Frage nach einem bestimmten Werkzeug beantwortet die Anzahl plus ein gezielter Blick, nie diese Liste.

## Was die Zahlen sagen — und was nicht

Die Zahl der Nicht-MCP-Werkzeuge ist zwischen Läufen nicht stabil, und eine kleinere Zahl bedeutet keine kleinere Oberfläche. Manche Werkzeuge liegen hinter `ToolSearch` und brauchen erst einen Schema-Abruf, bevor sie aufrufbar sind — zurückgestellt ist nicht abwesend, und `Bash` und `Write` waren so oder so in der direkt aufrufbaren Menge.

Zwei Ergebnisse lohnen sich zu kennen, bevor du dein eigenes Inventar liest:

- **Der Provider ersetzt den gesamten Goose-Werkzeugsatz, nicht einen Teil davon.** In keinem Inventar tauchte eine Goose-Plattform-Extension auf — kein `developer`, `todo`, `analyze` oder `summon` — obwohl alle vier in `~/.config/goose/config.yaml` aktiviert sind. Nur MCP-Extensions überleben, als `mcp__*`.
- **Alles, was Goose als Plattformwerkzeug anbietet, ist hier als fehlend anzunehmen, bis es als vorhanden gemessen wurde.** Das schließt `load_skill` ein; `goose skills list` berichtet über Auffindbarkeit, nicht über Verfügbarkeit zur Laufzeit.

Ob die Plugin- und Projektschichten hinter `Skill` und `Agent` befüllt sind, klärt das Gegenstück: [Provider-Plugins prüfen](provider-plugin-check.md).

## Quellen

- [`recipes/provider-surface-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/provider-surface-check.yaml) — die vier Abschnitte und die Zählregel
- [`spec/goose/recipe-project-pattern/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/de.md) — die erfassten Inventare mit Messdatum und Goose-Version
