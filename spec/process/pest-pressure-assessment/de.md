# Beurteilung des Schädlingsdrucks

Status: Entwurf
Portfolio-Scope: local

## Kontext

Einen Schädling zu benennen ist nicht dasselbe, wie ihn zu diagnostizieren. Ein Katalog mit 34 Schädlingen liefert zu einem beschriebenen Schadbild immer den nächstliegenden Treffer, und der nächstliegende Treffer stimmt oft genug, dass ein falscher plausibel klingt. Der Preis des falschen Namens ist nicht akademisch: Er wählt eine Behandlung aus. Eine Raubmilbe gegen Thripse zu empfehlen, die sich als Blattläuse entpuppen, verschenkt eine Nützlingsfreilassung; ein Breitband-Insektizid neben einem Nützling zu empfehlen, neutralisiert den Nützling; überhaupt etwas innerhalb der Karenzzeit einer kurz vor der Ernte stehenden Kultur zu empfehlen, ist ein Lebensmittelsicherheits-Fehler, kein gärtnerischer.

**Was eine echte Bestimmung von einer plausiblen trennt, ist selten das Schadbild. Es ist die Frage, ob die Biologie des Organismus zur Pflanze, zum Medium, zur Jahreszeit und zum Raum passt, in dem er angeblich lebt.** Diese Prüfung ist mechanisch, wo der Datensatz sie trägt — eine Milbe mit `pest_type: insect` ist falsch, wie gut das Schadbild auch passt — und unmöglich, wo er schweigt.

Diese Spezifikation existiert, weil er an bestimmten, benennbaren Stellen schweigt. Gemessen trägt `get_pest` ein Temperaturoptimum und eine Generationsdauer, aber **keine Feuchtespanne, keine Wirtspflanzenliste, keine Präventions- oder Monitoring-Hinweise und keine Schwere-Einstufung**. Die wertvollste Einzelprüfung des Quellverfahrens, das dieser Prozess erbt — dass Spinnmilben durch *trockene* Luft gefördert werden, Luftfeuchte anzuheben also eine Maßnahme ist und keine Verschlimmerung —, lässt sich am Datensatz überhaupt nicht durchführen. `get_disease` trägt dagegen `environmental_triggers`, dieselbe Argumentation gilt also für Krankheiten und nicht für Schädlinge. Ein Verfahren, das nicht weiß, wo seine Daten enden, füllt diese Lücken aus dem eigenen Modellwissen und trägt das Ergebnis im selben Tonfall vor wie eine belegte Tatsache.

Es ist das Gegenstück zur [Pflanzengesundheits-Bildanalyse](../plant-health-image-analysis/de.md), kein Teil davon, und es komponiert mit ihr genauso wie die [Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md). Dort ist ein Schädlingsbefund einer von mehreren möglichen — neben Mangel, Krankheit und Trockenheit —, und das Bild ist der Hauptbeleg. Hier ist die Schädlingsfrage der ganze Gegenstand, Inspektionshistorie und Katalog sind die Hauptbelege, und das Bild bestätigt oder widerlegt.

Alles als *gemessen* Gekennzeichnete wurde am 2026-08-07 von der Referenzinstanz gelesen.

Leserschaft: Autorinnen und Autoren schädlingsbezogener Rezepte in diesem Repository sowie alle, die eine von ihnen vorgeschlagene Maßnahme prüfen, bevor danach gehandelt wird.

## Ziele

- Eine Bestimmung wird nur angenommen, wenn die belegte Biologie des Organismus zur Pflanze und ihrer Situation passt — nie allein aufgrund einer Schadbild-Ähnlichkeit
- Jede Aussage benennt, ob sie aus dem Datensatz stammt oder aus allgemeinem Wissen über das Taxon, weil beides nicht gleich überprüfbar ist
- Eine Maßnahme wird nur vorgeschlagen, wenn die Bestimmung genug Belege trägt, um eine auszuwählen; die Verweigerung benennt, was sie auflösen würde
- Die Unterscheidung zwischen saugendem, raspelndem und fressendem Schaden wird als Falsifikationstest angewandt, weil sie mehr Fehlbestimmungen widerlegt als jede andere Einzelprüfung
- Die Karenzzeit jeder genannten Behandlung wird gegen die Erntesituation der Pflanze gestellt
- Wo der Datensatz nicht antworten kann — Feuchte-Ökologie, Wirtsspektrum, Nachweismethode —, sagt das Verfahren das, statt trotzdem zu antworten

## Nicht-Ziele

- Eine Behandlung anwenden, eine Pflegeaufgabe bestätigen oder eine Inspektion erfassen; dieses Verfahren liest und beurteilt
- Eine Laborbestimmung oder ein Mikroskop ersetzen; es schließt aus dem Datensatz, den Kamerplanter hält, plus dem Sichtbaren
- Den Schädlings-, Krankheits- oder Behandlungskatalog verfassen — der gehört dem Backend, und seine Korrektur gehört nach `nolte/kamerplanter`
- Nährstoffstörungen oder Trockenheit diagnostizieren, außer um sie als konkurrierende Erklärung auszuschließen — das ist die [Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md)
- Bilder lesen; ein Verdacht kommt aus der [Pflanzengesundheits-Bildanalyse](../plant-health-image-analysis/de.md) oder aus einem Tagebucheintrag
- Rezeptmechanik sowie MCP-Transport, -Authentifizierung und -Mandantenfähigkeit — spezifiziert im [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) und in der [Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md)

## Gemessene Ausgangslage

### Die Historie der Pflanze selbst

`get_plant_inspections` liefert die IPM-Inspektionshistorie einer Pflanze — Druckniveau, Befunde, Symptome. Gemessen an einer nie inspizierten Pflanze antwortet es mit `count: 0`, einem leeren `items`-Array und einer Klartext-Zusammenfassung, die genau das sagt. **Eine leere Historie ist der Regelfall**, kein Fehler und kein Beleg für Abwesenheit; sie besagt nur, dass niemand nachgesehen oder niemand das Nachsehen erfasst hat.

### Der Katalog, und wo er endet

Gemessen meldet `list_pests` 34 Schädlinge und `list_diseases` 34 Krankheiten. `get_pest` lieferte zu `Tetranychus urticae` genau diese Felder:

| Vorhanden | Gemessener Wert |
|-----------|-----------------|
| `pest_key`, `scientific_name`, `common_name`, `common_name_de` | `8974`, `Tetranychus urticae`, `Spider Mites`, `Spinnmilben` |
| `pest_type` | `arachnid` |
| `damage_symptoms`, `detection_symptom_hint` | Freitext (deutsch) zu Sprenkelung, Gespinsten, Bronzefärbung |
| `lifecycle_days` | `21` |
| `optimal_temp_min`, `optimal_temp_max` | `25.0`, `30.0` |
| `description` | `null` |
| `treatments[]` | `treatment_key`, `name`, `treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`, `dosage_per_liter`, `protective_equipment[]` |
| `beneficials[]` | `common_name`, `scientific_name`, `preys_on[]`, `description` |

**Abwesend und tragend für die geerbten Prüfungen:** `optimal_humidity_min`/`max`, `host_plants`, `prevention_tips`, `monitoring_hints`, `affected_plant_parts`, jede Einstufung von Schwere oder Erkennungsschwierigkeit, jeder GBIF-Taxon-Schlüssel. Ihr Fehlen ist keine still zu schließende Lücke, sondern die Grenze dessen, was eine Beurteilung als belegt behaupten kann.

`get_disease` ist die besser ausgestattete Hälfte. Gemessen trägt es `pathogen_type`, `incubation_period_days`, `affected_plant_parts[]` und **`environmental_triggers[]`** mit Werten wie `low_humidity`, `high_humidity`, `warm_temperature`, `cool_temperature`, `poor_air_circulation`, `condensation`, `drought_stress`. `Erysiphe spp.` wird durch `low_humidity` ausgelöst, `Botrytis cinerea` durch `high_humidity` — genau die Feuchteachse, die auf der Schädlingsseite fehlt.

### Die Situation

Der Pflanzenkontext wird im Sammelschritt hergestellt, nicht hier: `get_plant`, `get_species_info`, `list_phase_definitions`, `get_plant_care_log`. Drei seiner Felder entscheiden über die Schädlings-Plausibilität und werden deshalb hier genannt: `plant_category` (gemessen `tropical_foliage` an einer Zimmerpflanze) begrenzt, welche Organismen überhaupt möglich sind; `growth_habit` und `root_type` entscheiden, ob Schaden ober- oder unterirdisch auftritt; `allows_harvest` entscheidet, ob eine Karenzzeit greift.

Der Aufstellungsraum ist kein erfasstes Feld. Er wird aus dem Standorttyp sowie aus `frost_sensitivity` und `hardiness_zones` der Art erschlossen — und dieser Schluss ist selbst eine Behauptung, die als solche zu benennen ist.

## Die Belegleiter

Jede Aussage wird danach eingestuft, worauf sie ruht. Eine niedrigere Stufe bestätigt oder widerlegt eine höhere; sie hebt sie nie auf. Die Stufe wandert mit der Aussage in die Ausgabe.

| Stufe | Beleg | Gewicht |
|-------|-------|---------|
| 1 | Eine erfasste Inspektion, die den Organismus benennt, mit Druckniveau und Befunden | Belegt die Anwesenheit für sich allein |
| 2 | Katalogfelder — `pest_type`, `lifecycle_days`, `optimal_temp_*`, `damage_symptoms` oder die `environmental_triggers` einer Krankheit | Bestätigt oder falsifiziert einen Kandidaten; belegt keine Anwesenheit |
| 3 | Situationspassung — `plant_category` der Art, Phase, Jahreszeit, Pflegehistorie, Aufstellungsraum | Engt die Kandidatenmenge ein, wählt nie aus ihr aus |
| 4 | Sichtbare Symptome auf einem Foto | Lokalisiert und staffelt; belegt Anwesenheit nur für einen als solchen sichtbaren Organismus, nie für einen aus dem Schaden erschlossenen |
| 5 | Allgemeines Wissen über das Taxon außerhalb des Datensatzes — Wirtsspektrum, Feuchte-Ökologie, Nachweismethode, Gegenspieler jenseits von `beneficials[]` | Nur Denkhilfe. **Immer als nicht belegt gekennzeichnet** |

**Eine Behandlung wird nur vorgeschlagen, wenn die Bestimmung auf Stufe 1 ruht oder auf Stufe 4 plus einer unwidersprochenen Stufe 2.** Darunter ist die Beobachtung das Ergebnis, die es auflösen würde — und das ist meist eine benannte Nachweismethode, kein weiteres Foto.

## Die Falsifikationstests

In dieser Reihenfolge anzuwenden. Jeder kann einen Kandidaten nur verwerfen, nie bestätigen. Ein Kandidat, der alle vier übersteht, ist *nicht widerlegt* — eine schwächere Aussage als *bestimmt*, und die Ausgabe darf beides nicht verwischen.

### 1. Ernährungsweise gegen Schadbild

Der schärfste Test und derjenige, der die selbstsichersten Fehler abfängt:

| Ernährungsweise | Organismen | Signatur | Ausgeschlossen |
|-----------------|------------|----------|----------------|
| Phloemsauger mit Honigtau | Blattläuse, Weiße Fliege, Schild- und Schmierläuse | klebriger Honigtau, Rußtau, gekräuselte Triebspitzen, sichtbare Kolonien | — |
| Zellsauger ohne Honigtau | Spinnmilben, Thripse | Sprenkelung, Silberglanz, Bronzefärbung, Gespinste (Milben), schwarze Kotpünktchen (Thripse) | **Honigtau. Ein Datensatz, der Milben oder Thripse mit Honigtau verbindet, ist falsch** |
| Fraßschädlinge | Raupen, Erdflöhe, Käfer, Schnecken | Loch- und Buchtenfraß, Kot, Schleimspuren | Saugschaden jeder Art |
| Wurzel und Substrat | Trauermückenlarven, Nematoden | Welke, Wurzelfraß; oberirdisch unspezifisch | Eine spezifische oberirdische Signatur |

### 2. Taxon gegen `pest_type`

Milben und Spinnen sind `arachnid`, Insekten `insect`, Nacktschnecken und Schnecken `gastropod`, Fadenwürmer `nematode`, Wirbeltiere `mammal`. Eine als `insect` erfasste Spinnmilbe ist ein Katalogfehler und ein eigenständiger Befund — melden, nicht stillschweigend korrigieren, und die Bestimmung nicht davon abhängig machen.

Ein `scientific_name` auf Familien- oder Überfamilienrang (`Aphididae`, `Sciaridae`, `Coccoidea`) ist Absicht, kein Fehler, solange `common_name` und `pest_type` zum Rang konsistent bleiben.

### 3. Entwicklung gegen das erfasste Temperaturfenster

`lifecycle_days` ist eine Generationsdauer beim erfassten Optimum, und beide müssen zueinander und zum Zeitverlauf der Beobachtung passen. Ein Befall, der binnen einer Woche eskaliert ist, verträgt sich mit keinem Kandidaten, dessen Generation einen Monat braucht — bei keiner Temperatur. Dieser Test löst Größenordnungen auf; für Rechnungen auf einem Einzelwert trägt er nicht.

Liegt die tatsächliche Standorttemperatur weit außerhalb von `optimal_temp_min`–`optimal_temp_max`, verläuft die Entwicklung langsamer als der Datensatz nahelegt, und eine schnelle Eskalation macht den Kandidaten unwahrscheinlicher statt wahrscheinlicher.

### 4. Situation

Ob der Organismus dort sein kann, wo die Pflanze steht. Eine Gewächshaus-Weiße-Fliege an einer Zimmerpflanze ist gewöhnlich; eine Nacktschnecke auf der Fensterbank nicht. Jahreszeit und Überwinterung zählen im Freiland und in einem beheizten Raum fast nicht.

**Für Schädlinge läuft dieser Test auf Stufe 5.** Der Datensatz trägt weder Wirtsspektrum noch Feuchte-Ökologie, die Antwort kommt also aus allgemeinem Wissen über das Taxon und wird entsprechend gekennzeichnet. Für Krankheiten läuft er auf Stufe 2, weil `environmental_triggers` erfasst ist — und dieser Unterschied gehört in die Ausgabe statt geglättet zu werden.

## Von der Bestimmung zur Maßnahme

Übersteht ein Kandidat die Tests, ist die Maßnahmenseite besser durch den Datensatz gedeckt als die Bestimmung es war.

**Nützlinge.** `beneficials[].preys_on` benennt, was jeder Gegenspieler tatsächlich nimmt. Prüfe den genannten Gegenspieler gegen den bestimmten Schädling, statt der Verknüpfung zu vertrauen: Gemessen führen die an `Tetranychus urticae` hängenden Nützlinge mit `Coccinellidae` — einem generalistischen Blattlausräuber und nicht dem Spezialisten, den ein Spinnmilbenbefall verlangt. Ein Gegenspieler, der den Schädling nicht in `preys_on` führt, ist ein Befund.

Innen- und Freilandraum unterscheiden sich hier grundsätzlich, nicht graduell: Unter Glas oder im Zelt werden Nützlinge gezielt *eingebracht*, und die Frage ist welche Art und wann; im Freiland werden sie *gefördert und erhalten*, und eine Freilassungsempfehlung ist dort meist die falsche Form von Rat.

**Behandlungen.** `treatment_type` und `application_method` verorten eine Maßnahme in der IPM-Hierarchie — kulturell und physikalisch vor biologisch, biologisch vor chemisch. Eine Empfehlung, die mit einer chemischen beginnt, ohne zu sagen, warum die früheren Stufen erschöpft oder nicht verfügbar sind, ist unvollständig, unabhängig davon, ob das Mittel wirkt.

`safety_interval_days` ist die Karenz vor der Ernte und wird gegen die Pflanze geprüft, nicht abstrakt zitiert. Ist `allows_harvest` wahr und die Ernte nah, scheidet eine Behandlung aus, deren Karenz die verbleibende Zeit überschreitet — und das zu sagen, ist die Empfehlung.

Zwei Maßnahmen mit demselben Wirkstoff oder Wirkmechanismus dürfen nicht nacheinander als Alternativen empfohlen werden; so züchtet man Resistenz heran. Ist `active_ingredient` gleich `null`, ist der Wirkmechanismus aus dem Datensatz unbekannt und die Rotationsaussage nicht zu treffen.

**Gegenanzeigen sind nicht erfasst.** Kein Feld paart eine Behandlung mit einer, zu der sie im Widerspruch steht. Der klassische Konflikt — ein Breitband-Insektizid nach einer Nützlingsfreilassung, das diese auslöscht — muss also erschlossen statt nachgeschlagen und als Stufe 5 ausgewiesen werden.

## Ausgabe und Grenzen

Das Ergebnis benennt den Kandidaten, die tragende Stufe, welche Falsifikationstests er überstanden hat und welche mangels Datenlage nicht laufen konnten. Ein Kandidat, der jeden lauffähigen Test übersteht, wird als *nicht widerlegt* gemeldet, mit namentlicher Nennung der nicht laufbaren Tests.

Befunde tragen einen Schweregrad: Eine Aussage, die zu einer falschen oder schädlichen Maßnahme führen würde, rangiert über einer bloß unvollständigen, diese über einer Verfeinerung. Ein nebenbei gefundener Katalogfehler — ein falscher `pest_type`, eine honigtaubildende Milbe — wird als Befund gegen den Katalog gemeldet und nach `nolte/kamerplanter` gerichtet, nie hier korrigiert.

Das Verfahren schreibt nichts. Eine Inspektion oder einen Tagebucheintrag zu erfassen, ist ein eigener Schritt mit `-apply`-Suffix.

## Anforderungen

- **MUSS [MUST]** vor der Beurteilung `get_plant_inspections` aufrufen und **MUSS** eine leere Historie als „nicht inspiziert" melden, nicht als Abwesenheit von Druck
- **MUSS [MUST]** einen Kandidaten gegen `get_pest` oder `get_disease` auflösen statt aus dem Modellwissen, und **MUSS** das gelesene Tool benennen
- **MUSS [MUST]** den Ernährungsweise-Test auf jeden Kandidaten anwenden und **MUSS** einen Kandidaten verwerfen, dessen erfasste `damage_symptoms` seiner Ernährungsweise widersprechen
- **MUSS [MUST]** einen zum Taxon inkonsistenten `pest_type` als Befund gegen den Katalog melden und **DARF NICHT** den korrekten Wert stillschweigend einsetzen
- **MUSS [MUST]** jede Aussage zu Wirtsspektrum, Feuchte-Ökologie, Nachweismethode oder Gegenanzeige als nicht belegt kennzeichnen, da gemessen keines dieser Felder auf `get_pest` existiert
- **DARF NICHT [MUST NOT]** eine Feuchtepräferenz eines Schädlings als belegt darstellen; für eine Krankheit **MUSS** es `environmental_triggers` zitieren, wo vorhanden
- **MUSS [MUST]** in der Ausgabe *nicht widerlegt* von *bestimmt* unterscheiden und **MUSS** die nicht laufbaren Tests auflisten
- **MUSS [MUST]** `safety_interval_days` gegen die Erntesituation prüfen, sobald `allows_harvest` wahr ist, und **MUSS** eine Behandlung ausschließen, deren Karenz die verbleibende Zeit überschreitet
- **DARF NICHT [MUST NOT]** aus einem Rezept unter dieser Spezifikation `confirm_care_task`, `add_plant_diary_entry` oder ein anderes zustandsänderndes Tool aufrufen
- **SOLLTE [SHOULD]** jeden Eintrag in `beneficials[]` über `preys_on` gegen den bestimmten Schädling prüfen und **SOLLTE** eine Nichtübereinstimmung als Befund melden
- **SOLLTE [SHOULD]** angeben, ob eine Maßnahme für einen geschlossenen oder offenen Raum gedacht ist, da Einbringung und Erhaltung von Gegenspielern verschiedene Empfehlungen sind
- **SOLLTE [SHOULD]** die Nachweismethode benennen, die die Belegstufe heben würde, statt eine Behandlung zu nennen, solange die Bestimmung unter Stufe 2 liegt
- **SOLLTE [SHOULD]** die IPM-Hierarchie in der Reihenfolge der angebotenen Maßnahmen wahren und **SOLLTE** begründen, warum eine frühere Stufe entfällt, wenn mit einer späteren begonnen wird
- **SOLLTE [SHOULD]** `search_glossary` für einen fachsprachlich verwendeten Begriff konsultieren, statt ihn lokal zu definieren
- **KANN [MAY]** `get_treatment` für den vollständigen Datensatz einer Maßnahme lesen, wenn die verschachtelte `treatments[]`-Zusammenfassung nicht ausreicht
- **KANN [MAY]** einen Mangelverdacht an die [Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md) übergeben, wenn das Symptom zu beiden passt, und **KANN** umgekehrt vom Bildverfahren aufgerufen werden

## Akzeptanzkriterien

- [ ] Jede Bestimmung benennt ihre Belegstufe und das Tool, das den Datensatz lieferte
- [ ] Kein Ergebnis empfiehlt eine Behandlung auf einer Bestimmung der Stufe 3 oder darunter
- [ ] Eine Pflanze ohne Inspektionshistorie liefert eine Beurteilung, die die leere Historie ausweist
- [ ] Jeder Kandidat wurde durch den Ernährungsweise-Test geführt, und das Ergebnis steht in der Ausgabe
- [ ] Keine Aussage zu Wirtsspektrum, Feuchte-Ökologie oder Nachweismethode wird als belegt dargestellt
- [ ] Eine Krankheitsbeurteilung, die eine Feuchtebedingung anführt, zitiert `environmental_triggers`
- [ ] Jede genannte Behandlung trägt ihre `safety_interval_days` und eine Aussage zur Erntesituation der Pflanze
- [ ] Empfehlungen wahren die IPM-Reihenfolge oder begründen die Abweichung
- [ ] Nützlingsempfehlungen sind gegen `preys_on` geprüft und Nichtübereinstimmungen gemeldet
- [ ] Ein Katalogfehler wird als Befund gemeldet, nicht an Ort und Stelle korrigiert
- [ ] Kein Rezept unter dieser Spezifikation ruft ein zustandsänderndes Tool auf
- [ ] Die Ausgabe unterscheidet *nicht widerlegt* von *bestimmt*

## Offene Fragen

- Ob `optimal_humidity_min`/`max` upstream existiert und nur nicht ausgespielt wird oder im Modell gar nicht vorkommt. Davon hängt ab, ob dieses Verfahren ein Feld einfordern oder eine dauerhafte Stufe-5-Lücke hinnehmen sollte.
- Ob `host_plants` folgt. Bis dahin ruht die Plausibilität eines Schädlings auf einer gegebenen Art vollständig auf allgemeinem Wissen — dem schwächsten Glied einer sonst belegten Kette.
- Was `get_plant_inspections` an einer tatsächlich inspizierten Pflanze zurückgibt. Gemessen nur gegen eine leere Historie; die Feldnamen für Druckniveau und Befunde stammen aus der Tool-Beschreibung, nicht aus einer befüllten Antwort.
- Ob Krankheits- und Schädlingskatalog ein gemeinsames Symptomvokabular teilen oder dasselbe sichtbare Zeichen je verschieden beschreiben — davon hängt ab, ob ein einzelnes Symptom in einem Durchgang gegen beide gematcht werden kann.
- Ob Home Assistant Feuchte- oder Temperatursensoren führt, die den Situationstest von Stufe 3 auf Stufe 1 heben könnten, und wie ein Sensor an eine Pflanzeninstanz gebunden würde. Dieselbe offene Frage wie im Nährstoffverfahren und dieselbe fehlende Zuordnung.
- Ob Gegenanzeigen zwischen Behandlungen hierher, in den Backend-Katalog oder ins Glossar gehören. Sie in dieser Spezifikation zu kodieren, birgt genau die Drift, die dieses Repository für Artdaten vermeidet.

## Quelle

- Gemessen gegen die Kamerplanter-Referenzinstanz am 2026-08-07 über `POST /api/v1/mcp`, nur lesend: `list_pests` (34), `get_pest` (`Tetranychus urticae`, vollständige Feldmenge inkl. verschachtelter `treatments[]` und `beneficials[]`), `list_diseases` (34, `environmental_triggers` beobachtet), `get_plant_inspections` (leere Historie), `get_species_info` (`Allium porrum`, `Spathiphyllum wallisii`), `list_phase_definitions` (29). Kein Schreibtool wurde aufgerufen.
- Fachverfahren übernommen aus `nolte/kamerplanter`, `.claude/skills/check-pest-data/SKILL.md` — die Signaturtabelle der Ernährungsweisen, die Zuordnung Taxon zu `pest_type`, die Größenordnungen der Generationsdauern, die Unterscheidung von Innen- und Freilandmaßnahmen sowie die IPM-Reihenfolge. Jener Skill beurteilt die dortige `ipm.yaml`; diese Spezifikation regelt dieselbe Beurteilung, angewandt auf das, was der MCP-Server liefert.
- Begleitende Verfahren: [Pflanzengesundheits-Bildanalyse](../plant-health-image-analysis/de.md), [Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md)
- Rezeptmechanik: [Das Goose-Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Server-Vertrag: [Die Kamerplanter-MCP-Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md)
