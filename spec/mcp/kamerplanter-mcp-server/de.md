# Kamerplanter MCP Server

Status: Entwurf
Portfolio-Scope: local

## Kontext

Rezepte in diesem Repository erreichen Pflanzendaten über den MCP-Server, der im Kamerplanter-Backend mitläuft. Dieser Server ist kein generisches REST-Abbild: Er stellt eine kuratierte, semantisch hochstehende Werkzeugpalette bereit, bei der ein Tool einen ganzen Anwendungsfall kapselt und kompaktes JSON zurückgibt, statt dass das Modell mehrere REST-Aufrufe verketten muss.

Zwei Eigenschaften machen eine Spezifikation lohnender als eine Entdeckung pro Rezept. Erstens ist der Werkzeugkatalog **fest und aufzählbar** — live gemessen bietet der Server exakt die 12 Tools, die die Upstream-Dokumentation führt, sodass die vollständige Oberfläche vorab bekannt ist. Das ist der scharfe Gegensatz zu [Home Assistant](../home-assistant-mcp-server/de.md), dessen Katalog zur Laufzeit zusammengesetzt wird und pro Instanz abweicht. Zweitens ist der Server **mandantenfähig mit einem Berechtigungsmodell pro Garten**, sodass derselbe Schlüssel in einem Garten schreiben darf und in einem anderen dieselbe Aktion verweigert bekommt. Ein Rezept, das dies ignoriert, erzeugt Fehler, die wie Bugs aussehen, aber korrekte Ablehnungen sind.

Alles unten als *gemessen* Gekennzeichnete wurde am 2026-08-04 von der Referenzinstanz gelesen, über `initialize`, `tools/list` und einen nur lesenden `list_tenants`-Aufruf. Die Upstream-Dokumentation kennzeichnet den Server als **teilweise verfügbar**: Die 12 Tools sind das Implementierte; spezifiziert sind insgesamt rund 30.

Leserschaft: Autorinnen und Autoren von Rezepten in diesem Repository sowie alle, die den deklarierten Extension-Block und Prompt eines Rezepts auf Korrektheit prüfen.

## Ziele

- Wer ein Rezept schreibt, kann das exakte Tool für eine Aufgabe benennen, ohne einen laufenden Server zu inspizieren
- Das Tenant-Argument, die Berechtigungsklasse und die Lese-/Schreibgrenze jedes Tools sind sichtbar, bevor ein Rezept läuft
- Rezepte scheitern mit einer diagnostizierbaren Meldung, wenn der Server deaktiviert, der Schlüssel ungültig oder die Rolle unzureichend ist — nie mit einer stillen Falschantwort
- Schreibzugriff ist eine bewusste, deklarierte Eigenschaft eines Rezepts, kein Nebenprodukt der Prompt-Formulierung

## Nicht-Ziele

- Dokumentation der Kamerplanter-REST-API, des In-App-KI-Assistenten oder des Knowledge-Service — der MCP-Server ist eine eigene Maschine-zu-Maschine-Schnittstelle
- Spezifikation von Tools, die Upstream als spezifiziert-aber-nicht-implementiert führt (Setup-Makros, Massenanlage von Pflanzen, IPM- und Ernte-Schreibtools, die Wissensdatenbank-Brücke)
- Betrieb, Skalierung oder Helm — der Server läuft derzeit im Backend-Prozess mit
- Vorgaben zur Prompt-Formulierung; nur die Invarianten, die ein Prompt wahren muss

## Schnittstelle

### Transport und Endpunkte

Der Server implementiert den **Streamable-HTTP**-Transport unter `/api/v1/mcp/`. Gemessen: `initialize` verhandelt die Protokollrevision `2025-06-18`, antwortet mit `content-type: application/json` und **vergibt eine `Mcp-Session-Id`**, die Folgeaufrufe zurückspiegeln. `serverInfo` meldet `{"name": "kamerplanter-mcp", "version": "1.0"}`.

Deklarierte Fähigkeiten, gemessen: **ausschließlich `tools`**, mit `listChanged: false`. Der Server bietet weder `prompts` noch `resources` an — ein Rezept, das eines davon erwartet, erhält nichts.

| Methode | Pfad | Zweck | Gemessen |
|---------|------|-------|----------|
| `POST` | `/mcp` | Der MCP-Endpunkt — JSON-RPC 2.0: `initialize`, `tools/list`, `tools/call`, `ping` | ✓ |
| `GET` | `/mcp` | `405` — der Server sendet keine servergetriebenen Nachrichten | ✓ `405` |
| `DELETE` | `/mcp` | Beendet die in `Mcp-Session-Id` genannte Sitzung | nicht geprüft |
| `GET` | `/mcp/tools` | REST-freundliche Werkzeugliste | nicht geprüft |
| `POST` | `/mcp/tools/{tool_name}` | REST-freundlicher Werkzeugaufruf, JSON-Body als Argumente | nicht geprüft |
| `POST` | `/mcp/rpc` | Beibehaltener Alias von `POST /mcp` (veraltet) | nicht geprüft |

Ein stdio-Transport ist Upstream spezifiziert, aber nicht implementiert; verfügbar ist nur Streamable HTTP.

### Authentifizierung

Der Server akzeptiert **ausschließlich API-Keys** — nie ein JWT-Access-Token, nie eine interaktive Sitzung. Der Schlüssel trägt das Präfix `kp_` und reist als `X-API-Key` oder `Authorization: Bearer kp_...`. Gemessen: Eine Anfrage ohne Schlüssel antwortet `401`.

Der Server ist **standardmäßig deaktiviert**. Solange `MCP_SERVER_ENABLED=true` nicht gesetzt ist, antwortet jeder `/mcp/*`-Endpunkt mit `404` — die Schnittstelle existiert effektiv nicht.

### Mandantenfähigkeit

Ein Schlüssel gewährt genau die Gärten, in denen sein Konto aktives Mitglied ist. Welcher Garten für einen Aufruf gilt, entscheidet pro Aufruf das Argument `tenant` (der Slug des Gartens); bei genau einer Mitgliedschaft darf es entfallen, bei mehreren ist es erforderlich. Der Server löst **zuerst den Garten** auf und prüft **danach** die Berechtigung — umgekehrt geprüft hielte ein Schlüssel überall seine stärkste Rolle.

Ein Garten, den der Schlüssel nicht abdeckt, antwortet `not_found`, identisch zu einem nicht existierenden Garten; die Schnittstelle lässt sich damit nicht zum Aufspüren fremder Gärten verwenden.

Gemessen: `list_tenants` liefert je Garten `slug`, `name`, `role` **und das aufgelöste Array `mcp_permissions`**. Ein Rezept kann damit vorab feststellen, was es darf, statt die Grenze durch eine Ablehnung zu entdecken.

### Berechtigungsklassen

Jedes Tool erfordert genau eine von drei Berechtigungen, gebunden an die Rolle, die das Konto **im adressierten Garten** hält:

| Tenant-Rolle | `mcp.read` | `mcp.write` | `mcp.setup` | Quelle |
|--------------|:----------:|:-----------:|:-----------:|--------|
| viewer | ✓ | ✗ | ✗ | dokumentiert |
| grower | ✓ | ✓ | ✗ | dokumentiert |
| admin | ✓ | ✓ | ✓ | dokumentiert |
| `lead` | ✓ | ✓ | ✓ | **gemessen, undokumentiert** |

Das Konto der Referenzinstanz hält die Rolle `lead` mit allen drei Berechtigungen. Diese Rolle taucht in keiner Upstream-Rollentabelle auf. Rezepte **dürfen** Berechtigungen daher **nicht** aus dem Rollennamen ableiten; das Array `mcp_permissions` ist die einzig verlässliche Quelle.

Ein Aufruf ohne die Berechtigung wird mit `permission.denied` abgelehnt und als `status: "denied"` auditiert.

## Werkzeugkatalog (gemessen, 12 Tools, 2026-08-04)

Der laufende Katalog deckt sich exakt mit dem dokumentierten. Anders als bei Home Assistant trägt **jedes `inputSchema` ein vollständiges JSON Schema** — gemessene Schlüssel umfassen `required`, `properties`, `$defs`, `additionalProperties` und `title` —, sodass ein Client Pflicht- von Optionalargumenten unterscheiden kann, ohne dass man es ihm sagt.

### Lesetools (`mcp.read`)

| Tool | Pflicht | Nimmt `tenant` | Zweck |
|------|---------|:--------------:|-------|
| `list_tenants` | — | nein | Gärten des Schlüssels, mit Rolle und `mcp_permissions` |
| `list_species` | — | nein | Katalog der Pflanzenarten (`limit`, `offset`) |
| `get_species_info` | `species_key` | nein | Stammdaten einer Art, inkl. Hinweisen zur Mischkultur |
| `list_planting_runs` | — | ja | Anbauläufe (`status`, `limit`, `offset`) |
| `list_tasks` | — | ja | Aufgaben (`status`, `limit`, `offset`) |
| `get_due_care_tasks` | — | ja | Fällige und überfällige Pflegeerinnerungen (`urgency`) |
| `get_harvest_readiness` | — | ja | Übersicht der Erntereife (`limit`) |
| `get_mcp_activity` | — | nein | Die eigene MCP-Aufrufhistorie des Kontos (`limit`) |

Drei Lesetools nehmen kein `tenant`: `list_tenants` und `get_mcp_activity` sind kontobezogen, `list_species` / `get_species_info` bedienen den gemeinsamen Artenkatalog.

### Schreibtools (`mcp.write`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `confirm_care_task` | `plant_key`, `reminder_type` | Eine Pflegeerinnerung für eine Pflanze bestätigen |
| `archive_plant` | `plant_key` | Eine Pflanze als entsorgt / verschenkt / eingegangen markieren — nie ein hartes Löschen |
| `set_plant_location` | `plant_key` | Eine Pflanze an einen anderen Standort, Ort oder Platz verschieben |

### Setup-Tool (`mcp.setup`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `create_site` | `name` | Einen Standort-Wurzelknoten anlegen (Wohnung, Garten, Balkon, Gewächshaus, Fensterbank, Growbox) |

Gemessen: Alle vier zustandsändernden Tools bieten `tenant`, `dry_run` und `idempotency_key` an.

### Antwort-Hülle

Gemessen trägt ein `tools/call`-Ergebnis `isError`, ein MCP-übliches `content`-Array mit der Zusammenfassung als `type: "text"` sowie ein Objekt **`structuredContent`** mit den drei dokumentierten Feldern: `summary` (Einsatz-Zusammenfassung), `data` (das strukturierte Ergebnis), `links` (Verweise in die Oberfläche oder die REST-API). Die dokumentierte Hülle liegt also unter `structuredContent`, nicht auf oberster Ebene.

`dry_run` (Standard `false`) liefert die geplante Wirkung, ohne zu persistieren. `idempotency_key` lässt einen identischen Schlüssel desselben Kontos, Mandanten und Tools 24 Stunden lang das ursprüngliche Ergebnis wiederholen, gekennzeichnet mit `"idempotent_replay": true`.

Jeder Aufruf wird mit einem SHA-256-Hash der Argumente auditiert — nie im Klartext, nie mit dem Schlüssel. Audit-Einträge werden nach 90 Tagen entfernt.

## Anforderungen

- **MUSS [MUST]** den Server über eine `streamable_http`-Extension erreichen, die auf `${KAMERPLANTER_URL}/api/v1/mcp` zeigt, deklariert entweder im eigenen `extensions:`-Block des Rezepts oder in der geteilten `extensions.yaml` des Repositorys
- **DARF NICHT [MUST NOT]** einen eigenen `extensions:`-Block deklarieren, wenn es sich auf die geteilte `extensions.yaml` stützt; ein rezeptlokaler Block **ersetzt** den geteilten Satz, statt ihn zu erweitern, und lässt dabei still jeden Server fallen, den das Rezept nicht erneut deklariert
- **MUSS [MUST]** `KAMERPLANTER_URL` und `KAMERPLANTER_API_KEY` in den `env_keys` dieser Extension aufführen, wo immer sie deklariert ist; ohne das sendet Goose die literale Zeichenkette `${...}` als Header-Wert
- **MUSS [MUST]** die Zugangsdaten als Header `X-API-Key` übergeben, nie als URL-Parameter und nie eingebettet in einer Rezept- oder Konfigurationsdatei
- **MUSS [MUST]** den Garten explizit auflösen: entweder einen `tenant`-Rezeptparameter annehmen oder zuerst `list_tenants` aufrufen; ein Rezept **DARF NICHT [MUST NOT]** annehmen, dass der Schlüssel genau einen Garten abdeckt
- **MUSS [MUST]** jedes verbotene Schreibtool im `prompt` des Rezepts benennen, wenn das Rezept nur liest — `instructions` allein wird bei einem Headless-Lauf nicht durchgesetzt; zu benennen sind die vier: `confirm_care_task`, `archive_plant`, `set_plant_location`, `create_site`
- **MUSS [MUST]** das Suffix `-apply` im Dateinamen tragen und die Wirkung in `description` benennen, wenn ein Rezept ein `mcp.write`- oder `mcp.setup`-Tool aufruft
- **DARF NICHT [MUST NOT]** aus dem Rollennamen eines Gartens ableiten, was es darf; das Array `mcp_permissions` aus `list_tenants` ist die einzig verlässliche Quelle, und es existieren undokumentierte Rollen
- **DARF NICHT [MUST NOT]** `prompts` oder `resources` von diesem Server erwarten; er bietet ausschließlich die `tools`-Fähigkeit an
- **SOLLTE [SHOULD]** `mcp_permissions` aus `list_tenants` lesen, bevor es schreibt, und eine fehlende Berechtigung als Vorbedingung melden, statt `permission.denied` zu provozieren
- **SOLLTE [SHOULD]** ein Schreibtool zuerst mit `dry_run: true` aufrufen, wenn das Rezept einem Menschen eine geplante Aktion zur Bestätigung meldet
- **SOLLTE [SHOULD]** bei jedem Schreibaufruf einen `idempotency_key` übergeben, damit ein wiederholter Lauf die Aktion nicht dupliziert
- **SOLLTE [SHOULD]** `not_found` für einen benannten Garten als „von diesem Schlüssel nicht abgedeckt" behandeln statt als „existiert nicht" und dies im Bericht sagen
- **DARF NICHT [MUST NOT]** ein `404` auf dem Endpunkt als falsche URL deuten, ohne `MCP_SERVER_ENABLED` als wahrscheinliche Ursache zu benennen; ein fehlender oder ungültiger Schlüssel antwortet `401`, was ein anderer Fehler ist
- **DARF NICHT [MUST NOT]** ein Tool aufrufen, das der Katalog dieser Spec nicht führt; nicht gelistete Tools sind Upstream nicht implementiert
- **KANN [MAY]** die REST-freundliche Form `POST /mcp/tools/{tool_name}` zur Diagnose außerhalb eines Rezepts nutzen, **DARF** sich aber innerhalb eines Rezepts **NICHT [MUST NOT]** darauf stützen

## Akzeptanzkriterien

- [ ] Die Extension ist genau einmal deklariert — im Rezept oder in `extensions.yaml` — und benennt `streamable_http`, den Pfad `/api/v1/mcp` und beide Env-Keys
- [ ] Kein Rezept, das sich auf die geteilte `extensions.yaml` stützt, deklariert einen eigenen `extensions:`-Block
- [ ] `goose recipe validate` läuft für das Rezept durch
- [ ] Ein Lauf gegen einen Server ohne gesetztes `MCP_SERVER_ENABLED` meldet die Opt-in-Variable, keinen URL-Fehler
- [ ] Ein Lauf mit fehlendem oder widerrufenem Schlüssel meldet `401` als Authentifizierungsfehler, unterscheidbar von einem Berechtigungsfehler
- [ ] Ein nur lesendes Rezept benennt alle vier zustandsändernden Tools als verboten innerhalb von `prompt`
- [ ] Jedes Rezept, das ein Schreibtool aufruft, trägt einen `-apply`-Dateinamen und sagt dies in `description`
- [ ] Ein Rezeptlauf mit einem Schlüssel über zwei Gärten nimmt entweder `tenant` als Parameter an oder ruft `list_tenants` vor jedem mandantenbezogenen Tool auf
- [ ] Kein Rezept leitet Berechtigungen aus einem Rollennamen statt aus `mcp_permissions` ab
- [ ] Kein Rezept referenziert ein Tool außerhalb des obigen Katalogs
- [ ] Kein Rezept setzt `prompts/list` oder `resources/list` gegen diesen Server ab

## Offene Fragen

- Die Rolle `lead` ist auf der Referenzinstanz gemessen, taucht aber in keiner Upstream-Rollentabelle auf. Ob sie eine Umbenennung von `admin`, eine eigenständige vierte Rolle oder instanzlokale Konfiguration ist, ist ungeklärt — daher die Regel, `mcp_permissions` statt der Rolle zu lesen.
- Ob die `Mcp-Session-Id` bei jedem Aufruf zurückgespiegelt werden muss oder nur innerhalb eines Sitzungsfensters; die Referenzprüfung hat sie durchgehend mitgesendet und den Fall ohne sie nicht getestet.
- Ob `get_mcp_activity` als Selbstprüfungsschritt am Ende eines `-apply`-Rezepts nützt oder nur Rauschen erzeugt.
- Der Upstream-Katalog ist als auf rund 30 Tools wachsend dokumentiert. Diese Spec hat noch keinen Mechanismus, um zu erkennen, dass der laufende Server Tools anbietet, die dieses Dokument nicht führt; heute stimmen beide exakt überein.

## Quelle

- Live-Messung der Referenzinstanz, 2026-08-04: `initialize` (Protokoll `2025-06-18`, `Mcp-Session-Id`, Fähigkeiten nur `tools`), `tools/list` (12 Tools mit vollständigem JSON Schema), `tools/call list_tenants` (Rolle `lead`, `mcp_permissions`, `structuredContent`-Hülle), `GET /mcp` → `405`, unauthentifiziertes `POST` → `401`
- `nolte/kamerplanter` — `docs/en/api/mcp-server.md` (Transport, Authentifizierung, Mandantenfähigkeit, dokumentierte Berechtigungsklassen, Werkzeugzwecke, Audit-Trail), gelesen am 2026-08-04
- `env_keys`-Verhalten von Goose gemessen gegen Goose 1.45.0 durch Mitschnitt der tatsächlich gesendeten Requests; siehe `README.md` §Notes
