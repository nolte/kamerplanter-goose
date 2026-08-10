# Kamerplanter MCP Server

Status: Entwurf
Portfolio-Scope: local

## Kontext

Rezepte in diesem Repository erreichen Pflanzendaten über den MCP-Server, der im Kamerplanter-Backend mitläuft. Dieser Server ist kein generisches REST-Abbild: Er stellt eine kuratierte, semantisch hochstehende Werkzeugpalette bereit, bei der ein Tool einen ganzen Anwendungsfall kapselt und kompaktes JSON zurückgibt, statt dass das Modell mehrere REST-Aufrufe verketten muss.

Zwei Eigenschaften machen eine Spezifikation lohnender als eine Entdeckung pro Rezept. Erstens ist der Werkzeugkatalog **aufzählbar und vollständig schematisiert** — jedes Tool deklariert ein komplettes JSON Schema, sodass die gesamte Oberfläche durch eine einzige Abfrage vorab bekannt ist. Das ist der scharfe Gegensatz zu [Home Assistant](../home-assistant-mcp-server/de.md), dessen Katalog zur Laufzeit zusammengesetzt wird und pro Instanz abweicht. Aufzählbar heißt aber nicht fest: Zwischen zwei Messungen im Abstand von drei Tagen wuchs der Katalog von 12 auf 43 Tools — die Oberfläche ist also je Instanz und je Datum erkennbar, nicht ein für alle Mal. Zweitens ist der Server **mandantenfähig mit einem Berechtigungsmodell pro Garten**, sodass derselbe Schlüssel in einem Garten schreiben darf und in einem anderen dieselbe Aktion verweigert bekommt. Ein Rezept, das dies ignoriert, erzeugt Fehler, die wie Bugs aussehen, aber korrekte Ablehnungen sind.

Alles unten als *gemessen* Gekennzeichnete wurde von der Referenzinstanz über `initialize`, `tools/list` und nur lesende `tools/call`-Aufrufe gelesen — Transport, Authentifizierung und Mandantenfähigkeit am 2026-08-04, der Werkzeugkatalog und seine Feldstrukturen am 2026-08-07. Die Upstream-Dokumentation kennzeichnete den Server bei der ersten Messung als **teilweise verfügbar**, mit 12 von rund 30 spezifizierten Tools; die zweite Messung fand 43. Die Implementierung hat diesen Stand also überholt, und die Dokumentation ist für den Umfang nicht mehr maßgeblich.

Rezept-Mechanik — wo eine Extension deklariert werden darf, wie sich die `env_keys`-Ersetzung verhält, was der Provider dem Agenten hinzufügt — ist einmal im [Goose-Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md) spezifiziert und wird hier nicht wiederholt.

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

## Werkzeugkatalog (gemessen, 43 Tools, 2026-08-07)

Anders als bei Home Assistant trägt **jedes `inputSchema` ein vollständiges JSON Schema** — gemessene Schlüssel umfassen `required`, `properties`, `$defs`, `additionalProperties` und `title` —, sodass ein Client Pflicht- von Optionalargumenten unterscheiden kann, ohne dass man es ihm sagt.

Der Katalog wächst zwischen zwei Messungen. Eine Inventur am 2026-08-04 ergab 12 Tools und deckte sich mit der damaligen Dokumentation; eine erneute Inventur am 2026-08-07 ergab **43** — 31 mehr, davon 28 Lesetools und drei Schreibtools (`add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis`). **Jede Zahl hier ist eine Untergrenze, keine Zusicherung** — vor der Annahme, ein Tool fehle, ist `tools/list` erneut abzufragen.

### Lesetools (`mcp.read`), 36 gemessen

Gruppiert danach, wonach ein Rezept greift, nicht nach der Schichtung des Servers.

| Gruppe | Tools |
|--------|-------|
| Konto und Mandant | `list_tenants`, `get_mcp_activity` |
| Pflanzen | `list_plants`, `get_plant`, `list_plants_at_location`, `list_planting_runs` |
| Arten und Sorten | `list_species`, `get_species_info`, `list_cultivars`, `get_cultivar` |
| Phasen und Lebenszyklus | `list_phase_definitions`, `get_sowing_calendar`, `list_overwintering_profiles`, `list_hardiness_zones` |
| Pflege und Aufgaben | `list_tasks`, `get_due_care_tasks`, `get_plant_care_log`, `get_harvest_readiness` |
| Ernährung und Medium | `get_plant_nutrient_plan`, `list_nutrient_plans`, `get_nutrient_plan`, `list_fertilizers`, `list_substrates`, `calculate_mixing_protocol` |
| Pflanzenschutz | `get_plant_inspections`, `list_pests`, `get_pest`, `list_diseases`, `get_disease`, `get_treatment` |
| Tagebuch | `list_diary_entries`, `get_diary_entry`, `get_diary_entry_photos`, `list_pending_diary_analyses` |
| Einstieg und Fachvokabular | `list_starter_kits`, `search_glossary` |

Signaturen, die eigens zu nennen sind, weil ein Rezept sie sonst falsch bedient:

| Tool | Pflicht | Nimmt `tenant` | Anmerkung |
|------|---------|:--------------:|-----------|
| `get_species_info` | `species_key` | nein | `include_cultivars` optional; bedient den gemeinsamen Katalog |
| `get_pest` | `pest_key` | nein | Liefert verschachtelte `treatments[]` und `beneficials[]` in einem Aufruf |
| `get_disease` | `disease_key` | nein | Trägt `environmental_triggers[]` und `incubation_period_days` |
| `get_treatment` | `treatment_key` | nein | Trägt `safety_interval_days` — die Karenz vor der Ernte |
| `get_plant_inspections` | `plant_key` | ja | IPM-Historie; gemessen leer bei einer nie inspizierten Pflanze |
| `get_sowing_calendar` | — | ja | **Verweigert einen unspezifizierten Aufruf**: Ohne `query` antwortet er `validation.error` mit der Artenzahl und der `limit`-Obergrenze 25 |
| `list_phase_definitions` | — | nein | 29 Definitionen gemessen; das Vokabular der Lebenszyklus-Engine |
| `search_glossary` | — | nein | Die projekteigenen Definitionen von EC, VPD, Karenz |

`calculate_mixing_protocol` rechnet und persistiert nichts — deshalb steht es trotz seines Namens bei den Lesetools.

Fünfzehn Lesetools nehmen kein `tenant`: `list_tenants` und `get_mcp_activity` sind kontobezogen, und die Kataloge für Arten, Sorten, Schädlinge, Krankheiten, Behandlungen, Substrate, Glossar, Winterhärtezonen und Phasendefinitionen gelten gartenübergreifend. Die Aufteilung gilt je Tool und wurde aus dem jeweiligen `inputSchema` gelesen, nicht aus der Gruppe erschlossen, in der ein Tool steht: `list_substrates` nimmt kein `tenant`, `list_fertilizers` in derselben Gruppe schon. Für die übrigen, mandantengebundenen Tools gilt die Mandantenregel von oben — optional bei einem Schlüssel mit einer Mitgliedschaft, verpflichtend bei mehreren —, aus diesem Abschnitt lässt sich also nicht ableiten, dass das Weglassen je unbedenklich wäre.

### Schreibtools (`mcp.write`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `add_plant_diary_entry` | `plant_key`, `text` | Eine Beobachtung, ein Problem oder eine Messung festhalten |
| `confirm_care_task` | `plant_key`, `reminder_type` | Eine Pflegeerinnerung für eine Pflanze bestätigen |
| `archive_plant` | `plant_key` | Eine Pflanze als entsorgt / verschenkt / eingegangen markieren — nie ein hartes Löschen |
| `set_plant_location` | `plant_key` | Eine Pflanze an einen anderen Standort, Ort oder Platz verschieben |
| `claim_diary_analysis` | `entry_key`, `worker_id` | Einen Eintrag unter einer Lease zur Analyse beanspruchen |
| `submit_diary_analysis` | `entry_key`, `lease_token`, `status` | Ein Ergebnis zurückschreiben und den Anspruch beenden |

### Setup-Tool (`mcp.setup`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `create_site` | `name` | Einen Standort-Wurzelknoten anlegen (Wohnung, Garten, Balkon, Gewächshaus, Fensterbank, Growbox) |

Gemessen: Jedes zustandsändernde Tool bietet `dry_run` und `idempotency_key` an, und kein Lesetool trägt eines davon — das ist der billigste Weg, die beiden Klassen in einer `tools/list`-Antwort zu unterscheiden. `tenant` trennt sie **nicht**: Alle sieben zustandsändernden Tools nehmen es — die sechs `mcp.write`-Tools und das eine `mcp.setup`-Tool — und 21 der 36 Lesetools ebenfalls. Schreibtools sind wie alles andere mandantengebunden, die Mandantenregel von oben gilt für sie also vollständig: Bei einem Schlüssel über mehrere Gärten ist ein Schreibaufruf ohne `tenant` ein Fehler, kein Standardwert.

### Was der Katalog nicht trägt

Zwei Lücken sind bedeutsam, weil ein Verfahren, das das Feld voraussetzt, eine selbstsichere Antwort ohne Grundlage erzeugt. Beide gemessen am 2026-08-07:

- **`get_pest` hat keine Felder zu Luftfeuchte, Wirtspflanzen, Prävention oder Monitoring.** Gemessen an `Tetranychus urticae` besteht der Datensatz aus `pest_key`, `scientific_name`, `common_name`, `common_name_de`, `pest_type`, `damage_symptoms`, `lifecycle_days`, `optimal_temp_min`, `optimal_temp_max`, `description`, `detection_symptom_hint` sowie den verschachtelten `treatments[]` und `beneficials[]`. Es gibt kein `optimal_humidity_min/max`, keine `host_plants`, keine `prevention_tips`, keine `monitoring_hints`, keine `affected_plant_parts`, keine Einstufung von Schwere oder Erkennungsschwierigkeit und keinen GBIF-Schlüssel. `get_disease` **trägt** dagegen `environmental_triggers[]` (`low_humidity`, `high_humidity`, `poor_air_circulation`, …) — die Feuchteachse existiert also für Krankheiten und nicht für Schädlinge.
- **`get_species_info` liefert nur die befüllten Felder**, und die Menge unterscheidet sich je Art. Gemessen lieferte `Allium porrum` 23 Felder samt vollständigem `seed_profile` (`germination_temp_min_c`/`max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination`, `pretreatment[]`, `thousand_seed_weight_g`, `sowing_density_per_m2`) und `growing_periods[]`; `Spathiphyllum wallisii` lieferte 18, mit `plant_category` und ganz ohne `seed_profile`. Keine der beiden trug `toxicity`, obwohl die Beschreibung des Tools es ausweist. Ein fehlender Schlüssel bedeutet „für diese Art nicht befüllt", nie „trifft nicht zu".

### Antwort-Hülle

Gemessen trägt ein `tools/call`-Ergebnis `isError`, ein MCP-übliches `content`-Array mit der Zusammenfassung als `type: "text"` sowie ein Objekt **`structuredContent`** mit den drei dokumentierten Feldern: `summary` (Einsatz-Zusammenfassung), `data` (das strukturierte Ergebnis), `links` (Verweise in die Oberfläche oder die REST-API). Die dokumentierte Hülle liegt also unter `structuredContent`, nicht auf oberster Ebene.

`dry_run` (Standard `false`) liefert die geplante Wirkung, ohne zu persistieren. `idempotency_key` lässt einen identischen Schlüssel desselben Kontos, Mandanten und Tools 24 Stunden lang das ursprüngliche Ergebnis wiederholen, gekennzeichnet mit `"idempotent_replay": true`.

Jeder Aufruf wird mit einem SHA-256-Hash der Argumente auditiert — nie im Klartext, nie mit dem Schlüssel. Audit-Einträge werden nach 90 Tagen entfernt.

## Anforderungen

- **MUSS [MUST]** den Server über eine `streamable_http`-Extension erreichen, die auf `${KAMERPLANTER_URL}/api/v1/mcp` zeigt, deklariert entweder im eigenen `extensions:`-Block des Rezepts oder in der geteilten `extensions.yaml` des Repositorys
- **MUSS [MUST]** `KAMERPLANTER_URL` und `KAMERPLANTER_API_KEY` in den `env_keys` dieser Extension aufführen, wo immer sie deklariert ist; ohne das sendet Goose die literale Zeichenkette `${...}` als Header-Wert
- **MUSS [MUST]** die Zugangsdaten als Header `X-API-Key` übergeben, nie als URL-Parameter und nie eingebettet in einer Rezept- oder Konfigurationsdatei
- **MUSS [MUST]** den Garten explizit auflösen: entweder einen `tenant`-Rezeptparameter annehmen oder zuerst `list_tenants` aufrufen; ein Rezept **DARF NICHT [MUST NOT]** annehmen, dass der Schlüssel genau einen Garten abdeckt
- **MUSS [MUST]** jedes verbotene zustandsändernde Tool im `prompt` des Rezepts einzeln benennen, wenn das Rezept nur liest — `instructions` allein wird in einem Headless-Lauf nicht durchgesetzt. Die Katalogmessung hat diese Liste von vier auf sieben gehoben: `confirm_care_task`, `archive_plant`, `set_plant_location`, `create_site`, `add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis` (sechs `mcp.write` plus das eine `mcp.setup`). Eine Teilmenge zu nennen ist der Fehler, für den diese Regel existiert, und eine Kategorie („und alles andere, was schreibt") ersetzt keinen der sieben Namen: Das Verbot darf nicht von der Klassifikation des Modells abhängen. Ein schreibfähiges `-apply`-Rezept ist die Ausnahme, die das Wort *verboten* bereits enthält — die Werkzeuge, für die es existiert, werden deklariert, nicht verboten
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
- [ ] `goose recipe validate` läuft für das Rezept durch
- [ ] Ein Lauf gegen einen Server ohne gesetztes `MCP_SERVER_ENABLED` meldet die Opt-in-Variable, keinen URL-Fehler
- [ ] Ein Lauf mit fehlendem oder widerrufenem Schlüssel meldet `401` als Authentifizierungsfehler, unterscheidbar von einem Berechtigungsfehler
- [ ] Jedes nur lesende Rezept nennt alle sieben zustandsändernden Tools einzeln in seinem `prompt` — nie eine Teilmenge, nie eine Kategorie anstelle eines Namens
- [ ] Eine maschinelle Prüfung setzt das obige Kriterium durch; eine nur in Prosa formulierte Regel ist zweimal von den Rezepten abgedriftet
- [ ] Jedes Rezept, das ein Schreibtool aufruft, trägt einen `-apply`-Dateinamen und sagt dies in `description`
- [ ] Ein Rezeptlauf mit einem Schlüssel über zwei Gärten nimmt entweder `tenant` als Parameter an oder ruft `list_tenants` vor jedem mandantenbezogenen Tool auf
- [ ] Kein Rezept leitet Berechtigungen aus einem Rollennamen statt aus `mcp_permissions` ab
- [ ] Kein Rezept referenziert ein Tool außerhalb des obigen Katalogs
- [ ] Kein Rezept setzt `prompts/list` oder `resources/list` gegen diesen Server ab

## Offene Fragen

- Drei ausgelieferte Rezepte erfüllen das obige Kriterium nicht: `connectivity-check` nennt vier von sieben, `provider-surface-check` und `provider-plugin-check` nennen keines und verlassen sich auf ein Pauschalverbot. Die konformen Prompts und die Validator-Prüfung, die sie durchsetzt, liegen auf `refactor/recipe-validator-guard`; bis das landet, ist das Kriterium eine Absichtserklärung und keine gemessene Eigenschaft dieses Repositories.

- Die Rolle `lead` ist auf der Referenzinstanz gemessen, taucht aber in keiner Upstream-Rollentabelle auf. Ob sie eine Umbenennung von `admin`, eine eigenständige vierte Rolle oder instanzlokale Konfiguration ist, ist ungeklärt — daher die Regel, `mcp_permissions` statt der Rolle zu lesen.
- Ob die `Mcp-Session-Id` bei jedem Aufruf zurückgespiegelt werden muss oder nur innerhalb eines Sitzungsfensters; die Referenzprüfung hat sie durchgehend mitgesendet und den Fall ohne sie nicht getestet.
- Ob `get_mcp_activity` als Selbstprüfungsschritt am Ende eines `-apply`-Rezepts nützt oder nur Rauschen erzeugt.
- Diese Spec hat keinen Mechanismus, um zu erkennen, dass der laufende Server Tools anbietet, die sie nicht führt. Zum Stand der Nachinventur vom 2026-08-07 stimmen beide überein — alle 43 sind hier aufgeführt —, aber nichts hält sie in Übereinstimmung, und die Drift, die diesen Abschnitt falsch machte, fiel von Hand auf, drei Tage nachdem sie entstanden war. Davon unabhängig: Upstream dokumentiert den Katalog weiterhin als auf rund 30 wachsend, was die Implementierung überholt hat.

## Quelle

- Live-Messung der Referenzinstanz, 2026-08-04: `initialize` (Protokoll `2025-06-18`, `Mcp-Session-Id`, Fähigkeiten nur `tools`), `tools/list` (12 Tools mit vollständigem JSON Schema), `tools/call list_tenants` (Rolle `lead`, `mcp_permissions`, `structuredContent`-Hülle), `GET /mcp` → `405`, unauthentifiziertes `POST` → `401`
- Zuordnung von `tenant`, `dry_run` und `idempotency_key` je Tool, abgeleitet aus der `tools/list`-Antwort vom 2026-08-07 durch Prüfung von `inputSchema.properties` auf diese Schlüssel — nicht aus der Gruppierung in diesem Dokument und nicht aus Aufrufen: Kein Schreibtool wurde aufgerufen, die Aussage betrifft also das deklarierte Schema, nicht beobachtetes Verhalten
- Live-Messung der Referenzinstanz, 2026-08-07: `tools/list` (43 Tools) sowie nur lesende `tools/call` für `list_tenants`, `list_pests`, `get_pest` (`Tetranychus urticae`), `list_diseases`, `list_species`, `get_species_info` (`Allium porrum`, `Spathiphyllum wallisii`), `list_plants`, `get_plant_inspections`, `list_phase_definitions`, `list_overwintering_profiles` und `get_sowing_calendar` (einmal unspezifiziert, was abgelehnt wurde, und einmal mit `query`). Kein Schreibtool wurde aufgerufen.
- `nolte/kamerplanter` — `docs/en/api/mcp-server.md` (Transport, Authentifizierung, Mandantenfähigkeit, dokumentierte Berechtigungsklassen, Werkzeugzwecke, Audit-Trail), gelesen am 2026-08-04
- `env_keys`-Verhalten von Goose gemessen gegen Goose 1.45.0 durch Mitschnitt der tatsächlich gesendeten Requests; siehe `README.md` §Notes
