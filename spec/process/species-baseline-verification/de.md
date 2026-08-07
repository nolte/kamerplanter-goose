# Überprüfung der Speziesbaseline

Status: Entwurf
Portfolio-Scope: local

## Kontext

Jede Beurteilung, die dieses Repository über eine Pflanze trifft, wird gegen eine Baseline gemessen: was für diese Art, in dieser Phase, zu dieser Jahreszeit normal ist. Diese Baseline zu erheben, ist ein gelöstes Problem — der Server liefert sie, und der Skill `plant-context-collect` normalisiert sie. **Ob die Baseline stimmt, prüft niemand**, und eine falsche Baseline scheitert nicht laut. Sie erzeugt weiter unten eine selbstsichere, gut begründete, falsche Antwort: ein Lichtkeimer, einen Zentimeter tief vergraben, weil `sowing_depth_cm` es so sagte; ein als überfällig beurteiltes Erntefenster, gemessen an Monaten, die zu einer anderen Anbauperiode gehören; eine Frostwarnung, die nie auslöst, weil `frost_sensitivity` an einer tropischen Blattschmuckpflanze `hardy` liest.

Die Baseline ist auch der Ort, an dem Abwesenheit am leichtesten für eine Tatsache gehalten wird. Gemessen liefert `get_species_info` **nur die befüllten Felder**, und die Menge unterscheidet sich je Art: `Allium porrum` kam mit 23 Feldern samt vollständigem `seed_profile` zurück, `Spathiphyllum wallisii` mit 18 und ganz ohne `seed_profile`. Keine der beiden trug `toxicity`, obwohl die Beschreibung des Tools es ausweist. Wer einen fehlenden Schlüssel als „trifft nicht zu" liest, erklärt jemandem ein Einblatt für katzensicher.

Diese Spezifikation deckt zwei Fragen ab, die sich eine Datenquelle und eine Disziplin teilen:

- **Ist die erfasste Baseline plausibel** für diese Art — Keimparameter, Saattiefe gegen Lichtbedarf, Winterhärte gegen Herkunft, Ernte gegen Wuchsform?
- **Wie sieht der Lebenszyklus aus** — einjährig, zweijährig oder mehrjährig; die Aussaat-, Blüh- und Erntefenster; Dormanz und Frostempfindlichkeit —, wo der Datensatz schweigt oder sich widerspricht?

Sie bilden eine Spezifikation, weil die Lebenszyklusfenster *selbst* Baseline-Felder sind. Eine Trennung würde `bloom_months` im einen Dokument als zu prüfenden Wert führen und im anderen als zu bestimmenden.

Die gemeinsame Disziplin ist der eigentliche Grund für diese Spezifikation. Botanische Fakten sind genau das, was ein Sprachmodell flüssig und falsch produziert. **Keine Aussage hier darf auf Erinnerung ruhen.** Die aus dem Quellverfahren übernommene Regel lautet: drei unabhängige Quellen, bevor ein Wert als gesichert gilt, eine gerankte Quellenhierarchie und — das ist der arbeitende Teil — eine Konfidenzstufe, die entscheidet, ob überhaupt etwas geschieht. Unterhalb von *gesichert* bleibt der erfasste Wert stehen und der Zweifel wird berichtet. Diese Verweigerung ist das Ergebnis.

Alles als *gemessen* Gekennzeichnete wurde am 2026-08-07 von der Referenzinstanz gelesen.

Leserschaft: Autorinnen und Autoren von Rezepten, die eine Speziesbaseline konsumieren, sowie alle, die eine vorgeschlagene Korrektur prüfen, bevor sie `nolte/kamerplanter` erreicht.

## Ziele

- Ein Baseline-Feld wird an der tatsächlichen Biologie der Art gemessen, nicht bloß am Schema, das es zugelassen hat
- Ein fehlendes Feld wird als unbefüllt gemeldet, nie als negative Tatsache gelesen
- Lebenszyklusfenster werden gegen die instanzeigenen Frostdaten aufgelöst, nicht gegen einen generischen Kalender
- Jede botanische Aussage trägt eine Konfidenzstufe und ihre Quellen; nur die höchste Stufe rechtfertigt eine vorgeschlagene Korrektur
- Feldübergreifende Widersprüche werden sichtbar gemacht, denn ein Feld kann für sich plausibel und im Verbund unmöglich sein
- Wo botanischer und kultureller Zyklus auseinandergehen, wird beides genannt — die meisten essbaren Zweijährigen werden einjährig kultiviert

## Nicht-Ziele

- In den Artenkatalog, die Pflanze oder irgendeinen Kamerplanter-Datensatz schreiben; Korrekturen sind Vorschläge an `nolte/kamerplanter`
- Artenstammdaten oder Pflanzensteckbriefe verfassen — diese Pipeline lebt in `nolte/kamerplanter` und arbeitet auf Dateien, die dieses Repository nicht hält
- Die Gesundheit, Ernährung oder den Schädlingsdruck einer einzelnen Pflanze beurteilen; das sind [Bildanalyse](../plant-health-image-analysis/de.md), [Nährstoff-Ungleichgewichte](../nutrient-imbalance-detection/de.md) und [Schädlingsdruck](../pest-pressure-assessment/de.md)
- Ein Saatgutprüflabor ersetzen; dieses Verfahren schließt aus publiziertem gartenbaulichem Wissen und dem Datensatz
- Rezeptmechanik sowie MCP-Transport, -Authentifizierung und -Mandantenfähigkeit — spezifiziert im [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) und in der [Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md)

## Gemessene Ausgangslage

### Was `get_species_info` trägt

Gemessen an zwei bewusst verschiedenen Arten — einer Feldkultur und einer Zimmerpflanze:

| Gruppe | Beobachtete Felder |
|--------|--------------------|
| Identität | `species_key`, `scientific_name`, `common_names[]`, `genus`, `family_key`, `native_habitat` |
| Form | `growth_habit`, `root_type`, `plant_category`, `traits[]` |
| Zeiten | `direct_sow_months[]`, `harvest_months[]`, `bloom_months[]`, `sowing_indoor_weeks_before_last_frost`, `growing_periods[]` |
| Klima | `hardiness_zones[]`, `frost_sensitivity`, `base_temp_gdd` |
| Kultur | `nutrient_demand_level`, `green_manure_suitable`, `allows_harvest` |
| Saatgut | `seed_profile` — `germination_temp_min_c`, `germination_temp_max_c`, `sowing_depth_cm`, `days_to_germination`, `seed_viability_years`, `light_germination`, `pretreatment[]`, `thousand_seed_weight_g`, `sowing_density_per_m2` |
| Bezüge | `compatible_companions[]` (mit `score`), `cultivars[]` (mit `traits[]`, `days_to_maturity`, `seed_type`) |

`growing_periods[]` ist das Feld, das eine naive Lesart übersieht. Gemessen trägt `Allium porrum` zwei — Sommer- und Winterporree —, **jede mit eigenen `direct_sow_months` und `harvest_months`**. Die Monate auf oberster Ebene sind die Vereinigung über alle Perioden; eine Beobachtung ohne vorherige Periodenwahl dagegen zu halten, ergibt ein Fenster, das zu weit ist, um falsch zu sein, und zu weit, um zu nützen.

### Was es nicht trägt

Gemessen an beiden Arten abwesend, obwohl Dimensionen des Quellverfahrens: `photosynthesis_type`, `light_compensation_point_ppfd_min`/`max`, `shade_tolerance`, `salt_tolerance_class` samt Maas-Hoffman-Schwelle und -Steigung, `waterlogging_tolerance`, `soil_ph_preference`, `effective_root_depth_cm`, `climacteric`, `harvested_part`, `harvest_pattern`, `propagation_configs`, `allergen_info` sowie jedes explizite `cycle_type`.

**Auf `toxicity` ist besonders zu achten.** Die Tool-Beschreibung nennt es; keine der beiden Messungen lieferte es, auch nicht an einer Art mit bekannter Calciumoxalat-Toxizität. Ob das Feld unbefüllt oder nicht ausgespielt ist, bleibt offen — und bis dahin darf kein Lauf eine Pflanze aufgrund seiner Abwesenheit als ungiftig melden.

Das Fehlen von `cycle_type` bedeutet, dass die Frage einjährig/zweijährig/mehrjährig vom Artdatensatz nicht direkt beantwortet wird. Sie wird erschlossen — aus `growing_periods[]`, aus `bloom_months` gegen `harvest_months`, aus `hardiness_zones` und aus den Phasen, die der Pflanze tatsächlich zugewiesen sind — und jeder solche Schluss ist eine Behauptung, kein Nachschlagen.

### Die Lebenszyklus-Quellen

Drei Tools tragen, was der Artdatensatz nicht trägt:

| Tool | Liefert | Gemessen |
|------|---------|----------|
| `get_sowing_calendar` | Aussaat-, Auspflanz- und Erntebalken je Art für ein Jahr, dazu `frost.last_frost_date`, `frost.first_frost_date`, `frost.eisheilige_date` | `2026-05-01`, `null`, `2026-05-15` für die Referenzinstanz. **Verweigert einen unspezifizierten Aufruf** — ohne `query` antwortet er `validation.error` mit den abgedeckten 148 Arten und der `limit`-Obergrenze 25 |
| `list_overwintering_profiles` | Je Pflanze: `hardiness_zone_min`, `hardiness_rating`, `winter_action` + `winter_action_month`, `spring_action` + `spring_action_month`, `auto_generated`, `user_overridden`, `derived_path` | 5 Profile; die gesehenen mit `auto_generated: true`, `user_overridden: false` |
| `list_phase_definitions` | Das Vokabular der Lebenszyklus-Engine — `name`, `display_name`, `typical_duration_days`, `stress_tolerance`, `watering_interval_days`, `tags[]` | 29 Definitionen, darunter `dormancy` (120 Tage) und `active_growth` (180 Tage) |

`frost.eisheilige_date` ist die instanzeigene Antwort auf die Eisheiligen-Frage, und daran wird eine Aussaatempfehlung gemessen — nicht an einer erinnerten Faustregel. `first_frost_date` war zur Messung `null`, die Herbsthälfte des Kalenders hat also keinen Anker, und jede Aussage über das Ausgraben von Knollen vor dem ersten Frost hängt in der Luft.

Ein Überwinterungsprofil mit `auto_generated: true` und `user_overridden: false` ist eine Ableitung, keine Beobachtung. Es belegt, was das System erschlossen hat, und erbt jeden Fehler der Speziesbaseline, aus der es abgeleitet wurde — es ist damit eine bestätigende, nie eine unabhängige Quelle.

## Quellenhierarchie und Drei-Quellen-Regel

**Kein botanischer Wert darf aus der Erinnerung behauptet werden.** Jede Aussage zu Keimung, Zeiten, Dormanz, Winterhärte oder Toxizität wird entweder aus dem Datensatz gelesen — und als solche gekennzeichnet — oder recherchiert und belegt.

Eine Korrektur verlangt **drei übereinstimmende, unabhängige Quellen**. Unabhängig heißt: einander nicht zitierend; drei Seiten, die den Katalogtext einer Gärtnerei wiederholen, sind eine Quelle.

| Rang | Quellentyp | Zuverlässigkeit |
|------|------------|-----------------|
| 1 | Universitäre Gartenbauinstitute, Landwirtschaftskammern und Beratungsdienste, RHS, ISTA | Höchste |
| 2 | Gartenbauliche Standardwerke und botanische Enzyklopädien — Missouri Botanical Garden, PFAF, POWO/WCVP für Taxonomie, FAO für Salztoleranz | Hoch |
| 3 | Saatguthäuser und Gärtnereien, speziell für Aussaat- und Erntezeiten | Hoch für Zeiten |
| 4 | Gartenportale mit Fachredaktion | Mittel |
| 5 | Foren und Community-Beiträge | Niedrig; nur ergänzend |

**Nie allein ausreichend:** Wikipedia, KI-generierte Texte, unattribuierte Blogbeiträge oder jede Seite, deren einziger Inhalt das Zitat einer anderen Quelle ist.

In mindestens zwei Formulierungen suchen — wissenschaftlicher und Volksname, und bei in Mitteleuropa kultivierten Pflanzen deutsch und englisch —, denn eine einzelne Formulierung wählt eine einzelne Publikationstradition aus.

## Konfidenz, und was jede Stufe erlaubt

| Stufe | Bedeutung | Erlaubt |
|-------|-----------|---------|
| **Gesichert** | Drei oder mehr unabhängige Quellen stimmen überein | Eine vorgeschlagene Korrektur, mit Quellen |
| **Wahrscheinlich** | Zwei Quellen stimmen überein, oder drei mit kleiner Abweichung | Einen Befund. Der erfasste Wert bleibt |
| **Unsicher** | Quellen widersprechen sich, oder es fand sich nur eine | Einen Befund, der den Widerspruch benennt. Der erfasste Wert bleibt |
| **Nicht verifizierbar** | Keine brauchbare Quelle | Eine benannte Lücke. Der erfasste Wert bleibt |

Die Asymmetrie ist Absicht und tragend: Nur die oberste Stufe bewegt etwas. Alles darunter wird berichtet. **Ein Lauf, der zwölf zweifelhafte Werte findet und keine Korrektur vorschlägt, hat seine Arbeit getan**; ein Lauf, der einen Wert bei *wahrscheinlich* „verbessert", nicht.

## Die Plausibilitätsprüfungen

Anzuwenden auf das, was der Datensatz tatsächlich trägt. Eine Prüfung, deren Feld fehlt, wird als nicht durchgeführt gemeldet, nie als bestanden.

### Saatgut und Keimung

- `germination_temp_min_c` < `germination_temp_max_c`, und die Spanne passt zur Art statt zu einem Standardwert. Kaltkeimer liegen bei 2–10 °C, Wärmekeimer bei 20–30 °C; ein Katalog, in dem jede Art 20–25 °C liest, hat einen Default, keine Daten.
- `sowing_depth_cm` gegen `light_germination`. **Ein Lichtkeimer wird angedrückt, nicht vergraben** — `light_germination: light` bei `sowing_depth_cm` von 1 ist ein Widerspruch, den das Schema erlaubt und das Saatkorn nicht überlebt. Gemessen liest `Allium porrum` `dark` bei 1,0 cm, was stimmig ist.
- `light_germination` gegen Samengröße: Feinsamige Arten brauchen tendenziell Licht, großsamige Dunkelheit.
- `pretreatment[]` gegen Herkunft. Kaltstratifikation gehört zu temperaten Gehölzen und Kaltkeimern, Skarifikation zu hartschaligen Samen, Vorquellen zu langsam quellenden. **Stratifikation bei einer tropischen Art ist ein Befund**, keine Feinheit.
- `seed_viability_years` und `days_to_germination` konsistent zueinander und zur Temperaturspanne.

### Klima und Herkunft

- `frost_sensitivity` gegen `hardiness_zones` und `native_habitat`. Gemessen liest `Spathiphyllum wallisii` `sensitive` bei den Zonen `10b`–`11a` und mittelamerikanischer Herkunft — in sich stimmig. `Allium porrum` liest `hardy` über zehn Zonen. Zu suchen ist der Widerspruch: `hardy` bei einer Art, deren Zonen bei 10 beginnen.
- `base_temp_gdd` gegen dasselbe: gemessen 5,0 für Porree, 15,0 für das Einblatt. Eine tropische Art mit temperater Basistemperatur sammelt Wachstumsgradtage, die nie stattgefunden haben.

### Zeiten

- Blüte vor Ernte bei einer Fruchtkultur; eine Überlappung ist bei Blatt- oder Schnittkulturen normal und bei einer Frucht verdächtig.
- Jeder Eintrag in `growing_periods[]` in sich stimmig, und die Monate der obersten Ebene gleich ihrer Vereinigung.
- `direct_sow_months` und `sowing_indoor_weeks_before_last_frost` konsistent zu `frost.last_frost_date` und `frost.eisheilige_date` aus dem Kalender der Instanz.
- `allows_harvest` gegen `growth_habit` und das Vorhandensein von `harvest_months`.

### Feldübergreifend

Ein Feld kann allein plausibel und im Verbund unmöglich sein. Ausdrücklich zu prüfende Paare: Saatgutprofil vorhanden, aber keine Aussaatmonate; Erntemonate vorhanden bei `allows_harvest: false`; `days_to_maturity` einer Sorte unvereinbar mit der Spanne von Aussaat bis Ernte der Art; `compatible_companions` hoch bewertet für eine Art, die dieselben Standortbedingungen nicht teilen kann.

`compatible_companions` betrifft Pflanzentscheidungen. Es ist kein Beleg über die eigene Physiologie der Pflanze und darf nicht in eine solche Beurteilung übernommen werden.

## Den Lebenszyklus auflösen

Wo der Zyklus nicht erfasst ist, wird er in dieser Reihenfolge bestimmt — und die Reihenfolge zählt, weil jeder Schritt die Frage ohne den nächsten klären kann:

1. **Die Zuweisung der Instanz selbst.** Die `current_phase` der Pflanze gegen `list_phase_definitions` — eine Pflanze mit zugewiesener `dormancy` wird vom System als mehrjährig behandelt, was der Artdatensatz auch nahelegen mag.
2. **`growing_periods[]` und die Monatsfelder.** Aussaat und Ernte innerhalb eines Kalenderjahres ohne Dormanz deuten auf einjährig; ein Blühfenster im Jahr nach der Aussaat auf zweijährig; wiederkehrende Blüte und Ernte mit Dormanzphase auf mehrjährig.
3. **`list_overwintering_profiles`** für die Pflanze — eingedenk dessen, dass ein `auto_generated`-Profil bestätigt und nicht belegt.
4. **Recherchiert, unter der Drei-Quellen-Regel**, wo der Datensatz schweigt oder sich selbst widerspricht.

**Botanischen und kultivierten Zyklus getrennt nennen, wo sie auseinandergehen.** Zwiebel und Porree sind botanisch zweijährig und werden als Gemüse einjährig kultiviert; nur eines von beidem zu erfassen, beantwortet die Hälfte der daran gestellten Fragen falsch. Das ist die häufigste Abweichung in einem essbaren Katalog und der Grund, warum das Feld nicht einfach aus einem botanischen Nachschlagewerk übernommen werden kann.

## Ausgabe und Grenzen

Das Ergebnis meldet je Feld: was der Datensatz hält, ob die Prüfung lief, den Befund falls vorhanden, die Konfidenz und die Quellen. Felder, deren Prüfung mangels Feld nicht laufen konnte, werden als unbefüllt geführt — getrennt von geprüften und bestandenen Feldern. Beides zusammenzuwerfen, ist genau das, was aus einer Lücke eine falsche Sicherheit macht.

Der Schweregrad richtet sich nach der Folge: Ein Wert, der zu einer misslungenen Aussaat, einer toten Pflanze oder einer Sicherheitsaussage über Toxizität führen würde, rangiert über einem bloß irreführenden, dieser über einer Verfeinerung.

Vorgeschlagene Korrekturen gehen an `nolte/kamerplanter`, wo die Artdaten liegen. Dieses Verfahren schreibt nichts.

## Anforderungen

- **DARF NICHT [MUST NOT]** einen botanischen Wert aus der Erinnerung behaupten; jede Aussage wird entweder aus dem Datensatz gelesen und gekennzeichnet oder recherchiert und belegt
- **MUSS [MUST]** vor einer vorgeschlagenen Korrektur drei unabhängige, einander nicht zitierende Quellen verlangen und **MUSS** bei jeder niedrigeren Konfidenz den erfassten Wert stehen lassen
- **MUSS [MUST]** jedem Befund die Konfidenzstufe und die Quellen beifügen
- **MUSS [MUST]** ein in `get_species_info` fehlendes Feld als unbefüllt melden und **DARF NICHT** Abwesenheit als negative Tatsache behandeln — insbesondere **DARF NICHT** eine Pflanze als ungiftig melden, weil `toxicity` fehlt
- **MUSS [MUST]** bei mehreren `growing_periods[]` die zutreffende Periode wählen, bevor eine Beobachtung gegen `direct_sow_months` oder `harvest_months` beurteilt wird
- **MUSS [MUST]** `sowing_depth_cm` gegen `light_germination` prüfen und den Widerspruch „vergrabener Lichtkeimer" als Befund hohen Schweregrads melden
- **MUSS [MUST]** Frostdaten für die Instanz aus `get_sowing_calendar` lesen statt eine Regionalregel anzunehmen, und **MUSS** angeben, wenn `first_frost_date` gleich `null` ist, statt eines zu unterstellen
- **MUSS [MUST]** `get_sowing_calendar` mit `query` aufrufen, da ein unspezifizierter Aufruf gemessen mit `validation.error` abgelehnt wird
- **MUSS [MUST]** botanischen und kultivierten Zyklus getrennt nennen, wo sie auseinandergehen
- **DARF NICHT [MUST NOT]** ein zustandsänderndes Tool aufrufen; Korrekturen sind Vorschläge an `nolte/kamerplanter`
- **SOLLTE [SHOULD]** Prüfungen, die mangels Feld nicht laufen konnten, getrennt von geprüften und bestandenen auflisten
- **SOLLTE [SHOULD]** ein Überwinterungsprofil mit `auto_generated: true` nur als Bestätigung werten, da es aus derselben geprüften Baseline abgeleitet ist
- **SOLLTE [SHOULD]** in mindestens zwei Formulierungen suchen, wissenschaftlich und volkstümlich, und bei mitteleuropäischen Kulturen deutsch wie englisch
- **SOLLTE [SHOULD]** Befunde nach Folgenschwere ordnen und eine misslungene Aussaat oder eine Toxizitätsaussage über einen irreführenden Wert stellen
- **SOLLTE NICHT [SHOULD NOT]** `compatible_companions` in eine physiologische Beurteilung übernehmen
- **KANN [MAY]** `get_cultivar` lesen, wenn `days_to_maturity` oder `traits` einer Sorte die Arterwartung eingrenzen
- **KANN [MAY]** `search_glossary` nach der projekteigenen Definition eines Begriffs befragen, bevor ein externer eingeführt wird

## Akzeptanzkriterien

- [ ] Jeder Befund trägt eine Konfidenzstufe und seine Quellen
- [ ] Keine Korrektur wird unterhalb der Stufe *gesichert* vorgeschlagen
- [ ] Fehlende Felder werden als unbefüllt gemeldet und getrennt von bestandenen Prüfungen geführt
- [ ] Kein Lauf meldet eine Pflanze aufgrund eines fehlenden `toxicity`-Feldes als ungiftig
- [ ] Eine Art mit mehreren `growing_periods[]` wird gegen die zutreffende Periode beurteilt, nicht gegen die Vereinigung
- [ ] Jeder `get_sowing_calendar`-Aufruf übergibt `query`
- [ ] Frostbezogene Zeitaussagen zitieren `last_frost_date` oder `eisheilige_date` der Instanz
- [ ] Ein `null`-`first_frost_date` wird als fehlender Anker ausgewiesen statt ersetzt
- [ ] Botanischer und kultivierter Zyklus stehen beide dort, wo sie sich unterscheiden
- [ ] Kein Rezept unter dieser Spezifikation ruft ein zustandsänderndes Tool auf
- [ ] Feldübergreifende Widersprüche werden auch dann gemeldet, wenn jedes Feld für sich plausibel ist

## Offene Fragen

- Ob `toxicity` für die geprüften Arten unbefüllt oder vom Tool gar nicht ausgespielt wird. Solange das ungeklärt ist, ist eine ganze Klasse von Sicherheitsfragen aus dem Datensatz unbeantwortbar — ein schlechterer Zustand als eine dokumentierte Lücke.
- Ob die umweltphysiologischen Felder — Photosynthesetyp, Lichtkompensationspunkt, Salztoleranz, Boden-pH-Präferenz — upstream existieren. Das Quellverfahren prüft sie alle; keines war hier beobachtbar, diese Dimensionen sind derzeit also unerreichbar statt bestanden.
- Ob `cycle_type` unter anderem Namen existiert oder die Schlusskette dieser Spezifikation der einzige Weg ist. Existiert es, kollabiert der größte Teil der Lebenszyklus-Auflösung zu einem Nachschlagen.
- Warum `first_frost_date` `null` ist, während `last_frost_date` und `eisheilige_date` befüllt sind, und ob es später im Jahr verfügbar wird. Die Herbstplanung hängt vollständig daran.
- Ob `derived_path` an einem Überwinterungsprofil ausweist, welche Regel es erzeugt hat — das würde die Ableitung prüfbar machen statt nur markiert.
- Wie eine vorgeschlagene Korrektur `nolte/kamerplanter` erreichen soll — als Issue, als Pull Request gegen die Seed-Daten oder als Bericht, den ein Mensch hinüberträgt. Die `github`-MCP-Extension ist hier deklariert, der Mechanismus existiert also; die Konvention nicht.

## Quelle

- Gemessen gegen die Kamerplanter-Referenzinstanz am 2026-08-07 über `POST /api/v1/mcp`, nur lesend: `list_species` (210), `get_species_info` (`Allium porrum` 23 Felder mit vollständigem `seed_profile` und zwei `growing_periods`; `Spathiphyllum wallisii` 18 Felder, kein `seed_profile`, keine der beiden mit `toxicity`), `get_sowing_calendar` (unspezifiziert abgelehnt; mit `query` Frostdaten und Balken je Art), `list_overwintering_profiles` (5), `list_phase_definitions` (29), `list_plants`. Kein Schreibtool wurde aufgerufen.
- Fachverfahren übernommen aus `nolte/kamerplanter`: `.claude/skills/check-seed-data/SKILL.md` für die Saatgut-, Keim- und feldübergreifenden Dimensionen sowie `.claude/skills/plant-lifecycle/SKILL.md` für die Drei-Quellen-Regel, die Quellenhierarchie, die Konfidenzstufen und die Unterscheidung von botanischem und kultiviertem Zyklus. Jene Artefakte beurteilen die dortigen YAML-Seed-Daten; diese Spezifikation regelt dieselbe Beurteilung, angewandt auf das, was der MCP-Server liefert.
- Begleitende Verfahren: [Schädlingsdruck](../pest-pressure-assessment/de.md), [Nährstoff-Ungleichgewichte](../nutrient-imbalance-detection/de.md), [Pflanzengesundheits-Bildanalyse](../plant-health-image-analysis/de.md)
- Rezeptmechanik: [Das Goose-Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Server-Vertrag: [Die Kamerplanter-MCP-Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md)
