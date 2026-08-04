# Home Assistant MCP Server

Status: Entwurf
Portfolio-Scope: local

## Kontext

Rezepte in diesem Repository lesen Sensorzustände und schalten — sofern ein Rezept das deklariert — Geräte über die in Home Assistant eingebaute MCP-Server-Integration. Sie ist das zweite der beiden Backends, die diese Rezepte verbinden, und verhält sich grundlegend anders als das erste.

Der Kamerplanter-MCP-Server hat einen **festen, aufzählbaren** Werkzeugkatalog: Wer ein Rezept schreibt, kann jedes Tool vorab benennen. Home Assistant nicht. Seine Werkzeugliste wird **zur Laufzeit zusammengesetzt** — aus jeder installierten Integration, die eine LLM-Tools-Plattform registriert, sortiert nach Domain und begrenzt durch die Entitäten, die der Betreiber für Assist freigegeben hat (`homeassistant/components/llm/__init__.py`, `async_get_tools`). Zwei Home-Assistant-Instanzen derselben Version bieten legitimerweise unterschiedliche Tools. Eine Plattform, die beim Einsammeln eine Ausnahme wirft, wird protokolliert und übersprungen, sodass der Katalog zwischen zwei Läufen auch still schrumpfen kann.

Daraus folgt das Tragende für Rezepte hier: **Ein Rezept darf keinen Home-Assistant-Werkzeugnamen fest verdrahten und dessen Existenz voraussetzen.** Spezifizierbar sind der Entdeckungsmechanismus, der Authentifizierungsvertrag, die Gestalt der Antworten und die Regeln, denen ein Rezept angesichts dieser Ungewissheit folgt.

Der Katalogabschnitt unten ist eine **Messung der Referenzinstanz** vom 2026-08-04, kein Vertrag. Er ist festgehalten, weil er zeigt, was der Mechanismus tatsächlich hervorbringt — einschließlich zweier Tools, die nur auf dieser Instanz existieren.

Rezept-Mechanik — wo eine Extension deklariert werden darf, wie sich die `env_keys`-Ersetzung verhält, was der Provider dem Agenten hinzufügt — ist einmal im [Goose-Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md) spezifiziert und wird hier nicht wiederholt.

Leserschaft: Autorinnen und Autoren von Rezepten in diesem Repository sowie Betreibende, die eine Home-Assistant-Instanz daran anschließen.

## Ziele

- Wer ein Rezept schreibt, weiß, welche Eigenschaften dieses Servers zugesichert und welche instanzspezifisch sind
- Ein Rezept fällt auf einen diagnostizierbaren Bericht zurück, wenn ein erwartetes Tool fehlt, statt eine Antwort zu erfinden
- Schalten ist eine deklarierte, überprüfbare Eigenschaft eines Rezepts, nie eine beiläufig entstehende
- Die gemessene Werkzeugoberfläche der Referenzinstanz ist aktenkundig, sodass Drift sichtbar wird

## Nicht-Ziele

- Vorgaben, welche Entitäten ein Betreiber für Assist freigeben soll — das ist Instanzpolitik
- Dokumentation der Home-Assistant-REST- oder WebSocket-API oder der Entitäten der `kamerplanter-ha`-Integration
- Vorschriften zu eigenen Intents; die Intents der Referenzinstanz werden festgehalten, nicht vorgeschrieben
- OAuth-Client-Registrierungsabläufe; Rezepte hier nutzen ein langlebiges Zugriffstoken

## Schnittstelle

### Transport und Endpunkt

Der Server liegt unter `/api/mcp` auf dem **Streamable-HTTP**-Transport. Gemessen gegen die Referenzinstanz: `initialize` verhandelt die Protokollrevision `2024-11-05`, antwortet mit `content-type: application/json` und vergibt **keinen `Mcp-Session-Id`-Header** — Folgeaufrufe gelingen, ohne eine Sitzung zurückzuspiegeln.

`serverInfo` meldet `{"name": "home-assistant", "version": "1.26.0"}`. Deklarierte Fähigkeiten: `prompts`, `resources` und `tools`, jeweils mit `listChanged: false`; `resources.subscribe: false`.

### Authentifizierung

Zwei Mechanismen werden unterstützt: OAuth über das IndieAuth von Home Assistant (ohne vorregistrierte Client-ID) und ein **langlebiges Zugriffstoken** aus den Sicherheitseinstellungen des Benutzerprofils. Rezepte hier nutzen das Token, gesendet als `Authorization: Bearer <token>`.

### Wie der Werkzeugkatalog entsteht

1. Die Integration wird gegen eine LLM-API konfiguriert; Vorgabe und rückwärtskompatibler Wert ist die eingebaute **Assist**-API (`llm.LLM_API_ASSIST`).
2. `async_get_tools` durchläuft jede Integration, die eine LLM-Tools-Plattform registriert hat, **nach Domain sortiert**, damit die Werkzeugreihenfolge nicht von der Ladereihenfolge abhängt, und hängt deren Tools aneinander.
3. Eine Integrationsplattform, die eine Ausnahme wirft, wird protokolliert und übersprungen — ihre Tools verschwinden aus dem Katalog, ohne dass ein Fehler den Client erreicht.
4. Jedes Tool wird in ein MCP-Tool überführt, dessen `inputSchema` als `{"type": "object", "properties": ...}` gebaut wird.

**Folge — das Schema führt keine `required`-Liste.** Live gegen die Referenzinstanz verifiziert: Über alle 25 Tools hinweg sind die einzigen vorkommenden `inputSchema`-Schlüssel `properties` und `type`. Ein Client kann allein aus dem Schema nicht erkennen, welche Argumente Pflicht sind.

### Ressourcen und Prompts

Wo die gewählte API `GetLiveContext` anbietet, veröffentlicht der Server zusätzlich eine nur lesbare Ressource. Gemessen: eine Ressource, `assist_context_snapshot` unter `homeassistant://assist/context-snapshot`, MIME-Typ `text/plain`, beschrieben als deckungsgleich mit der Ausgabe des `GetLiveContext`-Tools. `prompts/list` liefert einen nach der API benannten Prompt — gemessen: `Assist`.

## Werkzeugkatalog (gemessen, Referenzinstanz, 2026-08-04)

25 Tools. **Dies ist eine Momentaufnahme, kein Vertrag.** Die Gruppierung nach Wirkung ist die Einordnung dieser Spec, abgeleitet aus Werkzeugnamen und -beschreibungen.

### Nur lesend

| Tool | Anmerkungen |
|------|-------------|
| `GetLiveContext` | Aktueller Zustand von Geräten, Sensoren, Entitäten, Bereichen. Filter: `name`, `domain` (einzeln oder Liste), `area` |
| `GetDateTime` | Aktuelles Datum und Uhrzeit; keine Argumente |
| `todo_get_items` | Fragt eine To-do-Liste ab. `todo_list` ist ein Enum der Listen dieser Instanz; `status` filtert `needs_action` / `completed` / `all`, Vorgabe `needs_action` |

Das `todo_list`-Enum der Referenzinstanz enthält **`Kamerplanter Tasks`**, `Shopping List`, `Sourdough` und `gardening`. Die erste wird von der `kamerplanter-ha`-Integration bereitgestellt, was bedeutet: Pflanzenaufgaben sind über *beide* Backends erreichbar. Rezepte müssen bewusst entscheiden, welches maßgeblich ist.

### Schaltend

`HassTurnOn`, `HassTurnOff`, `HassSetPosition`, `HassStopMoving`, `HassCancelAllTimers`, `HassListAddItem`, `HassListCompleteItem`, `HassListRemoveItem`, `HassClimateSetTemperature`, `HassBroadcast`, `HassLightSet`, `HassMediaUnpause`, `HassMediaPause`, `HassMediaNext`, `HassMediaPrevious`, `HassSetVolume`, `HassSetVolumeRelative`, `HassMediaPlayerMute`, `HassMediaPlayerUnmute`, `HassMediaSearchAndPlay`.

### Instanzspezifisch, Wirkung nicht eingeordnet

| Tool | Gemessene Oberfläche |
|------|----------------------|
| `TimeTillErnte` | Beschreibung ist das generische `Execute Home Assistant TimeTillErnte intent`; Argumente sind die Standard-Entitätsfilter `name`, `area`, `floor`, `domain`, `device_class` |
| `time_till` | Beschreibung ist `Aliases: ['Ernte', 'ernten', 'time_till']`; keine Argumente |

Beide sind eigene Intents der Referenzinstanz und erscheinen auf keinem Standard-Home-Assistant. Ihre generischen Beschreibungen geben einem Modell wenig an die Hand, und diese Spec kann nicht feststellen, ob eines von beiden Seiteneffekte hat. Bis der Betreiber sie einordnet, behandeln Rezepte sie als nicht eingeordnet.

## Anforderungen

- **MUSS [MUST]** den Server über eine `streamable_http`-Extension erreichen, die auf `${HA_URL}/api/mcp` zeigt, deklariert entweder im eigenen `extensions:`-Block des Rezepts oder in der geteilten `extensions.yaml` des Repositorys
- **MUSS [MUST]** `HA_URL` und `HA_MCP_TOKEN` in den `env_keys` dieser Extension aufführen, wo immer sie deklariert ist; ohne das sendet Goose die literale Zeichenkette `${...}` als Header-Wert
- **MUSS [MUST]** die Zugangsdaten als `Authorization: Bearer <token>` übergeben, nie eingebettet in einer Rezept- oder Konfigurationsdatei
- **MUSS [MUST]** die verfügbaren Tools zur Laufzeit ermitteln und **DARF NICHT [MUST NOT]** die Existenz eines benannten Home-Assistant-Tools voraussetzen; jede Werkzeugnennung in einem `prompt` ist bedingt formuliert („bevorzugt X, falls vorhanden, sonst …")
- **MUSS [MUST]** ein fehlendes erwartetes Tool als ausdrückliches Schrittergebnis melden, nie still ein anderes Tool einsetzen oder aus dem Gedächtnis antworten
- **MUSS [MUST]** Pflichtargumente im `prompt` benennen, wenn ein Tool aufgerufen wird, bei dem sie zählen — das `inputSchema` des Servers lässt `required` weg, das Modell kann sie also nicht erschließen
- **MUSS [MUST]** Schalten im `prompt` verbieten — nicht nur in `instructions` — für jedes Rezept, das kein `-apply`-Rezept ist, und **MUSS [MUST]** die verbotenen Kategorien benennen (Geräte ein- oder ausschalten, Werte setzen, Skripte, Szenen oder Automationen ausführen)
- **MUSS [MUST]** die maßgebliche Quelle in seinem Prompt benennen, wenn ein Rezept Pflanzenaufgaben berührt, da die To-do-Liste `Kamerplanter Tasks` Daten spiegelt, die auch der eigene MCP-Server von Kamerplanter liefert
- **DARF NICHT [MUST NOT]** `TimeTillErnte` oder `time_till` aus einem nur lesenden Rezept aufrufen, solange deren Wirkung nicht eingeordnet ist
- **SOLLTE [SHOULD]** für Zustandsabfragen `GetLiveContext` bevorzugen, da es der dokumentierte Einstieg für Zustandsfragen ist und die veröffentlichte Ressource speist
- **SOLLTE [SHOULD]** eine schrumpfende Werkzeugliste als meldenswerten instanzseitigen Fehler behandeln: Eine Integrationsplattform, die eine Ausnahme wirft, wird Upstream still übersprungen
- **KANN [MAY]** die Ressource `homeassistant://assist/context-snapshot` lesen statt `GetLiveContext` aufzurufen, wenn ein Rezept die gesamte Momentaufnahme statt einer gefilterten Sicht will
- **KANN [MAY]** sich auf OAuth statt auf ein langlebiges Token stützen, sobald ein künftiger Client das unterstützt

## Akzeptanzkriterien

- [ ] Die Extension ist genau einmal deklariert — im Rezept oder in `extensions.yaml` — und benennt `streamable_http`, den Pfad `/api/mcp` und beide Env-Keys
- [ ] `goose recipe validate` läuft für das Rezept durch
- [ ] Kein Rezept-Prompt behauptet unbedingt, dass ein bestimmtes Home-Assistant-Tool existiert
- [ ] Ein Lauf gegen eine Instanz ohne ein erwartetes Tool erzeugt einen als übersprungen oder fehlgeschlagen markierten Schritt, der das Tool benennt
- [ ] Ein Lauf mit ungültigem Token meldet einen Authentifizierungsfehler, unterscheidbar von einer leeren Werkzeugliste
- [ ] Jedes Rezept ohne `-apply` verbietet die schaltenden Werkzeugkategorien innerhalb von `prompt`
- [ ] Kein nur lesendes Rezept ruft `TimeTillErnte` oder `time_till` auf
- [ ] Ein Rezept, das Pflanzenaufgaben liest, benennt, ob Kamerplanter oder die Liste `Kamerplanter Tasks` maßgeblich ist

## Offene Fragen

- Was `TimeTillErnte` und `time_till` tatsächlich tun und ob eines von beiden Seiteneffekte hat. Bis der Betreiber antwortet, bleiben beide nicht eingeordnet und für nur lesende Rezepte gesperrt.
- Ob die To-do-Liste `Kamerplanter Tasks` eine nur lesende Projektion von Kamerplanter ist oder aus Home Assistant heraus eigenständig beschreibbar. Davon hängt ab, ob ein Rezept dort je eine Aufgabe abschließen darf.
- Ob das Fehlen eines `Mcp-Session-Id`-Headers stabiles Verhalten ist oder ein Artefakt dieser Version; der Transport erlaubt Sitzungen, und eine künftige Version kann eine vergeben.
- Ob Rezepte beim Start einen Mindestsatz erwarteter Tools prüfen und abbrechen sollen oder pro Schritt degradieren. Diese Spec fordert derzeit das Degradieren pro Schritt.

## Quelle

- Live-Messung der Referenzinstanz, 2026-08-04: `initialize`, `tools/list` (25 Tools), `resources/list`, `prompts/list`. Endpunkt und Zugangsdaten aus der `.envrc` des Repositorys
- `home-assistant/core` — `homeassistant/components/mcp_server/server.py` (Servername, Werkzeugformatierung, `GetLiveContext`-Ressource) und `homeassistant/components/llm/__init__.py` (`async_get_tools`: Plattformdurchlauf, Domain-Sortierung, Überspringen bei Ausnahme), gelesen am 2026-08-04
- Home-Assistant-Dokumentation — [MCP-Server-Integration](https://www.home-assistant.io/integrations/mcp_server/) (Endpunkt, Transport, OAuth- und Langzeit-Token-Authentifizierung)
- `env_keys`-Verhalten von Goose gemessen gegen Goose 1.45.0; siehe `README.md` §Notes
