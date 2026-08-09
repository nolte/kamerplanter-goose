# Goose-Rezept-Projektmuster

Status: Entwurf
Portfolio-Scope: local

## Kontext

Ein Repository, das wiederverwendbare Goose-Rezepte ausliefert, stößt auf dieselben Hindernisse, unabhängig davon, was die Rezepte tun. Extension-Blöcke werden in jede Datei kopiert. Ein Zugangsdatum wird still nicht ersetzt, und der Lauf meldet einen Serverausfall. Eine Nebenbedingung im falschen Schlüssel wird bei einem Headless-Lauf ignoriert. Der Agent hält am Ende Werkzeuge, die niemand deklariert hat.

Nichts davon lässt sich durch Lesen eines Rezepts entdecken. Jede Regel unten wurde gegen **Goose 1.45.0** mit dem Provider `claude-code` gemessen — durch Mitschnitt der tatsächlich abgesetzten Requests und durch Abfragen der Werkzeugoberfläche des laufenden Agenten —, weil beobachtetes und dokumentiertes Verhalten an mehreren Stellen auseinandergehen.

Diese Spec ist die Mechanik-Ebene dieses Repositorys. Die Backend-Specs unter `spec/mcp/` beschreiben, *was ein Server anbietet*; diese hier beschreibt, *wie ein Goose-Projekt darum herum gebaut wird*, sodass dieselbe Regel nicht je Backend wiederholt wird.

Leserschaft: alle, die hier ein Rezept ergänzen, sowie alle, die ein vergleichbares Goose-Repository beginnen und die Fehlermodi vorab kennen wollen statt einzeln je Debugging-Sitzung.

## Ziele

- Ein MCP-Server wird einmal pro Repository deklariert, nicht einmal pro Rezept
- Ein falsch konfiguriertes Zugangsdatum erzeugt eine Meldung, die das Zugangsdatum benennt, keinen Fehlbericht über den Server
- Die Lese-/Schreibgrenze eines Rezepts ist am Dateinamen sichtbar und dort durchgesetzt, wo Goose tatsächlich durchsetzt
- Die Werkzeuge, die ein Agent wirklich hält, sind bekannt, bevor ihm ein Rezept anvertraut wird
- Ein Rezept, das die Skills eines Projekts wiederverwendet, benennt, was es von der Umgebung braucht, statt still zu scheitern, wenn es fehlt
- Ein neues Rezept kostet einen Prompt, kein Setup

## Nicht-Ziele

- Prompt-Gestaltung oder Ausgabeformat von Rezepten
- Welche MCP-Backends genutzt werden und was deren Tools bedeuten — das ist `spec/mcp/`
- Goose-Provider-Auswahl, Modellwahl oder Kostensteuerung
- Paketierung von Rezepten für Konsumenten außerhalb der Verteilung dieses Repositorys

## Gemessenes Verhalten

### Deklaration von Extensions und Vorrang

Extensions dürfen im `extensions:`-Block eines Rezepts oder in einer geteilten Datei stehen, die über `GOOSE_ADDITIONAL_CONFIG_FILES` geladen wird. **Beide werden nicht zusammengeführt.** Gemessen: Waren eine geteilte und eine rezeptlokale Extension gleichzeitig konfiguriert, verband sich nur die rezeptlokale; der geteilte Eintrag erzeugte überhaupt keinen Request.

Ein Rezept deklariert daher entweder jede Extension, die es braucht, oder gar keine und erbt den geteilten Satz. Ein „geteilt plus eine weitere" gibt es nicht.

Die beiden Orte nutzen unterschiedliche Formen für dieselben Daten:

| Ort | Form |
|-----|------|
| Geteilte Konfigurationsdatei | `extensions:` ist eine **Map**, nach Namen verschlüsselt, jeder Eintrag braucht `enabled: true` |
| Rezept | `extensions:` ist eine **Liste**, ohne `enabled`-Schlüssel |

### Ersetzung von Umgebungsvariablen

`${VAR}` innerhalb einer Extension wird **nur** ersetzt, wenn `VAR` in den `env_keys` dieser Extension steht. Gegen einen Mitschnitt-Server gemessen:

| Deklaration | Was Goose sendete |
|-------------|-------------------|
| `${SECRET}`, ohne `env_keys` | `${SECRET}` — die literale Zeichenkette |
| `${SECRET}` mit `env_keys: ["SECRET"]` | den Wert |
| `{{ param }}` als Rezeptparameter | den Wert |

Der Fehler ist still und irreführend: Das Rezept validiert, die Extension verbindet sich, und der Server antwortet `401`, als wären die Zugangsdaten falsch.

**Eine Extension, deren `env_keys`-Variable nicht gesetzt ist, wird vollständig übersprungen** — keine Warnung `Failed to start extension`, die Tools fehlen einfach. Beobachtet, als `pass` nicht entschlüsseln konnte: Zwei Extensions verschwanden, während eine dritte, deren Variable gesetzt war, normal lud. Der Agent diagnostizierte das als „keine MCP-Server konfiguriert", was falsch war.

`--render-recipe` klärt das nicht: Es druckt `${VAR}` in beiden Fällen unersetzt.

### Auffinden und Verteilung von Rezepten

- `GOOSE_RECIPE_PATH` akzeptiert mehrere Verzeichnisse, getrennt durch `:`
- Das Auffinden ist **flach** — `*.yaml` direkt unter jedem Verzeichnis; Unterordner werden nicht durchlaufen
- `GOOSE_RECIPE_GITHUB_REPO` nimmt `owner/repo` und holt Rezepte nach Namen
- Es holt **nur Rezepte**. Eine geteilte Extension-Datei ist nicht Teil dieser Übertragung, sodass ein so bezogenes Rezept ohne Server ankommt, sofern der Konsument die Konfiguration nicht separat bereitstellt

### Wo Nebenbedingungen durchgesetzt werden

Ein Rezept mit `instructions`, aber ohne `prompt`, lädt und validiert, scheitert dann bei einem Headless-Lauf mit `no text provided for prompt`. Nebenbedingungen, die nur in `instructions` stehen, wurden beobachtet ignoriert. Was gelten muss, gehört in `prompt`.

### Werkzeugoberfläche des Providers

Der Provider ist nicht zwingend ein nackter Modell-Endpunkt. Gemessen mit `GOOSE_PROVIDER=claude-code` meldete ein Rezept ohne jede Extension und ohne geladene geteilte Konfiguration dennoch **29 Nicht-MCP-Tools**, darunter `Bash`, `Read`, `Write`, `Edit`, `WebFetch`, `WebSearch`, `Agent`, `Workflow`, `Skill` sowie die Familien `Task*` und `Cron*`.

Ein „nur lesendes" Rezept hält unter einem solchen Provider Shell-Zugriff, Schreibzugriff auf Dateien und die Fähigkeit, Subagenten zu starten. Seine Nur-Lese-Eigenschaft ist **Prompt-Disziplin, keine technische Grenze**. MCP-Tools aus Goose-Extensions erscheinen als `mcp__<server>__<tool>`.

Die Zahl ist nicht stabil: Eine wiederholte Inventur am 2026-08-05 ergab beim selben Provider **32** Nicht-MCP-Tools, von denen nur zehn (`Agent`, `Bash`, `Edit`, `Read`, `ReportFindings`, `ScheduleWakeup`, `Skill`, `ToolSearch`, `Workflow`, `Write`) direkt aufrufbar waren — der Rest lag zurückgestellt hinter `ToolSearch` und brauchte zuerst einen Schema-Abruf. Zurückgestellt heißt nicht abwesend: `Bash` und `Write` gehören ohnehin zum direkt aufrufbaren Satz, die obige Grenze verschiebt sich also nicht.

**Der Provider ersetzt den gesamten Goose-Werkzeugsatz, nicht einen Teil davon.** In derselben Inventur erschien keine einzige Goose-Platform-Extension — kein Tool aus `developer`, `todo`, `analyze` oder `summon` —, obwohl alle vier in `~/.config/goose/config.yaml` auf `enabled: true` stehen. Nur MCP-Extensions überleben die Ersetzung, als `mcp__*`. Was Goose als Platform-Tool anbietet, ist unter diesem Provider deshalb als fehlend anzunehmen, bis das Gegenteil gemessen ist.

### Verfügbarkeit von Plugins

Unter dem Provider `claude-code` gemessen:

| Fähigkeit | Ergebnis | Beleg |
|-----------|----------|-------|
| Plugin-**Skill** laden | funktioniert | `Skill(frontend-design:frontend-design)` aus dem Plugin-Cache geladen |
| Plugin-**Agent** dispatchen | scheitert | `Agent type '…' not found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup` |

Sichtbar sind nur Skills aus Plugins, die installiert und aktiviert sind; Skills, die in einer interaktiven Claude-Code-Sitzung über einen anderen Mechanismus erreichbar sind, nicht.

### Agents aus einem Projekt-Checkout

Dass ein Plugin-Agent unerreichbar ist, sagt nichts über einen Agent, der im Checkout selbst definiert ist. Goose dokumentiert eine eigene Agent-Ebene — Markdown-Dateien mit den Frontmatter-Schlüsseln `name`, `description` und `model`, aufgefunden unter `.agents/agents/`, `.goose/agents/` und `.claude/agents/` im Projekt sowie deren `~`-Entsprechungen, aufgerufen im Gespräch per `@name` oder per Delegationsbitte. Als Ort für neue Projekt-Agents nennt sie `.agents/agents/`.

Gemessen am 2026-08-07 mit zwei Sonden-Agents, deren einzige Aufgabe eine Ein-Wort-Antwort ist und die sich nur im Verzeichnis unterscheiden:

| Fähigkeit | Ergebnis | Beleg |
|-----------|----------|-------|
| Projektlokalen **Agent-Typ** auflisten | funktioniert | `probe-agent-reachable` erschien neben den fünf eingebauten Typen in der Registry, mit eigener `description` und `(Tools: Read)` |
| Aus `.claude/agents/` dispatchen | funktioniert | `Agent(subagent_type: probe-agent-reachable)` lieferte `reachable` |
| Den Zwilling aus `.agents/agents/` dispatchen | scheitert | `Agent type 'probe-agents-dir' not found. Available agents: claude, Explore, general-purpose, Plan, probe-agent-reachable, statusline-setup` |
| Plugin-Agent im selben Lauf dispatchen | scheitert | `Agent type 'nolte-shared:project-structure-reviewer' not found.` — dieselbe Liste |

Drei Ergebnisse aus einem Lauf klären, welche Ebene antwortet. Die Registry führt Claude Codes eigene eingebaute Typen (`Explore`, `Plan`, `general-purpose`), der Dispatch läuft über das `Agent`-Tool des Providers mit einem `subagent_type`, und gelesen wird ausschließlich das `.claude/`-Verzeichnis. **Das ist die Agent-Ebene des Providers, nicht die von Goose** — die genaue Entsprechung zur Lage bei den Skills, wo der `.claude/skills/`-Leser des Providers überlebt und Gooses `load_skill` nicht.

Daraus folgt eine Falle, denn die beiden Ebenen sind sich über den Ablageort uneinig:

| Verzeichnis | Gooses Dokumentation | Aus einem Recipe-Lauf hier erreichbar |
|-------------|----------------------|----------------------------------------|
| `.claude/agents/` | unterstützt, überkommen | ja |
| `.agents/agents/` | empfohlen für neue Projekt-Agents | **nein** |
| `~/.claude/plugins/*/agents/` | nicht Gooses Mechanismus | nein |

Wer Gooses eigener Empfehlung folgt, legt einen Projekt-Agent dorthin, wo dieser Provider ihn nicht sieht — und der Fehlschlag ist ein schlichtes „not found" gegen eine Liste, die vollständig aussieht. Ob Gooses `@name`-Aufruf unter einem nativen Provider funktioniert, ist hier ungetestet; konfiguriert ist nur `claude-code`, sodass „unter diesem Provider abwesend" und „überall abwesend" ununterscheidbar bleiben — genau wie bei `load_skill`.

Die Auffindung ist genauso arbeitsverzeichnisrelativ wie bei Projekt-Skills und trägt dieselbe Fehlerart: Ein aus einem anderen Verzeichnis gestarteter Lauf verliert den Agent ohne Fehlermeldung. Anders als bei einem Skill gibt es kein Gegenstück zu `disable-model-invocation`, ein Agent lässt sich einem nicht-interaktiven Lauf also nicht vorenthalten.

Dieses Repository liefert dennoch Skills statt Agents, weil ein Skill im Kontext des Aufrufers läuft und mit den übrigen komponiert, statt aus einem frischen Kontext zu antworten. Die beiden Sonden existieren, damit die Aussagen oben Messungen bleiben und keine Annahmen — andere Agents gibt es hier nicht.

### Skills aus einem Projekt-Checkout

Goose hat eine eigene Skill-Ebene — eine Platform-Extension `skills`, den Befehl `goose skills list` und ein Tool `load_skill`, dokumentiert als „Load a skill's full content into your context so you can follow its instructions". Gefunden werden Skills unter `.claude/skills/`, `.agents/skills/` und `.goose/skills/` im aktuellen Projekt sowie unter `~/.agents/skills/`, `~/.agents/plugins/*/skills/` und `builtin://skills/`.

**Unter dem Provider `claude-code` ist diese Ebene unerreichbar.** `goose skills list` aus einem Projekt-Checkout heraus listete dessen 18 Skills vollständig auf, doch ein im selben Verzeichnis gestarteter Lauf meldete `load_skill` als abwesend — im Einklang mit der oben beschriebenen Ersetzung des gesamten Werkzeugsatzes. `goose skills list` ist eine Aussage über das Auffinden, nicht über die Verfügbarkeit zur Laufzeit.

Was stattdessen funktioniert, ist das providereigene Gegenstück, das dasselbe Verzeichnis `.claude/skills/` liest — relativ zum **Arbeitsverzeichnis des Goose-Prozesses**. Durchgängig gemessen: Ein über `GOOSE_RECIPE_PATH` aus dem einen Repository aufgelöstes Rezept, ausgeführt mit dem Arbeitsverzeichnis eines zweiten Repositorys, lud den Projekt-Skill dieses zweiten Repositorys und erhielt den `{{ parameter }}` des Rezepts als `$ARGUMENTS` des Skills.

Ein einziger Frontmatter-Schlüssel entscheidet, ob ein Projekt-Skill für einen Rezept-Lauf überhaupt existiert:

| Skill-Frontmatter | Für einen Rezept-Lauf sichtbar |
|-------------------|--------------------------------|
| ohne Schlüssel `disable-model-invocation` | ja |
| `disable-model-invocation: true` | nein |

Gemessen mit zwei ansonsten identischen Probe-Skills in einem Verzeichnis: Der Lauf listete den ersten und nicht den zweiten. Der Schlüssel bedeutet „nur ein Mensch darf das aufrufen, per Slash-Befehl" — und ein Rezept-Lauf hat keinen Menschen. Goose' eigenes `skills list` ignoriert den Schlüssel und zeigt solche Skills trotzdem an; die beiden Sichten widersprechen sich also, und die optimistische ist die, die das Rezept nicht ausführt.

Das Arbeitsverzeichnis ist der einzige Hebel. Gemessen änderten weder `GOOSE_SEARCH_PATHS` noch `GOOSE_WORKING_DIR` etwas am Gefundenen; das Rezept-Schema kennt keinen Schlüssel `skills:` und `goose run` kein entsprechendes Flag. Einem Symlink `.claude/skills` in ein anderes Checkout wird **gefolgt**, was das Auffinden verlagert, ohne den Prozess zu verlagern — ein Skill, der die Dateien seines eigenen Repositorys liest, braucht dieses Repository aber ohnehin als Arbeitsverzeichnis.

### Unter-Rezepte

Das Rezept-Schema nimmt eine Liste `sub_recipes:` an — Einträge mit `name`, `path`, `values` und `sequential_when_repeated` —, und `goose run` nimmt ein wiederholbares Flag `--sub-recipe`. Beides ist der naheliegende Weg, einen Warteschlangen-Läufer zu bauen, der ein Einzel-Rezept je Element aufruft.

**Unter dem Provider `claude-code` funktioniert keines von beidem.** Gemessen am 2026-08-05 mit einem Kind-Rezept, dessen einzige Aufgabe ein `touch` auf eine Markierungsdatei war: mit einem `sub_recipes:`-Block und ebenso mit `--sub-recipe` meldete der Lauf kein Unter-Rezept-Tool, und **es entstand keine Markierungsdatei**. Der Mechanismus ist als Goose-Tool registriert und verschwindet damit in derselben Ersetzung des Werkzeugsatzes, die auch `load_skill` entfernt.

Der Fehlermodus verdient eine eigene Erwähnung, weil er kein sauberer Fehler ist. Auf die Frage, ob ein Unter-Rezept-Tool existiere, antwortete ein Lauf einmal mit `subrecipe__echo_child` — ein plausibler, aus dem Feld `name:` des Rezepts konstruierter Name, ohne dass ein solches Tool vorhanden gewesen wäre. Die Behauptung eines Modells, es habe ein Unter-Rezept aufgerufen, ist kein Beleg dafür, dass etwas lief; nur eine beobachtbare Nebenwirkung ist es.

Eine Schleife über N Elemente hat hier deshalb zwei Formen: innerhalb eines Rezepts über geteilte Skills iterieren und einen Kontext für den ganzen Stapel in Kauf nehmen, oder je Element einen eigenen Goose-Prozess aus einem Shell-Skript starten, was die Isolation je Element erhält und einen Prozessstart kostet.

`goose plugin install <git-url>` installiert ein Git-Repository mit `plugin.json` (oder `.goose-plugin/plugin.json` oder `.plugin/plugin.json`) samt `skills/`, `agents/` und `.mcp.json` nach `~/.agents/plugins/` und hebt das Auffinden auf der Goose-Seite aus dem Arbeitsverzeichnis heraus. Hier hilft das nicht: Das Tool, das solche Skills laden würde, ist genau das, welches der Provider entfernt hat.

## Projektlayout

```
recipes/                       ein Rezept je Datei, flach — das ausgelieferte Artefakt
extensions.yaml                jeder MCP-Server, einmal deklariert
spec/                          diese Ebene plus eine Spec je Backend
.envrc                         Endpunkte, Zugangsdaten-Abrufe, Konfigurationspfad
```

## Anforderungen

- **MUSS [MUST]** jeden MCP-Server genau einmal für das Repository deklarieren — in `extensions.yaml` —, und Rezepte, die sich darauf stützen, **DÜRFEN NICHT [MUST NOT]** einen eigenen `extensions:`-Block tragen, da ein rezeptlokaler Block den geteilten Satz ersetzt, statt ihn zu erweitern
- **MUSS [MUST]** jede `${VAR}`, die eine Extension referenziert, in deren `env_keys` aufführen, wo immer die Extension deklariert ist
- **MUSS [MUST]** Zugangsdaten aus der Umgebung beziehen; ein literales Zugangsdatum **DARF NICHT [MUST NOT]** in einem Rezept, in `extensions.yaml` oder in einer versionierten Datei auftauchen
- **MUSS [MUST]** jede Nebenbedingung, die gelten muss, in den `prompt` des Rezepts setzen; `instructions` **KANN [MAY]** Rahmen und Ton tragen, **DARF** aber **NICHT [MUST NOT]** der einzige Ort eines Verbots sein
- **MUSS [MUST]** die konkreten Tools benennen, die ein nur lesendes Rezept nicht aufrufen darf, statt nur die Kategorie zu beschreiben, damit das Verbot nicht von der Einordnung des Modells abhängt
- **MUSS [MUST]** das Dateinamens-Suffix `-apply` tragen und die Wirkung in `description` benennen, wenn ein Rezept ein Tool aufruft, das den Zustand eines Backends ändert: Kamerplanters Klassen `mcp.write` und `mcp.setup` sowie jedes Home-Assistant-Tool, das aktuiert — ein Gerät ein- oder ausschalten, einen Wert setzen, ein Skript, eine Szene oder eine Automation ausführen. Maschinell prüfbar ist nur die Kamerplanter-Hälfte, weil dieser Katalog aufzählbar ist und der von Home Assistant je Instanz zusammengesetzt wird; die aktuierende Hälfte ruht auf der [Home-Assistant-Server-Spezifikation](../../mcp/home-assistant-mcp-server/de.md) und auf dem Review
- **DARF NICHT [MUST NOT]** das Suffix tragen, wenn ein Rezept keinen Backend-Zustand ändert und nur eine Datei in den gitignorierten `.audits/`-Baum schreibt, und **MUSS [MUST]** stattdessen in seiner `description` sagen, was es schreibt. Das Suffix ist eine Aussage über den Garten von jemandem, nicht über das Dateisystem, und es an einen Bericht zu verschwenden, den niemand verlieren kann, entwertet es dort, wo es zählt
- **MUSS [MUST]** `recipes/` flach halten; Gruppierung **MUSS [MUST]** in Dateinamen kodiert werden, da das Auffinden keine Unterverzeichnisse durchläuft
- **MUSS [MUST]** im README des Repositorys angeben, dass der Bezug von Rezepten über `GOOSE_RECIPE_GITHUB_REPO` das separate Bereitstellen der Extension-Konfiguration erfordert
- **DARF NICHT [MUST NOT]** einen nur lesenden Prompt als Sicherheitsgrenze behandeln, wenn der Provider Ausführungswerkzeuge mitbringt; ein Rezept, das nicht vertrauenswürdige Eingaben verarbeitet, **MUSS [MUST]** unter einem Provider ohne solche Werkzeuge oder unter `--no-profile` laufen
- **MUSS [MUST]** das erforderliche Arbeitsverzeichnis in der `description` eines Rezepts benennen, das einen Projekt-Skill lädt, da das Auffinden von Skills relativ zum Arbeitsverzeichnis des Goose-Prozesses geschieht und ein anderswo gestartetes Rezept den Skill ohne Fehlermeldung verliert
- **DARF NICHT [MUST NOT]** `load_skill` aufrufen oder sich anderweitig auf Goose' eigene Skill-Ebene stützen, solange der Provider den Goose-Werkzeugsatz ersetzt; ein von `goose skills list` angezeigter Name **DARF NICHT [MUST NOT]** als Beleg dafür gelten, dass der Skill zur Laufzeit ladbar ist
- **DARF NICHT [MUST NOT]** sich unter einem solchen Provider auf `sub_recipes:` oder `--sub-recipe` stützen, und **MUSS [MUST]** jeden behaupteten Unter-Rezept-Aufruf an einer beobachtbaren Nebenwirkung prüfen statt am Bericht des Laufs, da ein Lauf ein plausibles, nicht existierendes Unter-Rezept-Tool benennt
- **DARF NICHT [MUST NOT]** `disable-model-invocation: true` in einem Projekt-Skill tragen, den ein Rezept laden soll, da der Schlüssel den Skill für jeden nicht-interaktiven Lauf unsichtbar macht
- **MUSS [MUST]** einen Projekt-Agent unter `.claude/agents/` ablegen statt unter dem von Gooses eigener Dokumentation empfohlenen `.agents/agents/`, da nur Ersteres in der Registry steht, die ein Lauf unter diesem Provider sieht
- **MUSS [MUST]** das erforderliche Arbeitsverzeichnis in der `description` eines Rezepts benennen, das einen projektlokalen Agent dispatcht — aus demselben Grund wie bei einem Skill: `.claude/agents/` löst gegen das Arbeitsverzeichnis des Goose-Prozesses auf, und es gibt keinen Frontmatter-Schlüssel, der einen Agent gezielt unsichtbar machen würde, wenn es das nicht tut
- **DARF NICHT [MUST NOT]** einen von einem Plugin bereitgestellten Agent-Typ aus einem Rezept dispatchen; in der Registry, die ein Lauf sieht, stehen nur die eingebauten Typen und die aus `.claude/agents/` des Arbeitsverzeichnisses
- **SOLLTE [SHOULD]** ein Konnektivitätsrezept ausliefern, das jeden deklarierten Server nur lesend prüft und je Server PASS/FAIL meldet, und **SOLLTE [SHOULD]** es ausführen, bevor einem anderen Rezept in einer neuen Umgebung vertraut wird
- **SOLLTE [SHOULD]** ein Provider-Oberflächen-Rezept ausliefern, das die Werkzeuge des Agenten inventarisiert, damit die Ausführungsoberfläche eine Messung statt einer Annahme ist
- **SOLLTE [SHOULD]** ein fehlendes Tool als ausdrückliches Schrittergebnis melden, das das Tool benennt, nie als stille Ersetzung
- **SOLLTE [SHOULD]** ein Rezept, das einen Skill lädt, diesen Ladevorgang als benanntes Schrittergebnis melden lassen, da ein nicht geladener Skill einen Lauf hinterlässt, der allein aus dem Prompt weiterhin eine plausible Antwort erzeugt
- **SOLLTE [SHOULD]** die Verfügbarkeit eines Skills in der Zielumgebung messen, bevor ein Rezept sich darauf stützt — so wie die Werkzeugoberfläche des Providers gemessen statt angenommen wird
- **SOLLTE [SHOULD]** beim Melden eines Fehlers ein nicht gesetztes Zugangsdatum von einem nicht erreichbaren Server unterscheiden, da eine Extension mit nicht gesetzter `env_keys`-Variable ohne Warnung verschwindet
- **KANN [MAY]** Extensions innerhalb eines einzelnen Rezepts deklarieren, wenn es eigenständig konsumiert werden soll, wobei es dann auf den geteilten Satz vollständig verzichtet

## Akzeptanzkriterien

- [ ] Jeder MCP-Server erscheint genau einmal im gesamten Repository
- [ ] Kein Rezept, das sich auf `extensions.yaml` stützt, deklariert einen `extensions:`-Block
- [ ] Jede in einer Extension verwendete `${VAR}` steht in deren `env_keys`
- [ ] Keine versionierte Datei enthält ein literales Zugangsdatum
- [ ] Jedes Verbot, auf das sich ein Rezept stützt, steht in seinem `prompt`
- [ ] Jedes Rezept, das ein `mcp.write`- oder `mcp.setup`-Tool aufruft, trägt einen `-apply`-Dateinamen
- [ ] Jedes Rezept, das überhaupt etwas schreibt, sagt das in seiner `description` — mit Suffix oder ohne
- [ ] `recipes/` enthält keine Unterverzeichnisse
- [ ] Das README benennt die Anforderung an die Extension-Konfiguration für über GitHub bezogene Rezepte
- [ ] Ein Konnektivitätsrezept existiert und läuft gegen die aktuelle Umgebung durch
- [ ] Ein Provider-Oberflächen-Rezept existiert und sein letztes Ergebnis ist festgehalten
- [ ] Kein Rezept ruft `load_skill` auf
- [ ] Kein Rezept deklariert `sub_recipes:` oder wird mit `--sub-recipe` gestartet, solange der Provider den Goose-Werkzeugsatz ersetzt
- [ ] Jedes Rezept, das einen Projekt-Skill lädt, benennt das erforderliche Arbeitsverzeichnis in seiner `description`
- [ ] Kein von einem Rezept geladener Skill trägt `disable-model-invocation: true`
- [ ] Kein Rezept dispatcht einen von einem Plugin bereitgestellten Agent-Typ
- [ ] Jeder Projekt-Agent liegt unter `.claude/agents/`, nicht unter `.agents/agents/`
- [ ] `goose recipe validate` läuft für jede Datei in `recipes/` durch

## Offene Fragen

- Ob sich die Werkzeugoberfläche des Providers je Rezept statt je Lauf einschränken lässt; `--no-profile` ist als „lässt Standard-Extensions weg" dokumentiert, seine Wirkung auf providerseitige Werkzeuge wurde nicht gemessen.
- Wie mehrere Dateien in `GOOSE_ADDITIONAL_CONFIG_FILES` getrennt werden und ob sich `~/.config/goose/config.yaml` identisch zu einer zusätzlichen Datei verhält. Ungetestet — die globale Konfiguration des Nutzers wurde bewusst nicht angefasst.
- Ob MCP-Server, die in den Einstellungen des Providers konfiguriert sind, dem Goose-Agenten zugänglich gemacht werden. Die Prüfung ergab keine, aber die Server des Providers waren zu diesem Zeitpunkt fehlerhaft, sodass „nicht weitergereicht" und „weitergereicht, aber defekt" am Ergebnis nicht unterscheidbar sind.
- Ob ein als Plugin installierter Skill für Goose sofort sichtbar wird oder erst nach einem Sitzungsneustart.
- Ob `load_skill` unter einem nativen Modell-Provider wie `anthropic` oder `openai` erscheint, was Goose' eigene Skill-Ebene — und damit `~/.agents/plugins/` und `goose plugin install` — nutzbar machen würde. Ungetestet: Hier ist nur `claude-code` konfiguriert, sodass „unter diesem Provider abwesend" und „überall abwesend" an der Messung nicht unterscheidbar sind.
- Ob Gooses eigene Agent-Ebene — der `@name`-Aufruf und das von ihr dokumentierte Verzeichnis `.agents/agents/` — unter einem nativen Modell-Provider funktioniert. Ungetestet aus demselben Grund wie bei `load_skill`: Konfiguriert ist nur `claude-code`, und darunter antwortet stattdessen die Agent-Ebene des Providers. Falls ja, hätte ein Agent je nach Provider zwei unvereinbare Ablageorte — schlechter als der eine, den es derzeit gibt.
- Ob die Verteilung von Skills als providerseitiges Plugin ein stabilerer Weg ist als das Arbeitsverzeichnis, da an diesem zugleich die Dateipfade eines Skills hängen. Nicht gemessen; beide Belange ziehen in entgegengesetzte Richtungen, und noch stützt sich kein Rezept hier auf einen Skill.
- Ob die am 2026-08-05 beobachtete Trennung in zurückgestellte und direkt aufrufbare Tools je nach Provider-Version oder Sitzung variiert und ob ein Tool während eines laufenden Durchgangs zwischen beiden Mengen wechseln kann.

## Quelle

- Gemessen gegen Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`, 2026-08-04: Vorrang von Extensions und `env_keys`-Ersetzung mitgeschnitten mit einem lokalen HTTP-Server, der eingehende Header protokolliert; Auffinden von Rezepten geprüft mit `goose recipe list`; Werkzeugoberfläche und Plugin-Verfügbarkeit geprüft mit `recipes/provider-surface-check.yaml` und `recipes/provider-plugin-check.yaml`
- Gemessen gegen Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`, 2026-08-05: Auffinden von Skills geprüft mit `goose skills list` aus mehreren Arbeitsverzeichnissen und mit einem symlinkten Skills-Verzeichnis; Verfügbarkeit von `load_skill`, Werkzeug-Inventur und Wirkung von `disable-model-invocation` geprüft mit Headless-Läufen `goose run --no-session`, letztere gegen zwei eigens gebaute Probe-Skills, die sich nur in diesem Schlüssel unterscheiden; Durchreichen von Parametern nach `$ARGUMENTS` geprüft mit einem Wegwerf-Rezept auf `GOOSE_RECIPE_PATH`, ausgeführt aus dem Checkout eines anderen Repositorys; Auffindpfade und Aufbau des Plugin-Manifests aus den eingebetteten Strings der Binärdatei gelesen; Verfügbarkeit von Unter-Rezepten geprüft mit einem Kind-Rezept, dessen einzige Wirkung das Anlegen einer Markierungsdatei war, einmal über einen `sub_recipes:`-Block und einmal über `--sub-recipe`
- Gemessen gegen Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`, 2026-08-07: Auffinden und Dispatch projektlokaler Agents geprüft mit `recipes/provider-plugin-check.yaml`, erweitert um drei Schritte, gegen zwei eigens gebaute Sonden-Agents, die sich nur im Verzeichnis unterscheiden — `.claude/agents/probe-agent-reachable.md` und `.agents/agents/probe-agents-dir.md`; der Plugin-Agent-Dispatch im selben Lauf lieferte das dritte Kontrastergebnis
- Goose-Dokumentation, *Custom Agents* (`https://goose-docs.ai/docs/guides/context-engineering/custom-agents/`), gelesen am 2026-08-07, für die dokumentierten Auffindverzeichnisse, das Frontmatter aus `name` / `description` / `model` und die Empfehlung, `.agents/agents/` zu verwenden — jene Empfehlung, der die Messung oben unter diesem Provider widerspricht
- `goose run --help`, `goose recipe --help`, `goose skills --help`, `goose plugin install --help` (Goose 1.45.0) für Auffind- und Extension-Optionen
- Backend-Verträge: `spec/mcp/kamerplanter-mcp-server/de.md`, `spec/mcp/home-assistant-mcp-server/de.md`
