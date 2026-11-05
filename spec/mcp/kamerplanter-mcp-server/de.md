# Kamerplanter MCP Server

Status: Entwurf
Portfolio-Scope: local

## Kontext

Rezepte in diesem Repository erreichen Pflanzendaten über den MCP-Server, der im Kamerplanter-Backend mitläuft. Dieser Server ist kein generisches REST-Abbild: Er stellt eine kuratierte, semantisch hochstehende Werkzeugpalette bereit, bei der ein Tool einen ganzen Anwendungsfall kapselt und kompaktes JSON zurückgibt, statt dass das Modell mehrere REST-Aufrufe verketten muss.

Zwei Eigenschaften machen eine Spezifikation lohnender als eine Entdeckung pro Rezept. Erstens ist der Werkzeugkatalog **aufzählbar und vollständig schematisiert** — jedes Tool deklariert ein komplettes JSON Schema, sodass die gesamte Oberfläche durch eine einzige Abfrage vorab bekannt ist. Das ist der scharfe Gegensatz zu [Home Assistant](../home-assistant-mcp-server/de.md), dessen Katalog zur Laufzeit zusammengesetzt wird und pro Instanz abweicht. Aufzählbar heißt aber nicht fest: Zwischen zwei Messungen im Abstand von drei Tagen wuchs der Katalog von 12 auf 43 Tools und neun Tage später auf 56, und ein lokaler Build zählte am 2026-11-05 67 — die Oberfläche ist also je Instanz und je Datum erkennbar, nicht ein für alle Mal. Zweitens ist der Server **mandantenfähig mit einem Berechtigungsmodell pro Garten**, sodass derselbe Schlüssel in einem Garten schreiben darf und in einem anderen dieselbe Aktion verweigert bekommt. Ein Rezept, das dies ignoriert, erzeugt Fehler, die wie Bugs aussehen, aber korrekte Ablehnungen sind.

Alles unten als *gemessen* Gekennzeichnete wurde von der Referenzinstanz gelesen — Transport, Authentifizierung und Mandantenfähigkeit am 2026-08-04 über `initialize`, `tools/list` und nur lesende `tools/call`-Aufrufe; der Werkzeugkatalog und seine Feldstrukturen am 2026-08-07 auf demselben Weg; der Katalog am 2026-08-16 neu gezählt anhand der Werkzeugoberfläche, die eine Goose-Sitzung erhält, wobei das `inputSchema` jedes neuen Tools von dieser Oberfläche gelesen und mehrere davon aufgerufen wurden. Die Zählung vom 2026-11-05 ist die Ausnahme: Sie stammt von einer lokalen Instanz aus `nolte/kamerplanter` @ `5fc20429a`, und ob die Referenzinstanz dieselben 67 Tools anbietet, ist nicht gemessen. Die Upstream-Dokumentation kennzeichnete den Server bei der ersten Messung als **teilweise verfügbar**, mit 12 von rund 30 spezifizierten Tools; die zweite Messung fand 43, die dritte 56. Die Implementierung hat diesen Stand also überholt, und die Dokumentation ist für den Umfang nicht mehr maßgeblich.

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

## Werkzeugkatalog (gemessen, 67 Tools, 2026-11-05)

Anders als bei Home Assistant trägt **jedes `inputSchema` ein vollständiges JSON Schema** — gemessene Schlüssel umfassen `required`, `properties`, `$defs`, `additionalProperties` und `title` —, sodass ein Client Pflicht- von Optionalargumenten unterscheiden kann, ohne dass man es ihm sagt.

Der Katalog wächst zwischen zwei Messungen. Eine Inventur am 2026-08-04 ergab 12 Tools und deckte sich mit der damaligen Dokumentation; eine erneute Inventur am 2026-08-07 ergab **43** — 31 mehr, davon 28 Lesetools und drei Schreibtools (`add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis`). Eine dritte Zählung am 2026-08-16 ergab **56** — 13 mehr, davon acht Lesetools und fünf Schreibtools. Der Zuwachs ist eine zusammenhängende Schicht und keine verstreute Ergänzung: die Oberfläche für Lebenszyklus und Phasenabläufe (`get_plant_phase_status`, `get_plant_phase_history`, `get_species_lifecycle`, `get_species_phase_sequence`, `list_phase_sequences`, `list_species_by_phase_sequence`, `assign_species_phase_sequence`, `transition_plant_phase`), dazu Diagnostik, IPM-Rückschreibung, Düngeereignisse, Nährstoffplan-Zuweisung und eine Wissenssuche. Eine vierte Zählung am 2026-11-05, an einer lokalen Instanz aus `nolte/kamerplanter` @ `5fc20429a` statt an der Referenzinstanz, ergab **67** — 11 mehr, davon sieben Lese- und vier Schreibtools, wieder eine Schicht: Substratpflege (`get_substrate`, `list_substrate_batches`, `get_substrate_batch`, `check_batch_reusability`, `preview_substrate_mix`, `create_substrate_mix`, `set_plant_substrate`), Nährstoffplanpflege (`clone_nutrient_plan`, `set_nutrient_plan_phase_targets`, `validate_nutrient_plan_coverage`) und `get_location`. **Jede Zahl hier ist eine Untergrenze, keine Zusicherung** — vor der Annahme, ein Tool fehle, ist `tools/list` erneut abzufragen.

Zwei gemessene Vorbehalte zur Oberfläche vom 2026-08-16, denn ein deklariertes Tool ist nicht dasselbe wie ein funktionierendes:

- **`search_plant_knowledge` ist deklariert, hier aber nicht ausgerollt.** Es antwortet `service.unavailable: The knowledge base is not reachable right now; retry later. It is an optional component and may not be deployed on this instance.` — eine saubere, typisierte Ablehnung und genau die Form, die ein Rezept von einer optionalen Komponente erwarten sollte.
- **`get_mcp_activity` antwortete bei jedem Aufruf mit `INTERNAL_ERROR`** (drei Versuche, verschiedene `limit`-Werte, unterschiedliche Referenz-IDs). Das ist ein Serverdefekt und keine Katalogeigenschaft — gemeldet als `nolte/kamerplanter#1145` —, aber ein Rezept, das einen Selbstaudit-Schritt plant, darf nicht voraussetzen, dass das Tool antwortet.

### Lesetools (`mcp.read`), 51 gemessen

Gruppiert danach, wonach ein Rezept greift, nicht nach der Schichtung des Servers.

| Gruppe | Tools |
|--------|-------|
| Konto und Mandant | `list_tenants`, `get_mcp_activity` |
| Pflanzen | `list_plants`, `get_plant`, `list_plants_at_location`, `list_planting_runs`, `get_plant_diagnostics`, `get_location` |
| Arten und Sorten | `list_species`, `get_species_info`, `list_cultivars`, `get_cultivar`, `get_species_lifecycle` |
| Phasen und Lebenszyklus | `list_phase_definitions`, `get_sowing_calendar`, `list_overwintering_profiles`, `list_hardiness_zones`, `get_plant_phase_status`, `get_plant_phase_history`, `get_species_phase_sequence`, `list_phase_sequences`, `list_species_by_phase_sequence` |
| Pflege und Aufgaben | `list_tasks`, `get_due_care_tasks`, `get_plant_care_log`, `get_harvest_readiness` |
| Ernährung und Medium | `get_plant_nutrient_plan`, `list_nutrient_plans`, `get_nutrient_plan`, `validate_nutrient_plan_coverage`, `list_fertilizers`, `list_substrates`, `get_substrate`, `list_substrate_batches`, `get_substrate_batch`, `check_batch_reusability`, `calculate_mixing_protocol`, `preview_substrate_mix` |
| Pflanzenschutz | `get_plant_inspections`, `list_pests`, `get_pest`, `list_diseases`, `get_disease`, `get_treatment` |
| Tagebuch | `list_diary_entries`, `get_diary_entry`, `get_diary_entry_photos`, `list_pending_diary_analyses` |
| Einstieg und Fachvokabular | `list_starter_kits`, `search_glossary`, `search_plant_knowledge` |

Signaturen, die eigens zu nennen sind, weil ein Rezept sie sonst falsch bedient:

| Tool | Pflicht | Nimmt `tenant` | Anmerkung |
|------|---------|:--------------:|-----------|
| `get_species_info` | `species_key` | ja (optional) | `include_cultivars` optional; bedient den gemeinsamen Katalog, mit `tenant` zusätzlich die eigenen Einträge des Mandanten |
| `get_pest` | `pest_key` | nein | Liefert verschachtelte `treatments[]` und `beneficials[]` in einem Aufruf |
| `get_disease` | `disease_key` | nein | Trägt `environmental_triggers[]` und `incubation_period_days` |
| `get_treatment` | `treatment_key` | nein | Trägt `safety_interval_days` — die Karenz vor der Ernte |
| `get_plant_inspections` | `plant_key` | ja | IPM-Historie; gemessen leer bei einer nie inspizierten Pflanze |
| `get_plant_diagnostics` | `plant_key` | ja | `window_days` (Standard 14, 1–365) begrenzt jede Historie, die es liefert. Liefert `plant`, `window`, `ec_ph_trend` (EC und pH, je aufgeteilt in `input`, `after`, `runoff`, `sensor`), `feeding_events[]`, `sensors`, `inspections`, `karenz`, `care_events`. **Das einzige Lesetool, das gemessen zurückgibt, was `record_feeding_event` geschrieben hat** — jedes Feld des Schreibaufrufs außer `dry_run` und `idempotency_key`, dazu `feeding_event_key` und `timestamp`; `get_plant_care_log` liefert nichts davon (2026-11-05, #54) |
| `get_sowing_calendar` | — | ja | **Verweigert einen unspezifizierten Aufruf**: Ohne `query` antwortet er `validation.error` mit der Artenzahl und der `limit`-Obergrenze 25 |
| `list_phase_definitions` | — | nein | 29 Definitionen gemessen; das Vokabular der Lebenszyklus-Engine |
| `search_glossary` | — | nein | Die projekteigenen Definitionen von EC, VPD, Karenz |
| `get_plant_phase_status` | `plant_key` | ja | Löst die Phase der Pflanze auf; antwortet `phase_state: unresolved`, wenn der offene Satz auf keine Phase zeigt — das liest sich wie ein normales Ergebnis und ist keines |
| `get_species_phase_sequence` | `species_key` | nein | Liefert `sequence: null` für eine ungebundene Art — ein gewöhnlicher Zustand, kein Fehler |
| `list_phase_sequences` | — | nein | 22 Abläufe gemessen; `include_entries` standardmäßig aus |
| `search_plant_knowledge` | `query` | nein | Optionale Komponente; siehe den Vorbehalt oben |

`calculate_mixing_protocol` und `preview_substrate_mix` rechnen und persistieren nichts — deshalb stehen sie trotz ihrer Namen bei den Lesetools.

Vierzehn Lesetools nehmen kein `tenant` (2026-11-05): `list_tenants` und `get_mcp_activity` sind kontobezogen, und die Kataloge für Schädlinge, Krankheiten, Behandlungen, Glossar, Winterhärtezonen, Phasendefinitionen, Phasenabläufe, Art-Lebenszyklen und Wissensbasis gelten gartenübergreifend. Am 2026-08-16 waren es zwanzig: `list_species`, `get_species_info`, `list_cultivars`, `get_cultivar`, `list_substrates` und `list_species_by_phase_sequence` haben seither ein optionales `tenant`, das den gemeinsamen Einträgen die eigenen des Mandanten hinzufügt. Die Aufteilung gilt je Tool und wurde aus dem jeweiligen `inputSchema` gelesen, nicht aus der Gruppe erschlossen, in der ein Tool steht: `get_species_lifecycle` nimmt kein `tenant`, `get_species_info` schon, und `get_species_phase_sequence` nimmt keines, während `get_plant_phase_status` in derselben Gruppe eines nimmt. Für die übrigen 37 gilt die Mandantenregel von oben — optional bei einem Schlüssel mit einer Mitgliedschaft, verpflichtend bei mehreren —, aus diesem Abschnitt lässt sich also nicht ableiten, dass das Weglassen je unbedenklich wäre.

### Schreibtools (`mcp.write`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `add_plant_diary_entry` | `plant_key`, `text` | Eine Beobachtung, ein Problem oder eine Messung festhalten |
| `confirm_care_task` | `plant_key`, `reminder_type` | Eine Pflegeerinnerung für eine Pflanze bestätigen |
| `archive_plant` | `plant_key` | Eine Pflanze als entsorgt / verschenkt / eingegangen markieren — nie ein hartes Löschen |
| `set_plant_location` | `plant_key` | Eine Pflanze an einen anderen Standort, Ort oder Platz verschieben |
| `claim_diary_analysis` | `entry_key`, `worker_id` | Einen Eintrag unter einer Lease zur Analyse beanspruchen |
| `submit_diary_analysis` | `entry_key`, `lease_token`, `status` | Ein Ergebnis zurückschreiben und den Anspruch beenden |
| `transition_plant_phase` | `plant_key`, `target_phase_key` | Eine Pflanze in eine Phase ihres aufgelösten Ablaufs überführen oder eine falsche reparieren |
| `assign_species_phase_sequence` | `species_key`, `sequence_key` | Eine Art an einen bestehenden Ablauf binden — **nimmt kein `tenant`**, siehe unten |
| `assign_nutrient_plan` | `plant_key`, `plan_key` | Einen bestehenden Nährstoffplan an eine Pflanze binden |
| `record_feeding_event` | `plant_key`, `volume_applied_liters` | Eine Fertigation festhalten: Menge, EC/pH davor und danach, Ablauf |
| `create_inspection` | `plant_key` | Eine IPM-Inspektion festhalten: Druckstufe, Symptome, strukturierte Befunde |
| `clone_nutrient_plan` | `plan_key` | Eine mandanteneigene Kopie eines Nährstoffplans ableiten, um sie zu korrigieren, ohne das Original zu berühren |
| `set_nutrient_plan_phase_targets` | `plan_key`, `phase` | Die EC-Ziele einer Phase in einem mandanteneigenen Plan ändern |
| `create_substrate_mix` | `name_de`, `name_en`, `components` | Eine Substratmischung anlegen, die dem Mandanten gehört |
| `set_plant_substrate` | `plant_key` | Substrat und/oder Charge einer Pflanze setzen, ohne andere Felder zu ändern |

### Setup-Tool (`mcp.setup`)

| Tool | Pflicht | Zweck |
|------|---------|-------|
| `create_site` | `name` | Einen Standort-Wurzelknoten anlegen (Wohnung, Garten, Balkon, Gewächshaus, Fensterbank, Growbox) |

Gemessen: Jedes zustandsändernde Tool bietet `dry_run` und `idempotency_key` an, und kein Lesetool trägt eines davon — das ist der billigste Weg, die beiden Klassen in einer `tools/list`-Antwort zu unterscheiden. Das galt am 2026-08-16 für alle zwölf und am 2026-11-05 für alle sechzehn und ist damit das einzige Unterscheidungsmerkmal, das jedes Katalogwachstum überstanden hat.

`tenant` trennt sie **nicht**, und seit dem 2026-08-16 gilt es nicht einmal mehr innerhalb der Schreibklasse. Fünfzehn der sechzehn zustandsändernden Tools nehmen `tenant`, ebenso 37 der 51 Lesetools (2026-11-05). Die Ausnahme ist **`assign_species_phase_sequence`, das keines nimmt**: Beide Argumente benennen Zeilen in gartenübergreifenden Katalogen — eine Art und einen Phasenablauf —, der Aufruf ist also überhaupt nicht auf einen Garten bezogen. Seine Wirkung ist es ebenso wenig: Eine Art neu zu binden ändert den aufgelösten Ablauf dieser Art in *jedem* Mandanten. Ein Rezept, das „kein `tenant`-Argument" als „harmlos" liest, hat die Schlussrichtung hier verkehrt.

Für die übrigen fünfzehn sind Schreibtools wie alles andere mandantengebunden, die Mandantenregel von oben gilt für sie also vollständig: Bei einem Schlüssel über mehrere Gärten ist ein Schreibaufruf ohne `tenant` ein Fehler, kein Standardwert.

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
- **MUSS [MUST]** jedes verbotene zustandsändernde Tool im `prompt` des Rezepts einzeln benennen, wenn das Rezept nur liest — `instructions` allein wird in einem Headless-Lauf nicht durchgesetzt. Aufeinanderfolgende Katalogmessungen haben diese Liste von vier auf sieben, dann auf zwölf und dann auf sechzehn gehoben: `confirm_care_task`, `archive_plant`, `set_plant_location`, `create_site`, `add_plant_diary_entry`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event`, `create_inspection`, `clone_nutrient_plan`, `set_nutrient_plan_phase_targets`, `create_substrate_mix`, `set_plant_substrate` (fünfzehn `mcp.write` plus das eine `mcp.setup`). Eine Teilmenge zu nennen ist der Fehler, für den diese Regel existiert, und eine Kategorie („und alles andere, was schreibt") ersetzt keinen der sechzehn Namen: Das Verbot darf nicht von der Klassifikation des Modells abhängen. Die Liste ist dreimal gewachsen; ein gegen einen früheren Stand geschriebenes Rezept ist heute eine Teilmenge — deshalb trägt die maschinelle Prüfung weiter unten die Regel und nicht dieser Absatz. Ein schreibfähiges `-apply`-Rezept ist die Ausnahme, die das Wort *verboten* bereits enthält — die Werkzeuge, für die es existiert, werden deklariert, nicht verboten
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
- [x] Jedes nur lesende Rezept nennt alle sechzehn zustandsändernden Tools einzeln in seinem `prompt` — nie eine Teilmenge, nie eine Kategorie anstelle eines Namens
- [x] Eine maschinelle Prüfung setzt das obige Kriterium durch; eine nur in Prosa formulierte Regel ist zweimal von den Rezepten abgedriftet
- [x] Jeder Skill, der diesen Server referenziert, nennt alle sechzehn zustandsändernden Tools, und eine maschinelle Prüfung setzt das durch; die Aufrufrichtung ist auf den deklarierten Anweisungsabschnitten durchgesetzt (siehe Offene Fragen)
- [ ] Jedes Rezept, das ein Schreibtool aufruft, trägt einen `-apply`-Dateinamen und sagt dies in `description`
- [ ] Ein Rezeptlauf mit einem Schlüssel über zwei Gärten nimmt entweder `tenant` als Parameter an oder ruft `list_tenants` vor jedem mandantenbezogenen Tool auf
- [ ] Kein Rezept leitet Berechtigungen aus einem Rollennamen statt aus `mcp_permissions` ab
- [ ] Kein Rezept referenziert ein Tool außerhalb des obigen Katalogs
- [ ] Kein Rezept setzt `prompts/list` oder `resources/list` gegen diesen Server ab

## Offene Fragen

- Das Kriterium zu den verbotenen Tools wurde nun dreimal durch denselben Mechanismus verfehlt, und das dritte Mal geschah innerhalb der Änderung, die das zweite behob. Die Messung vom 2026-08-07 hob die Liste auf sieben, und die Rezepte wurden darauf gebracht. Die Messung vom 2026-08-16 hob sie auf zwölf, und **neun der zehn ausgelieferten Rezepte nannten gemessen sieben** — jedes gegen den älteren Stand geschriebene war still zu einer Teilmenge geworden. Der erste Korrekturlauf in derselben Änderung behob nur drei, weil er die Rezeptliste aus einer früheren Fassung *dieses Absatzes* übernahm, statt die Rezepte zu messen; ein Review fand die übrigen sechs. Alle zehn nennen jetzt zwölf.

  Daraus folgt zweierlei. Erstens ist eine Prosa-Liste betroffener Artefakte in einer Spec selbst ein Risiko für veraltete Zahlen — der Absatz, den Sie gerade lesen, war die Quelle der unvollständigen Korrektur. Deshalb nennt er jetzt die Messmethode statt einer Namensliste.

  Zweitens die Lücke, die haltbar war, bis sie geschlossen wurde: `tests/validate_recipes.py` setzte lange die *`-apply`-Suffix*-Regel durch (ein Rezept, das ein Schreibtool außerhalb eines Policy-Blocks nennt, muss den Suffix tragen), nicht aber die *Vollständigkeits*-Regel (ein nur lesendes Rezept muss jedes zustandsändernde Tool nennen). Nur eine Validator-Prüfung für die zweite Regel hätte einen der drei Rückfälle gefangen. Es gibt sie jetzt; sie bezieht ihre Liste aus `STATE_CHANGING_TOOLS` — derselben Konstante, die die Katalogmessung pflegt —, gilt für jedes Rezept mit einem `prompt` und misst allein an diesem `prompt`, weil `instructions` in einem Headless-Lauf nicht durchgesetzt wird; ein Rezept ganz ohne `prompt` wird bereits von seiner eigenen Prüfung abgewiesen, und eine zusätzliche Meldung dazu würde diese Ursache verschütten. Sie auf Rezepte zu beschränken, die diesen Server nachweislich erreichen, wurde versucht und zurückgenommen: Die bloße Namensform ist ohne eine Liste der Lese-Tools nicht erkennbar, und genau eine solche Liste ist der Veralterungsdefekt, den diese Prüfung fangen soll.

  Zweierlei leistet sie bewusst nicht. Sie begrenzt nicht, was ein `-apply`-Rezept unter `Permitted by name:` deklariert — eines, das dort alle sechzehn führt, besteht; dafür bräuchte es ein Register erlaubter Writes je Rezept. Und eine Verbotsliste, die als ein kommentiertes Bullet je Tool oder als Tabelle geschrieben ist, endet am Marker und wird abgewiesen — ebenso eine Konjunktion vor dem letzten Namen: `` `a`, and `b`. `` lässt `b` außerhalb des Blocks stehen und als Aufruf melden. Die Namen müssen zusammenstehen, ununterbrochen von Prosa, die Erläuterung gehört hinter den Block. Ein Toolname in einem umzäunten Beispiel zählt dagegen als deklariert: Das ist der eine Weg, ein Rezept vollständiger aussehen zu lassen, als es ist, und bewusst als die harmlose Richtung offengelassen.

  Dieselbe Vollständigkeitsregel erreicht Skills, eingegrenzt durch einen Verweis auf `mcp__kamerplanter__` statt auf jeden Skill angewandt: Die vier Review-Linsen berühren nie einen Garten und nennen nichts. Sie liest die ganze Datei, also zählt ein Name irgendwo — auch einer innerhalb eines Aufrufs oder einer unter `## Gotchas`. Die Aufrufrichtung ist ein eigener Befolgungs-Guard (#55), der an der Überschriften-Konvention aus [dem Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md) ansetzt: Ein zustandsändernder Name in den Anweisungsabschnitten eines Skills, außerhalb eines `Forbidden by name:`- oder `Permitted by name:`-Blocks, ist ein Aufruf und besteht nur, wenn der eigene `Permitted by name:`-Block dieses Skills ihn führt. Dieser Guard wählt jeden Skill aus, nicht nur die, die diesen Server referenzieren, weil auch ein bloßer Name ein Aufruf ist und der Präfix-Selektor ihn nicht sieht. Eine Zeile hält eine Ausnahme für genau diese Zeile: die `APPLY CONTRACT`-Zeile in `plant-planning`, die die sechzehn aufzählt und die [§F der Planungs-Prozess-Spec](../../process/plant-planning-and-planting-calendar/de.md) in jedem Plan verlangt; die Ausnahme speichert die ganze Zeile und lässt das Gate fehlschlagen, sofern genau diese Zeile nicht genau einmal vorkommt — eine geänderte Zeile, eine Kopie oder eine neue Zeile mit denselben Anfangsworten ist damit wieder geprüft. Was der Guard nicht sehen kann, ist ein Aufruf unter `## Gotchas` oder `## Source` — das ist Erläuterung per Deklaration, und die Regel, die Aufrufe dort heraushält, stützt sich auf Review.

  Die beiden `-apply`-Rezepte fallen nicht unter das Kriterium, das nur nur lesende Rezepte bindet — sie führen aber eine ausdrückliche Aufteilung in `Permitted by name:` und `Forbidden by name:`, und die fünf neuen Tools standen in keiner von beiden. Sie wurden der Verbotsseite hinzugefügt: Ein schreibfähiges Rezept hat einen *höheren* Bedarf an einer vollständigen Grenze, keinen geringeren.

- Die Rolle `lead` ist auf der Referenzinstanz gemessen, taucht aber in keiner Upstream-Rollentabelle auf. Ob sie eine Umbenennung von `admin`, eine eigenständige vierte Rolle oder instanzlokale Konfiguration ist, ist ungeklärt — daher die Regel, `mcp_permissions` statt der Rolle zu lesen.
- Ob die `Mcp-Session-Id` bei jedem Aufruf zurückgespiegelt werden muss oder nur innerhalb eines Sitzungsfensters; die Referenzprüfung hat sie durchgehend mitgesendet und den Fall ohne sie nicht getestet.
- Ob `get_mcp_activity` als Selbstprüfungsschritt am Ende eines `-apply`-Rezepts nützt oder nur Rauschen erzeugt.
- Diese Spec hat keinen Mechanismus, um zu erkennen, dass der laufende Server Tools anbietet, die sie nicht führt. Zum Stand der Nachinventur vom 2026-11-05, an einem lokalen Build, stimmen beide überein — alle 67 sind hier aufgeführt —, aber nichts hält sie in Übereinstimmung. Die Drift fiel inzwischen dreimal von Hand auf: drei Tage nachdem sie in der ersten Augustwoche entstand, neun Tage nachdem sie ein zweites Mal entstand, und am 2026-11-05, als vier neue Schreibtools jeden Policy-Block zur Teilmenge gemacht hatten (#80) — jedes Mal beiläufig und nicht durch eine Prüfung. Davon unabhängig: Upstream dokumentiert den Katalog weiterhin als auf rund 30 wachsend, was die Implementierung inzwischen doppelt überholt hat.

## Quelle

- Live-Messung der Referenzinstanz, 2026-08-04: `initialize` (Protokoll `2025-06-18`, `Mcp-Session-Id`, Fähigkeiten nur `tools`), `tools/list` (12 Tools mit vollständigem JSON Schema), `tools/call list_tenants` (Rolle `lead`, `mcp_permissions`, `structuredContent`-Hülle), `GET /mcp` → `405`, unauthentifiziertes `POST` → `401`
- Zuordnung von `tenant`, `dry_run` und `idempotency_key` je Tool, abgeleitet durch Prüfung von `inputSchema.properties` auf diese Schlüssel — nicht aus der Gruppierung in diesem Dokument. Für die 43 Tools vom 2026-08-07 stammt sie aus der `tools/list`-Antwort ohne jeden Aufruf, diese Aussagen betreffen also das deklarierte Schema und nicht beobachtetes Verhalten; für die bis 2026-08-16 hinzugekommenen 13 wurden die Schemata von der Oberfläche gelesen, die eine Goose-Sitzung erhält — also aus derselben Antwort, wie der Client sie darbietet
- Live-Messung der Referenzinstanz, 2026-08-07: `tools/list` (43 Tools) sowie nur lesende `tools/call` für `list_tenants`, `list_pests`, `get_pest` (`Tetranychus urticae`), `list_diseases`, `list_species`, `get_species_info` (`Allium porrum`, `Spathiphyllum wallisii`), `list_plants`, `get_plant_inspections`, `list_phase_definitions`, `list_overwintering_profiles` und `get_sowing_calendar` (einmal unspezifiziert, was abgelehnt wurde, und einmal mit `query`). Kein Schreibtool wurde aufgerufen.
- Live-Messung der Referenzinstanz, 2026-08-16, im Rahmen einer Pflanzenkonfigurations-Prüfung statt einer eigenen Sonde: 56 Tools auf der Sitzungsoberfläche, nur lesende `tools/call` für `list_tenants`, `list_plants`, `get_plant`, `list_plants_at_location`, `get_plant_diagnostics`, `get_plant_phase_status`, `get_plant_phase_history`, `get_species_info`, `get_species_lifecycle`, `get_species_phase_sequence`, `list_phase_sequences`, `list_species`, `list_cultivars`, `list_substrates`, `list_fertilizers`, `list_nutrient_plans`, `get_nutrient_plan`, `get_plant_nutrient_plan`, `calculate_mixing_protocol`, `get_due_care_tasks`, `list_tasks`, `get_harvest_readiness`, `list_planting_runs`, dazu `get_mcp_activity` und `search_plant_knowledge`, die beide wie oben vermerkt fehlschlugen. **Diesmal wurden Schreibtools aufgerufen**, anders als bei den früheren Messungen: `assign_species_phase_sequence` und `transition_plant_phase` waren erfolgreich, `assign_nutrient_plan` scheiterte auf dem Commit-Pfad mit `INTERNAL_ERROR`, während sein `dry_run` durchlief (`nolte/kamerplanter#1145`). Damit ist `dry_run` bei mindestens einem Schreibtool als echter No-op bestätigt — und zugleich als **kein** Beleg dafür, dass der Schreibvorgang selbst gelingt
- Live-Messung einer lokalen Instanz aus `nolte/kamerplanter` @ `5fc20429a`, 2026-11-05 (#80): `initialize`, `tools/list` (67 Tools; 16 tragen `dry_run` und `idempotency_key`, kein Lesetool trägt eines davon; `tenant` bei 15 Schreib- und 37 Lesetools). Die Berechtigungsklasse der vier neuen Schreibtools ist aus dem Upstream-Quelltext gelesen (`McpPermission.WRITE` in `src/backend/app/mcp_server/tools/nutrition.py:279`, `:347`, `substrates.py:143`, `:260`), nicht aus einem Aufruf; keines der vier wurde aufgerufen
- `nolte/kamerplanter` — `docs/en/api/mcp-server.md` (Transport, Authentifizierung, Mandantenfähigkeit, dokumentierte Berechtigungsklassen, Werkzeugzwecke, Audit-Trail), gelesen am 2026-08-04
- `env_keys`-Verhalten von Goose gemessen gegen Goose 1.45.0 durch Mitschnitt der tatsächlich gesendeten Requests; siehe `README.md` §Notes
