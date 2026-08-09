# Bildgestützte Pflanzengesundheitsanalyse

Status: Entwurf
Portfolio-Scope: local

## Kontext

Kamerplanter sammelt Tagebucheinträge, und ein Tagebucheintrag kann Fotos tragen. Das Backend markiert jene, die eine maschinelle Analyse erwarten, und hält sie in einer Warteschlange; auf der Referenzinstanz gemessen warteten zwei Einträge. Der MCP-Server bietet den gesamten Zyklus an — Warteschlange auflisten, Eintrag unter einer Lease beanspruchen, Fotos holen, Ergebnis zurückschreiben — und ein Feld des Submit-Tools heißt `recipe_version`. Der Server ist in der Erwartung gebaut, dass ein Agent wie die in diesem Repository die Analyse übernimmt.

Was der Server nicht liefert, ist die Analyse selbst, und die ist schwieriger, als ein Foto anzusehen. Ein vergilbendes unteres Blatt ist Seneszenz bei einer determinierten Tomate im Fruchtansatz, Stickstoffmangel bei einem Starkzehrer im Vegetativwachstum und Überwässerung bei einer Sukkulente in der Winterruhe. Das Foto ist in allen drei Fällen dasselbe. **Das Bild ist der Beleg; die Pflanzeninstanz ist das, wogegen der Beleg gelesen wird.** Eine Analyse, die die Instanz überspringt, erzeugt Text, der botanisch klingt und nichts bedeutet.

Diese Spec beschreibt diesen Prozess: welcher Kontext in welcher Reihenfolge erhoben wird, wie die Art die Lesart verschiebt, wie Unsicherheit ausgedrückt wird und wie eine Beanspruchung stets wieder freigegeben wird. Sie ist die Prozessebene. Die Rezept-Mechanik — wo Extensions deklariert werden, was der Provider mitbringt — steht im [Goose-Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md); was der Server anbietet, in der [Spec zum Kamerplanter-MCP-Server](../../mcp/kamerplanter-mcp-server/de.md). Beides wird hier nicht wiederholt.

Alles als *gemessen* Gekennzeichnete wurde am 2026-08-05 von der Referenzinstanz gelesen — über den Live-MCP-Endpunkt und über Headless-Goose-Läufe.

Leserschaft: alle, die das Analyse-Rezept in diesem Repository schreiben, sowie alle, die beurteilen, ob eine eingereichte Analyse durch das gedeckt war, was ihr vorlag.

## Ziele

- Ein Befund ist an eine Pflanzeninstanz, ihre Art und ihre aktuelle Phase gebunden — nie an ein generisches Pflanzenfoto
- Artunterschiede gelangen aus den Backend-Stammdaten in die Analyse, sodass die Spec kein botanisches Wissen trägt, das gegen den Katalog driftet
- Jede Beanspruchung, die ein Lauf öffnet, wird von demselben Lauf geschlossen, auch wenn die Analyse scheitert
- Unsicherheit wird beziffert und benannt, statt zu einer Diagnose aufgerundet zu werden
- Ein Foto, das die Frage nicht beantworten kann, führt zu einer benannten Lücke, nicht zu einem erfundenen Befund
- Eine prüfende Person kann aus dem eingereichten Ergebnis rekonstruieren, welches Foto und welches Kontextfeld jeden Befund erzeugt hat

## Nicht-Ziele

- Bildaufnahme, Upload und Erzeugung der Renditions — das gehört dem Backend; der Prozess verbraucht, was `get_diary_entry_photos` liefert
- Bestimmung der Art aus dem Bild; die Art ist eine Tatsache der Instanz, und ein Foto, das ihr widerspricht, ist ein Befund, keine Neubestimmung
- Auslösen von Behandlungen, Bestätigen von Pflegeaufgaben oder jede Zustandsänderung jenseits des Zurückschreibens des Analyseergebnisses an den eigenen Eintrag
- Der In-App-KI-Assistent von Kamerplanter, eine eigene Oberfläche mit eigenem Kontext
- Rezept-Mechanik sowie Transport, Authentifizierung und Mandantenregeln des MCP-Servers — anderswo spezifiziert, hier referenziert statt wiederholt
- Vorgabe von Prompt-Formulierungen; diese Spec legt die Invarianten fest, die ein Prompt wahren muss

## Gemessene Ausgangslage

Der Katalog ist weit über das hinausgewachsen, was die MCP-Server-Spec festhält. Am 2026-08-05 gemessen lieferte `tools/list` **42 Tools**, nicht die dort als vollständige Oberfläche dokumentierten 12. Der Analysezyklus stützt sich auf fünf der neueren, der Prozess ist also heute verfügbar:

| Tool | Erforderliche Argumente | Anmerkungen (gemessen) |
|------|-------------------------|------------------------|
| `list_pending_diary_analyses` | — | `limit` Vorgabe 20, max. 100; `include_stale` Vorgabe `true` liefert auch Einträge mit abgelaufener Lease |
| `claim_diary_analysis` | `entry_key`, `worker_id` | `lease_seconds` Vorgabe 900, max. 3600; Lease plus Compare-and-Set |
| `get_diary_entry` | `entry_key` | Vollständiger Pflanzenkontext inline, **ohne** Bilddaten |
| `get_diary_entry_photos` | `entry_key` | Fotos als MCP-Bild-Content-Blöcke (WebP); `size` ist 512 oder 1280, alles andere ist ein Validierungsfehler |
| `submit_diary_analysis` | `entry_key`, `lease_token`, `status` | `status` ist `completed` oder `failed`; beendet die Beanspruchung |

**Bild-Content-Blöcke erreichen das Modell und sind lesbar.** Durchgängig gemessen: Ein Headless-Lauf rief `get_diary_entry_photos` mit `size: 512` auf und beschrieb das Abgebildete. Der Prozess scheitert nicht an einer Transportgrenze.

Dieselbe Messung ist zugleich die schärfste verfügbare Erinnerung daran, warum Verweigerung zählt. Das Foto in der Warteschlange zeigte eine Kunststoffklemme und eine Fernbedienung — überhaupt keine Pflanze. Der Fall „das Bild beantwortet die Frage nicht" ist keine Hypothese, die man der Vollständigkeit halber behandelt; er war der erste real vorgefundene Eintrag.

`get_diary_entry` liefert den Instanzkontext bereits inline — `plant_key`, `species_key`, `species_name`, `cultivar_name`, `current_phase`, `phase_started_at`, `planted_on`, `location_name` — neben `text`, `tags`, `measurements` und `photo_refs` des Eintrags. Ein Aufruf klärt, wovon das Foto ein Foto ist.

## Der Prozess

Ein Lauf bearbeitet genau einen Tagebucheintrag. Die Stufen sind so geordnet, dass alles Billige und Verweigerbare vor der Beanspruchung geschieht und nichts nach ihr enden kann, ohne sie freizugeben.

### Stufe 0 — Vorbedingungen

Den Garten auflösen und `mcp_permissions` aus `list_tenants` lesen. Der Zyklus braucht `mcp.write` für `claim_diary_analysis` und `submit_diary_analysis`. Ein Schlüssel mit nur `mcp.read` muss hier abbrechen und das benennen — einen Eintrag zu beanspruchen, den er nicht einreichen kann, würde diesen bis zu einer Stunde unter einer Lease parken.

### Stufe 1 — Auswahl

Entweder den als Rezeptparameter übergebenen `entry_key` nehmen oder `list_pending_diary_analyses` aufrufen und den nach `requested_at` ältesten Eintrag wählen. Die Auflistung führt `photo_count`; ein Eintrag mit `photo_count: 0` ist kein Kandidat für eine Bildanalyse und wird als übersprungen gemeldet statt beansprucht.

### Stufe 2 — Beanspruchung

`claim_diary_analysis` aufrufen mit einer `worker_id`, die dieses Rezept und diesen Lauf identifiziert, und einem `lease_seconds`, das die erwartete Laufzeit übersteigt, nicht das Maximum. Das zurückgegebene `lease_token` festhalten; ohne es lässt sich das Ergebnis nicht einreichen. Ab hier führt jeder Ausgangspfad über Stufe 6.

### Stufe 3 — Instanzkontext

`get_diary_entry` für den Eintrag aufrufen, dann zusammentragen, was die Lesart braucht:

- `get_species_info` zum `species_key` — die Artbasis
- `list_phase_definitions`, um `current_phase` in seine Definition aufzulösen, die `stress_tolerance`, `watering_interval_days` und `typical_duration_days` trägt
- `get_cultivar`, wenn `cultivar_key` gesetzt ist — Merkmale und `days_to_maturity` verengen die Arterwartung
- `get_plant_care_log` — wann die Pflanze zuletzt gegossen oder gedüngt wurde, was entscheidet, ob eine Trockenheits- oder Mangellesart plausibel ist
- `get_plant_inspections` — die IPM-Historie; ein an dieser Pflanze bereits erfasster Schädling erhöht die Vorannahme für denselben Schädling, und eine Pflanze ohne Inspektionen hat keine solche Vorannahme

`text`, `tags` und `measurements` des Eintrags gehören zum Kontext und werden als Behauptung der beobachtenden Person gelesen, nicht als gesicherte Wahrheit. Wo Text und Bild auseinandergehen, wird beides berichtet.

### Stufe 4 — Bilder

Die Fotos mit `get_diary_entry_photos` holen. `size: 1280` vorziehen, wenn die Frage feinkörnig ist — Blattunterseiten, Chlorosemuster, Insektenkörper — und `512`, wenn es um Wuchsform oder Gesamtvitalität geht. Festhalten, welche `photo_ids` die Analyse tatsächlich getragen haben; höchstens fünf dürfen gemeldet werden.

### Stufe 5 — Lesart

Erst beschreiben, was sichtbar ist, dann deuten, und beides im Ergebnis trennbar halten. Anschließend jede Beobachtung gegen die Erwartung lesen, die die Instanz setzt, gemäß den Tabellen unten. Ein Befund ist der *Abstand* zwischen beidem, nicht die Beobachtung allein.

Jeder Befund trägt eine `confidence` zwischen 0.0 und 1.0 und eine `rationale`, die den Beleg benennt: welches Foto, welches sichtbare Merkmal und welches Kontextfeld daraus einen Befund statt Normalität gemacht hat. Höchstens zehn Befunde, höchstens zehn empfohlene Maßnahmen.

### Stufe 6 — Einreichung

Immer. Bei Erfolg `status: "completed"` mit einer `summary` aus ein bis drei Sätzen (höchstens 2000 Zeichen), den Befunden, den empfohlenen Maßnahmen, den analysierten Foto-Ids, dem Modell und der `recipe_version`. Wenn die Analyse nicht möglich ist — kein lesbares Foto, keine abgebildete Pflanze, fehlender Kontext, ein fehlgeschlagenes Tool — `status: "failed"` mit einem `error`, der die Ursache benennt. Eine gescheiterte Einreichung ist ein korrektes Ergebnis; eine liegengelassene Lease nicht.

## Was die Art verändert

Die Artbasis stammt aus `get_species_info`. Jedes Feld verschiebt, was als normal gilt, sodass dasselbe sichtbare Merkmal bei einer anderen Art einen anderen Befund ergibt. Die Spec benennt die Zuordnung; sie benennt nicht die Pflanzen.

| Feld (gemessen) | Verschiebt die Lesart von |
|-----------------|---------------------------|
| `plant_category` | Welches Schädlings- und Krankheitsspektrum überhaupt plausibel ist und welches Licht und welche Luftfeuchte unterstellt werden — eine Zimmerpflanze und ein Freilandgemüse teilen kaum einen Fehlermodus |
| `growth_habit` | Ob hängender, kriechender oder ausladender Wuchs die Pflanze bei ihrer Arbeit zeigt oder ein Vergeilungssymptom ist; bei einem `groundcover` das Erstere |
| `root_type` | Wie schnell Trockenstress auftritt und wie er aussieht; ein faseriges Wurzelsystem welkt nach anderer Uhr als eine Pfahlwurzel |
| `nutrient_demand_level` | Ob eine Mangellesart unter der erfassten Düngehistorie plausibel ist; ein `heavy_feeder` und eine Magerstandort-Art ergeben aus demselben blassen Blatt gegenteilige Vorannahmen |
| `frost_sensitivity`, `hardiness_zones` | Ob Kälteschaden als Erklärung zum Datum des Eintrags und zum Standort der Pflanze überhaupt zulässig ist |
| `bloom_months`, `harvest_months` | Ob Blüten oder Früchte im Foto im Zeitplan liegen, verfrüht sind oder fehlen, obwohl sie fällig waren — gemessen an `created_at`, nicht an heute |
| `allows_harvest`, `harvest_pattern` | Ob Reife überhaupt eine sinnvolle Frage ist und ob eine teilweise abgeerntete Pflanze abgeerntet aussehen darf |
| `base_temp_gdd` | Wie viel Zuwachs seit `planted_on` zu erwarten ist, was „kümmerlich" erst zu einer Behauptung statt zu einem Eindruck macht |
| `cultivars[].traits`, `cultivars[].days_to_maturity` | Die auf die Sorte verengte Arterwartung, wenn `cultivar_key` gesetzt ist |
| `toxicity` | Nie die Gesundheitslesart — gehört aber in eine empfohlene Maßnahme, die jemanden die Pflanze anfassen oder essen ließe |

`compatible_companions` beschreibt Pflanzentscheidungen, nicht Pflanzengesundheit, und geht in keinen Befund ein.

Zwei Regeln halten das ehrlich. Ein fehlendes oder leeres Artfeld **verengt** die Analyse — die zugehörige Frage wird nicht gestellt und die Lücke benannt —, statt durch eine allgemeine Annahme über Pflanzen ersetzt zu werden. Und die Art wird nie aus dem Bild abgeleitet: Wo das Foto eine andere Pflanze zu zeigen scheint als `species_name`, ist genau diese Abweichung der Befund, mit der Konfidenz, die das Bild trägt.

## Was die Instanz verändert

Artdaten allein gäben für jede Erdbeere der Welt dieselbe Antwort. Die Instanz ist das, was die Analyse zu dieser Pflanze macht:

| Quelle | Verschiebt die Lesart von |
|--------|---------------------------|
| `current_phase` samt Definition | Was die Pflanze jetzt tun sollte; `stress_tolerance` setzt zudem, wie schwer ein Symptom in dieser Phase wiegt |
| `phase_started_at` gegen `typical_duration_days` | Ob die Pflanze überfällig ist, ihre Phase zu verlassen, was „blüht noch nicht" entweder als normal oder als Befund rahmt |
| `planted_on` | Das Alter der Pflanze und mit `base_temp_gdd` den bis jetzt erwarteten Zuwachs |
| `watering_interval_days` aus der Phase, gegen `get_plant_care_log` | Ob die Pflanze zum Aufnahmezeitpunkt plausibel unter- oder überwässert war |
| `get_plant_inspections` | Bisheriger Schädlings- und Krankheitsdruck an diesem Individuum — ein Wiederauftreten und ein Erstauftreten sind verschiedene Befunde |
| `measurements` und `tags` des Eintrags | Von der beobachtenden Person erfasste Werte, die mit dem Bild abzugleichen sind, statt ihm vorgezogen zu werden |
| `location_name` | Wo sie steht, was die verfügbaren Expositionserklärungen eingrenzt |

Jede zeitliche Beurteilung erfolgt gegen `created_at` des Eintrags, nie gegen den Zeitpunkt des Laufs. Ein Foto, das drei Wochen nach der Aufnahme analysiert wird, ist ein Beleg über die Pflanze vor drei Wochen.

## Konfidenz und Verweigerung

Die `confidence` eines Befunds betrifft den Beleg, nicht die Sprachgewandtheit des Modells. Drei Fälle dürfen nicht zusammenfallen:

- **Ein Befund** — das Bild zeigt etwas, und der Instanzkontext macht daraus eine Abweichung vom Normalen. Die Konfidenz spiegelt, wie eindeutig das sichtbare Merkmal ist.
- **Eine Lücke** — die Frage ist berechtigt, aber das Bild kann sie nicht beantworten (die Blattunterseiten sind nicht sichtbar, das Foto ist unscharf, der Ausschnitt lässt das Substrat weg). Wird als Lücke gemeldet, samt dem, was sie auflösen würde, nie als Befund niedriger Konfidenz.
- **Eine Verweigerung** — das Bild zeigt nicht die Pflanze oder gar keine Pflanze. `status: "failed"` mit einem `error`, der das sagt.

Ein Lauf, der nichts Auffälliges findet, reicht `completed` mit leerer Befundliste ein und einer Zusammenfassung, die sagt, dass die Pflanze für ihre Art und Phase normal wirkt. Gesund ist ein Ergebnis.

## Anforderungen

- **MUSS [MUST]** `mcp_permissions` aus `list_tenants` lesen und `mcp.write` bestätigen, bevor beansprucht wird, da eine Beanspruchung, die nicht eingereicht werden kann, den Eintrag bis zu einer Stunde unter einer Lease parkt
- **MUSS [MUST]** einen Eintrag mit `claim_diary_analysis` beanspruchen, bevor dessen Fotos gelesen werden, und **MUSS [MUST]** das zurückgegebene `lease_token` bis zur Einreichung mitführen
- **MUSS [MUST]** `submit_diary_analysis` auf jedem Pfad aufrufen, der einen Eintrag beansprucht hat, mit `status: "failed"` und gefülltem `error`, wenn die Analyse nicht möglich war
- **MUSS [MUST]** `lease_seconds` aus der erwarteten Laufzeit ableiten statt aus dem Maximum 3600, damit ein abgestürzter Lauf den Eintrag früher freigibt
- **MUSS [MUST]** eine `worker_id` übergeben, die Rezept und Lauf identifiziert, und beim Einreichen `recipe_version` und `model` füllen, damit ein Ergebnis auf seinen Erzeuger zurückführbar bleibt
- **MUSS [MUST]** die Pflanzeninstanz, ihre Art und ihre aktuelle Phase auflösen, bevor ein Bild gedeutet wird, und **DARF NICHT [MUST NOT]** einen Befund einreichen, der nicht gegen diesen Kontext gelesen wurde
- **MUSS [MUST]** artabhängige Erwartungen aus den Feldern von `get_species_info`, `get_cultivar` und `list_phase_definitions` ableiten und **DARF NICHT [MUST NOT]** artbezogene botanische Regeln im Rezept-Prompt kodieren, was den Katalog verdoppeln und gegen ihn driften würde
- **MUSS [MUST]** jede zeitliche Beurteilung gegen `created_at` des Eintrags vornehmen, nie gegen den Zeitpunkt des Laufs
- **MUSS [MUST]** jedem Befund eine `rationale` geben, die das Foto und das sichtbare Merkmal benennt, auf dem er beruht, sowie das Kontextfeld, das ihn zur Abweichung vom Normalen gemacht hat
- **MUSS [MUST]** eine Abweichung zwischen abgebildeter Pflanze und `species_name` als Befund melden und **DARF NICHT [MUST NOT]** die Art aus dem Bild neu bestimmen oder stillschweigend die scheinbar gezeigte Pflanze analysieren
- **DARF NICHT [MUST NOT]** ein anderes zustandsänderndes Tool aufrufen als `claim_diary_analysis` und `submit_diary_analysis` für den selbst beanspruchten Eintrag; die verbotenen im `prompt` zu benennen, verlangt das Rezept-Projektmuster
- **DARF NICHT [MUST NOT]** eine unbeantwortbare Frage in einen Befund niedriger Konfidenz verwandeln; eine Lücke wird als Lücke gemeldet
- **MUSS [MUST]** das Dateinamens-Suffix `-apply` tragen und die Schreibwirkung in seiner `description` benennen, da der Prozess schreibt
- **SOLLTE [SHOULD]** genau einen Eintrag je Lauf bearbeiten, damit ein Fehler zuordenbar bleibt und die Lease kurz
- **SOLLTE [SHOULD]** einen Eintrag mit `photo_count: 0` mit benanntem Grund überspringen, statt ihn zu beanspruchen
- **SOLLTE [SHOULD]** beim Einreichen `dry_run: true` setzen, wenn der Lauf eine Probe ist, sowie einen aus Eintrag und Lauf abgeleiteten `idempotency_key`, damit ein Wiederholungslauf nicht doppelt schreibt
- **SOLLTE [SHOULD]** `size: 1280` anfordern, wenn der Befund an feinem Detail hängt, und `512`, wenn er an Wuchsform oder Vitalität hängt, und festhalten, welche Foto-Ids das Ergebnis getragen haben
- **SOLLTE [SHOULD]** die Analyse verengen, wenn ein Artfeld fehlt, und die nicht stellbare Frage benennen, statt eine allgemeine Annahme einzusetzen
- **SOLLTE [SHOULD]** `completed` mit leerer Befundliste einreichen, wenn die Pflanze normal wirkt, statt einen Grenzbefund zu fabrizieren
- **KANN [MAY]** `get_plant_nutrient_plan`, `get_pest`, `get_disease` oder `get_treatment` lesen, um einen konkreten Befund zu untermauern, und **KANN [MAY]** die Karenzzeit einer Behandlung in einer empfohlenen Maßnahme nennen, wenn die Pflanze `allows_harvest` trägt
- **DARF NICHT [MUST NOT]** die Richtung eines vermuteten Nährstoffproblems — Unter- gegen Überversorgung — aus dem Bild angeben, da beide visuell ununterscheidbar sind; diese Bestimmung gehört zur [Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md) und **SOLLTE [SHOULD]** an sie übergeben statt geraten werden
- **KANN [MAY]** `list_pending_diary_analyses` mit `include_stale: true` abfragen, um einen Eintrag mit abgelaufener Lease aufzunehmen

## Akzeptanzkriterien

- [ ] Ein Lauf, der einen Eintrag beansprucht, reicht auf jedem Ausgangspfad ein Ergebnis ein, auch bei Tool-Fehlern und unbrauchbaren Bildern
- [ ] Ein Lauf ohne `mcp.write` bricht vor der Beanspruchung ab und benennt die fehlende Berechtigung
- [ ] Die `rationale` jedes eingereichten Befunds benennt eine Foto-Id, ein sichtbares Merkmal und ein Kontextfeld
- [ ] Kein eingereichter Befund beruht auf Artwissen, das in der Backend-Antwort fehlt
- [ ] Ein Eintrag, dessen Foto keine Pflanze zeigt, wird als `failed` mit erklärendem `error` eingereicht, nicht als Befund
- [ ] Eine gesunde Pflanze ergibt `completed` mit leerer Befundliste und einer Zusammenfassung, die das sagt
- [ ] Zeitaussagen in einer Zusammenfassung beziehen sich auf `created_at` des Eintrags, nicht auf das Laufdatum
- [ ] Die Rezeptdatei trägt ein `-apply`-Suffix und benennt ihre Schreibwirkung in `description`
- [ ] Der `prompt` des Rezepts benennt jedes verbotene zustandsändernde Tool
- [ ] `lease_seconds` im Rezept liegt unter dem Maximum 3600 und ist durch die erwartete Laufzeit begründet
- [ ] Befunde, empfohlene Maßnahmen und analysierte Foto-Ids bleiben in den Servergrenzen von 10, 10 und 5

## Offene Fragen

- Ob die Lesart des Modells auf einer 512-Pixel-Rendition für die hier maßgeblichen Befunde deutlich schlechter ist als auf einer mit 1280. Beide Größen stehen zur Verfügung; erprobt ist nur 512, und nur an einem Foto ohne Pflanze.
- Ob mehrere Fotos eines Eintrags gemeinsam in einem Durchgang oder getrennt und danach abgeglichen analysiert werden sollten. Das Submit-Schema nimmt bis zu fünf analysierte Foto-Ids an, ohne ihr Verhältnis zu benennen.
- Ob eine Neuanalyse das vorherige Ergebnis lesen sollte, bevor sie es überschreibt. Die Nutzlast selbst ist inzwischen gemessen (2026-08-05): Eine als `failed` eingereichte Analyse lässt `analysis` auf `null` und legt den Fehlertext wörtlich in `analysis_error`, während eine als `completed` eingereichte ein Objekt mit `summary`, `findings`, `recommended_actions`, `analyzed_photo_ids`, `model`, `recipe_version` speichert — dazu zwei Felder, die der Server selbst ergänzt: `analyzed_at` und ein `disclaimer`, der das Ergebnis als Hypothese eines Sprachmodells ausweist. Ein Rezept **DARF** deshalb **NICHT** einen eigenen Disclaimer-Text verfassen; diese Fläche gehört dem Server.
- Ob `confidence`-Werte eines LLM zwischen Läufen hinreichend vergleichbar sind, um einen Schwellenwert in der Oberfläche zu tragen, oder ob sie nur innerhalb einer Analyse ordinal sind.
- Wie der Prozess mit einem Eintrag umgehen soll, dessen `text` eine Diagnose behauptet, der das Bild widerspricht — derzeit „beides melden", was die falsche Vorgabe sein könnte, wenn beobachtende Personen sich regelmäßig selbst diagnostizieren.
- Ob die Zuwachserwartung aus `base_temp_gdd` ohne lokale Temperaturhistorie überhaupt berechenbar ist und ob Home-Assistant-Sensordaten sie liefern sollten. Nicht versucht; es würde den Prozess von einem zweiten Backend abhängig machen.

## Quelle

- Gemessen gegen die Kamerplanter-Referenzinstanz am 2026-08-05 über `POST /api/v1/mcp`: `tools/list` lieferte 42 Tools mit vollständigen Eingabeschemata; `list_tenants`, `list_pending_diary_analyses`, `get_diary_entry`, `get_plant`, `get_plant_inspections`, `get_species_info` und `list_phase_definitions` wurden nur lesend für ihre Nutzlastform aufgerufen. Kein Schreib-Tool wurde aufgerufen.
- Lesbarkeit der Bilder gemessen mit einem Headless-Lauf `goose run --no-session`, der `get_diary_entry_photos` mit `size: 512` an einem wartenden Eintrag aufrief, unter Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`
- Feldsemantik von `claim_diary_analysis` und `submit_diary_analysis` aus deren Live-`inputSchema` gelesen, einschließlich der Definition `DiaryFindingInput` und ihres bewussten Verzichts auf Längen- und Wertebereichsgrenzen zugunsten des Domänenmodells (`REQ-050 §5`)
- Rezept-Mechanik: [Goose-Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md)
- Server-Vertrag: [Spec zum Kamerplanter-MCP-Server](../../mcp/kamerplanter-mcp-server/de.md)
