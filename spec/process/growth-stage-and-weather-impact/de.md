# Wachstumsstadium und Wetterwirkung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Unter fast jedem anderen Urteil über eine Pflanze liegen zwei Fragen: Steht sie in ihrer Entwicklung dort, wo ihr Datenbestand sagt, und was macht das Wetter mit ihr. Jede hat eine verlockende falsche Antwort. Ein Wachstumsstadium, das allein aus der erfassten Phase gelesen wird, wiederholt, was vor Wochen eingetragen wurde, und ein Stadium, das allein aus aufsummierter Wärme berechnet wird, verortet eine Pflanze anhand einer Zahl, die niemand an der Pflanze geprüft hat. Eine Wetterangabe, die zu einem Pflanzensymptom gemacht wird („der Frost hat die Blätter geschädigt“), meldet als beobachtet, was nur eine Exposition war. Diese Spezifikation legt fest, worauf eine Beurteilung des Wachstumsstadiums und eine Beurteilung der Wetterwirkung ruhen dürfen, welche geschlossene Menge an Antworten jede geben darf, wie die drei abgeleiteten Größen (Wachstumsgradtage, Dampfdruckdefizit, Photoperiode) berechnet werden und was sie nicht entscheiden dürfen, und wie eine Wetterexposition von einem Pflanzensymptom getrennt bleibt.

Eine Beurteilung ist hier eine Aussage an eine Person. Sie ändert nichts und wird aus Blöcken getroffen, die andere Skills bereits gesammelt haben, zuzüglich höchstens zweier Phasen-Lesezugriffe und eines optionalen Home-Assistant-Lesezugriffs, die unten genannt sind.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-16, und aus der [Spezifikation des Home-Assistant-MCP-Servers](../../mcp/home-assistant-mcp-server/de.md), gemessen am 2026-08-04; keine wurde für diese Spezifikation neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Sechs Tatsachen, auf denen die Anforderungen ruhen, wurden aus der Arbeitskopie gelesen und nicht gemessen: Die 44 Lese-Tools der Server-Spezifikation enthalten kein Wetter- und kein Vorhersage-Tool (ihr Abschnitt „Lesetools“); `get_plant_phase_status` kann `phase_state: unresolved` liefern, was wie ein normales Ergebnis aussieht und keines ist (ihre Signaturtabelle), und `plant-context-collect` ruft es nicht auf (`.claude/skills/plant-context-collect/SKILL.md` §2 und §4); keine Spezifikation hält die Antwortfelder von `get_plant_phase_history` fest (eine Suche in `spec/` findet den Tool-Namen nur in Katalog- und Tabellenzeilen); der Artdatensatz trägt `base_temp_gdd`, gemessen 5,0 für Lauch und 15,0 für das Einblatt, und die Sorte trägt `days_to_maturity` in Tagen ([Spezifikation zur Artdaten-Prüfung](../species-baseline-verification/de.md)); keine Spezifikation hält ein Feld zur Photoperiodenempfindlichkeit oder ein GDD-Ziel für ein Stadium oder für die Reife fest (eine Suche in `spec/` nach „photoperiod“ und „GDD“ findet keines von beiden); und ob Home Assistant eine Wetter-Entität bereitstellt, ist nicht gemessen ([Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md), Stufe 6).

Grenzen: Die [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln und die Form einer Empfehlung; Wetter ist ihre Stufe 6, und sie ordnet Quellen ein, nicht Ableitungen, daher trägt eine Ableitung hier keine Stufe. Diese Spezifikation nennt keine eigene Stufe. Die [Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) besitzt die Einklinkform eines Befunds und die tägliche Prüfung, die diese Beurteilungen ausführt. Die [Spezifikation zur Artdaten-Prüfung](../species-baseline-verification/de.md) besitzt die Plausibilität des Artdatensatzes, den diese Beurteilungen lesen, einschließlich der Warnung vor einer tropischen Art mit gemäßigter Basistemperatur. `plant-context-collect` besitzt den Pflanzenkontext-Block und `plant-lifecycle-resolve` die Lebenszyklus-Fenster; keines von beiden wird hier geändert. Das [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt, wie ein Rezept gebaut wird, einschließlich der namentlichen Verbote, und die Home-Assistant-Server-Spezifikation besitzt die Regeln für ihre Tools.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Autorinnen und Autoren der Domänen Pflanzengesundheit (nolte/kamerplanter-goose#48) und Ernte (#50), die diese Ergebnisse lesen werden, und die Personen, die die Beurteilungen ausführen und lesen, bevor sie handeln.

## Ziele

- Ein Ergebnis zum Wachstumsstadium sagt, ob das erfasste Stadium zu dem passt, was über die Pflanze bekannt ist, mit seinem Beleg und seiner Konfidenz, und sagt offen, wenn nichts bekannt ist
- Wachstumsgradtage, Dampfdruckdefizit und Photoperiode werden verwendet, wenn ihre Eingaben vorliegen, und mit Grund als fehlend gemeldet, wenn nicht
- Eine Wetterwirkung ist eine Exposition oder ein erwartetes Risiko, nie ein Symptom der Pflanze, und ein Symptom wird nie aus dem Wetter gelesen
- Unsicherheit ist ausdrücklich: was jedes Ergebnis nicht weiß und was es ändern würde
- Die Ergebnisse klinken sich in den Pflegeplan ein und übergeben benannte Felder an die Domänen Pflanzengesundheit und Ernte

## Nicht-Ziele

- Pflanzengesundheit und Schädlingsmanagement (nolte/kamerplanter-goose#48) und Ernteplanung (#50), über die in Abschnitt F genannten Übergabefelder hinaus
- Die erfasste Phase ändern: kein `-apply`-Rezept. Ein fragliches Stadium nennt die Mutation, die ein späterer Anwendungsschritt aufrufen würde, und ruft nichts auf
- Ein Wetter-Backend, eine Zuordnung von einem Home-Assistant-Sensor zu einer Pflanze oder eine Tabelle von GDD-Zielen je Stadium: Keines hat eine Quelle
- Die Stufen der Entscheidungsrichtlinie neu ordnen, auch nicht für Fragen, bei denen das Wetter entscheidet (Offene Fragen)
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikationen und sagen, dass sie nicht neu gemessen wurden

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** den Pflanzenkontext-Block von `plant-context-collect` so übernehmen, wie er ist, und **DARF NICHT [MUST NOT]** ein Tool aufrufen, um zu holen, was er schon enthält; **DARF [MAY]** den Leseberichts-Block und die Messwerte von `diary-measurements-read`, die Befunde von `plant-photo-read`, den Lebenszyklus-Bericht von `plant-lifecycle-resolve` und den Gartenkontext-Block von `garden-context` so übernehmen, wie sie sind
- **MUSS [MUST]** als vom Aufrufer geliefert, mit `caller` gekennzeichnet, nur Tatsachen annehmen, für die der Server keine Quelle hat: Wetter und Vorhersage, eine tägliche Temperaturreihe, den Breitengrad, einen Lichtplan für drinnen, wo die Pflanze steht (draußen, geschützt, drinnen), die eigene Beobachtung der Person an der Pflanze und das Beurteilungsdatum
- **MUSS [MUST]** das Beurteilungsdatum vom Aufrufer nehmen oder, ohne eines, vom erfassten Datum der jüngsten datierten verwendeten Beobachtung (ein tatsächlich gelesener Tagebucheintrag dieser Pflanze), **MUSS [MUST]** keinen zeitbezogenen Vergleich und keine zeitbezogene Ableitung berechnen (Tage in der Phase, Tage seit dem Pflanzen, Monatsfenster, Wachstumsgradtage, Photoperiode), wenn die eigene Beobachtung der Person ohne ein Beurteilungsdatum vom Aufrufer geliefert wird, und dabei sagen, dass die Beobachtung kein Datum trägt, und **DARF NICHT [MUST NOT]** das aktuelle Datum lesen
- **MUSS [MUST]** jede fehlende Eingabe als fehlend mit Grund melden, `no source` oder `not collected`, und **DARF NICHT [MUST NOT]** sie auffüllen

### B. Das Wachstumsstadium

- **MUSS [MUST]** `get_plant_phase_status` für die Pflanze aufrufen und **MUSS [MUST]** `phase_state: unresolved` als fehlendes erfasstes Stadium melden, nie als normales
- **DARF [MAY]** `get_plant_phase_history` für die Pflanze aufrufen und **MUSS [MUST]** seine Antwort so melden, wie sie zurückkam, ohne einen Feldnamen anzunehmen
- **MUSS [MUST]** genau eines von `recorded stage consistent`, `recorded stage questionable` und `insufficient evidence` liefern
- **MUSS [MUST]** bei `recorded stage questionable` eine `direction` von `ahead`, `behind` oder `unclear` tragen und bei den beiden anderen keine
- **MUSS [MUST]** `recorded stage consistent` und `recorded stage questionable` auf eine Beobachtung der gegenwärtigen Entwicklung der Pflanze der Stufe 1 bis 3 stützen oder auf eine Fotolesung, die eine zeitliche Erwartung bestätigt, und **MUSS [MUST]** diese Beobachtung nennen
- **MUSS [MUST]** das `typical_duration_days` der Phase, die Monatsfenster der Art, das `days_to_maturity` der Sorte und die Lebenszyklus-Fenster als zeitliche Erwartungen der Stufe 4 lesen, die **DÜRFEN NICHT [MUST NOT]** allein entscheiden, und eine Fotolesung als Lesung ohne Stufe, die **DARF NICHT [MUST NOT]** allein entscheiden
- **MUSS [MUST]** `insufficient evidence` liefern, wenn das erfasste Stadium fehlt, wenn keine Beobachtung der gegenwärtigen Entwicklung vorliegt oder wenn nur Vorannahmen, Ableitungen oder eine unbestätigte Fotolesung dazu etwas sagen, und **MUSS [MUST]** die Beobachtung nennen, die sie liefern würde
- **MUSS [MUST]** für ein fragliches Stadium `transition_plant_phase` als die Mutation nennen, die ein späterer Anwendungsschritt aufrufen würde, mit einer Zielphase nur dort, wo der Beleg eine nennt, und **DARF NICHT [MUST NOT]** es aufrufen
- **MUSS [MUST]** jedem Ergebnis seinen Beleg, seine Konfidenz, seine Unsicherheit und die fehlenden Daten geben, wie es die Entscheidungsrichtlinie verlangt

### C. Ableitungen

- **MUSS [MUST]** Wachstumsgradtage nur aus einer vom Aufrufer gelieferten täglichen Minimum- und Maximumreihe mit ihrer Einheit und dem `base_temp_gdd` der Art berechnen, die Methode und die Spanne nennen, die die Reihe abdeckt, und sie mit Grund als fehlend melden, wenn eine der Eingaben fehlt
- **DARF NICHT [MUST NOT]** Wachstumsgradtage aus einem einzelnen Wert, einem Home-Assistant-Schnappschuss oder einer Vorhersage berechnen und **DARF NICHT [MUST NOT]** ein Stadium allein aus aufsummierten Wachstumsgradtagen verorten, weil kein GDD-Ziel für ein Stadium oder für die Reife festgehalten ist
- **MUSS [MUST]** das Dampfdruckdefizit nur aus einer Temperatur und einer relativen Luftfeuchte berechnen, die zur selben Zeit am selben Ort genommen wurden, die Formel nennen, einen `measurements`-Schlüssel verwerfen, dessen Bedeutung oder Einheit mehrdeutig ist, und den Wert melden, ohne ihn an einem Zielwert zu messen, den keine der Quellen festhält
- **MUSS [MUST]** die Photoperiode draußen nur aus einem vom Aufrufer gelieferten Breitengrad und dem Beurteilungsdatum berechnen und drinnen nur aus dem Lichtplan des Aufrufers, und **MUSS [MUST]** die Reaktion der Art auf die Tageslänge als `no source` melden
- **MUSS [MUST]** jeder Ableitung `no level` geben und **MUSS [MUST]** sagen, dass `search_glossary` Definitionen liefert, keine Belege

### D. Wetterwirkung

- **MUSS [MUST]** Wetter und Vorhersage vom Aufrufer nehmen, mit `caller` gekennzeichnet, und **DARF [MAY]**, wo das Rezept es erlaubt, eine Wetter-Entität über `GetLiveContext` von Home Assistant lesen, wenn dieses Tool vorhanden ist, gemeldet als `home_assistant (unmeasured)`
- **MUSS [MUST]** jeden der Faktoren Temperaturextreme, Niederschlag, Wind, Luftfeuchte, Hitze- und Kälteereignisse und Vorhersageänderungen als genau eines von `exposure`, `no exposure in the supplied data` und `no source` melden
- **MUSS [MUST]** jeden Faktor als `no source` melden, wenn keine der beiden Quellen Daten geliefert hat, und **MUSS [MUST]** sagen, was die Beurteilung nicht schließen kann
- **MUSS [MUST]** einen Widerspruch zwischen dem Aufrufer und Home Assistant als Widerspruch mit beiden Quellen nebeneinander melden und **DARF NICHT [MUST NOT]** sie mitteln
- **MUSS [MUST]** Wetter als Stufe 6 lesen, **MUSS [MUST]** eine Exposition nur an einer Schwelle messen, die wörtlich aus dem Art- oder Phasendatensatz gelesen ist (Stufe 4) oder aus Allgemeinwissen stammt, das als Stufe 8 gekennzeichnet ist, mit ihrer Quelle und Stufe genannt, und **MUSS [MUST]** sonst sagen, dass keine Schwelle festgehalten ist und die Wirkung nicht beurteilt wird
- **MUSS [MUST]** für jede Exposition den Bereich nennen, den sie voraussichtlich betrifft (Pflege, Gesundheit oder Erntezeitpunkt), und **MUSS [MUST]** sie davon abhängig machen, wo die Pflanze steht, wenn der Aufrufer es nicht gesagt hat
- **DARF NICHT [MUST NOT]** eine Home-Assistant-Entität einer anderen Domäne oder irgendeinen Sensor als Beleg zu einer Pflanze verwenden

### E. Trennung von Exposition und Symptom

- **MUSS [MUST]** eine Wetterwirkung als Exposition oder erwartetes Risiko nennen und **DARF NICHT [MUST NOT]** sie als Symptom der Pflanze oder als Beleg zu ihrem gegenwärtigen Zustand nennen
- **MUSS [MUST]** ein Symptom nur aus `plant-photo-read`, einem Tagebucheintrag oder einer erfassten Inspektion nehmen und **MUSS [MUST]** Symptome in einem eigenen Block melden
- **MUSS [MUST]** ein Symptom mit einer Exposition nur als „consistent with“ verknüpfen, was nach Regel 1 der Entscheidungsrichtlinie ein Verdacht ist und nie eine Diagnose

### F. Einklinkform und Übergabe

- **MUSS [MUST]** neben dem Ergebnis Befunde in der Form liefern, die die Spezifikation zur Pflegeplanung in ihrem Abschnitt C festlegt
- **MUSS [MUST]** `recorded stage questionable` und eine Exposition, die an einer Schwelle der Stufe 4 gemessen ist, für eine Pflanze, die der Aufrufer draußen oder geschützt verortet, als Empfehlungen liefern und jedes andere Ergebnis als Beobachtung
- **MUSS [MUST]** die Folge eines Befunds fehlen lassen, wenn keine Eingabe eine nennt
- **MUSS [MUST]** einen Übergabeblock für die Ernteplanung liefern, der das erfasste und das geschätzte Stadium, das Ergebnis und seine Richtung, die Tage in der Phase gegen `typical_duration_days`, die Tage seit `planted_on` gegen das `days_to_maturity` der Sorte, die aufsummierten Wachstumsgradtage mit ihren Eingaben und die Photoperiode enthält, jedes mit Grund als fehlend, wo es fehlt
- **MUSS [MUST]** einen Übergabeblock für die Pflanzengesundheit liefern, der die Expositionen und, getrennt davon, die Symptome mit einer etwaigen „consistent with“-Verknüpfung enthält

### G. Determinismus

- **MUSS [MUST]** jedes Ergebnis zu einer Funktion der gelieferten Blöcke, der in Abschnitt B genannten Lesezugriffe und des in Abschnitt D genannten Schnappschusses machen, sodass zwei Läufe über dieselbe Eingabe dasselbe Ergebnis, dieselbe Richtung, dieselben Faktorstatus, dieselben Belegstufen und dieselbe Liste fehlender Daten ergeben
- **DARF NICHT [MUST NOT]** das aktuelle Datum innerhalb der Fakten lesen; Abrufzeiten stehen neben den Fakten und werden nicht verglichen
- **MUSS [MUST]** sagen, dass byte-identische Prosa außerhalb der Fakten nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage von als Text ausgeschriebenen Eingabeblöcken geprüft wird

### H. Trennung und verbotene Tools

- **MUSS [MUST]** beide Skills und beide Rezepte frei von jedem zustandsändernden Tool halten und **MUSS [MUST]** alle zwölf, die die Kamerplanter-Server-Spezifikation führt, einzeln im Prompt jedes Rezepts als verboten nennen
- **MUSS [MUST]** im Prompt des Wetterrezepts das Ansteuern in Home Assistant nach Kategorien verbieten (ein Gerät ein- oder ausschalten, einen Wert setzen, ein Skript, eine Szene oder eine Automatisierung ausführen) und **DARF NICHT [MUST NOT]** `TimeTillErnte` oder `time_till` aufrufen, deren Wirkung nicht eingeordnet ist
- **DARF NICHT [MUST NOT]** ein Home-Assistant-Tool aus dem Skill oder Rezept zum Wachstumsstadium oder aus der täglichen Prüfung aufrufen
- **DARF NICHT [MUST NOT]** ein `-apply`-Gegenstück zu einem der beiden Rezepte ausliefern

## Akzeptanzkriterien

- [ ] Ein Ergebnis zum Wachstumsstadium ist eines von `recorded stage consistent`, `recorded stage questionable` und `insufficient evidence`, und ein fragliches trägt eine Richtung von `ahead`, `behind` oder `unclear`
- [ ] Jedes Ergebnis zum Wachstumsstadium trägt Beleg und Konfidenz, und ein passendes oder fragliches nennt die Beobachtung der gegenwärtigen Entwicklung, auf der es ruht
- [ ] Eine unaufgelöste Phase wird als fehlendes erfasstes Stadium gemeldet, und der Phasenverlauf wird so gemeldet, wie er zurückkam
- [ ] Kein Stadium wird allein aus aufsummierten Wachstumsgradtagen, einer zeitlichen Erwartung oder einer unbestätigten Fotolesung verortet
- [ ] Wachstumsgradtage, Dampfdruckdefizit und Photoperiode werden berechnet, wenn ihre Eingaben geliefert sind, tragen `no level` und werden sonst mit Grund als fehlend gemeldet
- [ ] Jeder Wetterfaktor ist eines von `exposure`, `no exposure in the supplied data` und `no source`, und ohne Quelle ist jeder Faktor `no source` und das Ergebnis sagt, was nicht geschlossen werden kann
- [ ] Eine Home-Assistant-Wetterangabe ist als `home_assistant (unmeasured)` gekennzeichnet, und ein Widerspruch zum Aufrufer wird nebeneinander gemeldet, nicht gemittelt
- [ ] Wetterwirkungen erscheinen als Expositionen in einem Block, der von den Pflanzensymptomen getrennt ist, und eine Verknüpfung zwischen ihnen lautet „consistent with“
- [ ] Jedes Ergebnis nennt seine Unsicherheit und seine fehlenden Daten
- [ ] Jedes Ergebnis liefert Befunde in der Einklinkform der Pflegeplanung, dazu die benannten Übergabeblöcke für Pflanzengesundheit und Ernteplanung
- [ ] Ein fragliches Stadium nennt `transition_plant_phase` als Mutation, und nichts ruft es auf
- [ ] Zwei Läufe über dieselbe Eingabe ergeben an einer festen Vorlage dieselben Fakten, und das Ergebnis sagt, was nicht beansprucht wird
- [ ] Weder Skill noch Rezept ruft ein zustandsänderndes Tool auf, der Prompt jedes Rezepts verbietet alle zwölf namentlich, das Wetterrezept verbietet das Ansteuern nach Kategorien sowie `TimeTillErnte` und `time_till`, und das Rezept zum Wachstumsstadium ruft kein Home-Assistant-Tool auf
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl Anforderungspunkte und dieselbe Anzahl Akzeptanz-Checkboxen

## Quelle

- [Die Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, Wetter als Stufe 6, die sechs Regeln, Ableitungen ohne Stufe und die offene Frage zu einer globalen Rangordnung
- [Die Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) — die Einklinkform und die tägliche Prüfung
- [Die Spezifikation zur Artdaten-Prüfung](../species-baseline-verification/de.md) — `base_temp_gdd`, `days_to_maturity`, die Felder der Phasendefinition und die Drei-Quellen-Regel
- [Die Spezifikation zur bildgestützten Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md) — die offene Frage zu GDD ohne Temperaturverlauf
- [Die Spezifikation zu Entscheidungen über Bewässerung und Düngung](../watering-and-fertilization-decisions/de.md) — Wetter als vom Aufrufer gelieferte Eingabe und kein Home-Assistant-Sensor als Beleg zu einer Pflanze
- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Tool-Katalog, `get_plant_phase_status`, `get_plant_phase_history` und die zustandsändernden Tools, gemessen 2026-08-16
- [Die Spezifikation des Home-Assistant-MCP-Servers](../../mcp/home-assistant-mcp-server/de.md) — `GetLiveContext`, die Regel zum Ansteuern und die nicht eingeordneten `TimeTillErnte` und `time_till`, gemessen 2026-08-04
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie ein Rezept hier gebaut wird, einschließlich der namentlichen Verbote
- Issue nolte/kamerplanter-goose#49 — der Umfang und die fünf Akzeptanzkriterien stammen aus seinem Text; #48 und #50 — die Domänen, die die Übergabeblöcke lesen

## Offene Fragen

- **Die Quelle für Wetter und Vorhersage.** Der gemessene Kamerplanter-Katalog hat keine; bis er eine hat, liefert sie der Aufrufer, und Home Assistant ist eine zweite, nicht gemessene Quelle.
- **Ob Home Assistant eine Wetter-Entität bereitstellt, und ihre Form.** Nicht gemessen. Ein Aufruf von `GetLiveContext`, gefiltert auf `domain: weather`, an der Referenzinstanz würde es klären; bis dahin wird eine Angabe so gemeldet, wie sie zurückkam.
- **Ein GDD-Ziel für ein Stadium oder für die Reife.** Kein Feld hält eines fest, und die Reife der Sorte zählt Tage. Bis es eines gibt, sind aufsummierte Wachstumsgradtage Kontext und verorten kein Stadium.
- **Die Einheit von `base_temp_gdd`.** Die gemessenen Werte, 5,0 und 15,0, passen zu Grad Celsius; keine Spezifikation hält die Einheit fest. Die Beurteilung liest sie als Celsius und sagt das.
- **Ein Feld zur Photoperiodenempfindlichkeit.** An den beiden untersuchten Arten ist keines festgehalten. Ein Aufruf von `get_species_info` für eine Kurztagskultur würde zeigen, ob es eines gibt.
- **Die Antwortfelder von `get_plant_phase_history`.** Nicht festgehalten; ein Lesezugriff an einer erreichbaren Instanz würde sie klären, und bis dahin wird der Verlauf so gemeldet, wie er zurückkam.
- **Ob die Rangordnung bei Frost und Hitze global oder je Frage gilt.** Die Entscheidungsrichtlinie stellt Artdaten über das Wetter, und ein Frost ist eine Frage, bei der das Wetter entscheidet; diese Spezifikation ordnet nicht neu und trägt die Frage zur [Entscheidungsrichtlinie](../garden-decision-policy/de.md).
- **Wo die eigene Beobachtung einer Person an der Pflanze steht.** Sie wird hier als bestätigte Beobachtung gelesen, Stufe 3, mit `caller` gekennzeichnet; ob eine Aussage in einem Rezeptparameter das Gewicht einer erfassten Inspektion trägt, ist offen, wie die offene Frage der Entscheidungsrichtlinie zu Fotolesungen.
- **Der Wertebereich von `frost_sensitivity` und die Form von `stress_tolerance`.** Beide Felder sind als vorhanden festgehalten, ihre Werte nicht, daher wird eine daraus gelesene Schwelle so genannt, wie sie gelesen wurde, und ihre Bedeutung nicht angenommen.
