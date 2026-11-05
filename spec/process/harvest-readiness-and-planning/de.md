# Erntereife und Ernteplanung

Status: Entwurf
Portfolio-Scope: local

## Kontext

„Ist sie reif?“ ist die Frage, die eine Gärtnerin oder ein Gärtner gegen Ende einer Kultur am häufigsten stellt, und sie hat zwei verlockende falsche Antworten. Die eine liest die Antwort vom Kalender ab: Die Art wird im August geerntet, es ist August, also ist die Pflanze reif. Die andere liest sie vom Alter der Pflanze ab: Die Sorte reift in 75 Tagen, 75 Tage sind vergangen, also ist sie reif. Keine sieht die Pflanze an, und die zweite ruht auf einer Zählung, deren Startpunkt niemand festgehalten hat. Ein Ernteplan über mehrere Pflanzen fügt drei weitere Versuchungen hinzu: einen Ertrag, den niemand gemessen hat, eine Lagergrenze, die niemand festgehalten hat, und eine Arbeitsschätzung, die niemand geliefert hat. Diese Spezifikation legt fest, worauf ein Urteil zur Erntereife ruhen darf, welche geschlossene Menge an Antworten es geben darf, wie eine Wartezeit vor der Ernte (Karenz) es sperrt und wie ein Ernteplan Pflanzen ordnet und Arbeit zählt, ohne eine Quelle für Ertrag, Lagerung oder Aufwand.

Ein Urteil ist hier eine Aussage an eine Person. Es ändert nichts: Nichts wird geerntet, erfasst oder eingeplant. Es wird aus Blöcken getroffen, die andere Skills bereits gesammelt haben, zuzüglich höchstens zweier unten genannter Lesezugriffe je Pflanze.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-16, und aus der [Spezifikation des Home-Assistant-MCP-Servers](../../mcp/home-assistant-mcp-server/de.md), gemessen am 2026-08-04; keine wurde für diese Spezifikation neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Sechs Tatsachen, auf denen die Anforderungen ruhen, wurden aus der Arbeitskopie gelesen und nicht gemessen: `get_harvest_readiness` ist ein Lese-Tool im Katalog (die Zeile „Care and tasks“ der Server-Spezifikation), es wurde am 2026-08-16 lesend aufgerufen, und seine Argumente und Antwortfelder sind nirgends festgehalten (eine Suche in `spec/`, `.claude/`, `recipes/` und `tests/` findet den Namen nur in der Katalogzeile und in jener Quellenzeile); `get_treatment` trägt `safety_interval_days`, die Karenz vor der Ernte (ihre Signaturtabelle); die Ernte-Schreib-Tools sind upstream spezifiziert, aber nicht umgesetzt, und keines gehört zu den zwölf zustandsändernden Tools (ihre Nicht-Ziele und Anforderungen); kein Feld für Ertrag, Erntemenge, Lagerung oder Haltbarkeit ist festgehalten (eine Suche in `spec/mcp` nach „yield“ und in `spec/` und `.claude/skills/` nach „storage“ findet keines); kein Datensatz, wann eine Behandlung ausgebracht wurde, ist beschrieben (das Pflegeprotokoll ist nur durch `reminder_type` und `confirmed_at` beschrieben, [Spezifikation zur Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md)); und `TimeTillErnte` und `time_till` auf der Home-Assistant-Referenzinstanz sind nicht eingestufte eigene Intents.

Grenzen: Die [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln und die Form einer Empfehlung; diese Spezifikation nennt keine eigene Stufe. Die [Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) besitzt das Ergebnis zum Wachstumsstadium, den Übergabeblock für die Ernteplanung (ihr Abschnitt F) und die Wetterexpositionen; diese Spezifikation übernimmt sie, wie sie geliefert werden, und wiederholt ihre Regeln nicht. Die [Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) besitzt die Regel für das Erntefenster und das Verbot eines Erntedatums aus `days_to_maturity`. Die [Spezifikation zur Beurteilung des Schädlingsdrucks](../pest-pressure-assessment/de.md) besitzt, welche Behandlung ein Schädling verlangt; diese Spezifikation liest nur die Wartezeit einer Behandlung, die laut Aufrufer ausgebracht wurde. Die [Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) besitzt die Einklinkform eines Befunds. Das [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt, wie ein Rezept gebaut wird, einschließlich der namentlichen Verbote.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Autorin oder der Autor der Garten- und Saisonrückschau (ihre Spezifikation liest die hier festgelegten Ergebnisse) und die Personen, die eine Ernteprüfung ausführen und lesen, bevor sie ernten.

## Ziele

- Ein Ergebnis zur Erntereife sagt, ob eine Pflanze reif ist, sich der Reife nähert, nicht reif ist, nicht erntbar ist oder ob es unbekannt ist, mit seinem Beleg und seiner Konfidenz, und sagt offen, wenn über die Pflanze selbst nichts bekannt ist
- Der Kalender und das Alter der Pflanze werden als Erwartungen verwendet, nie als Antwort, und kein Erntedatum wird aus einer Zählung berechnet, deren Startpunkt nicht festgehalten ist
- Eine Wartezeit vor der Ernte sperrt eine Ernte, wenn der Aufrufer sagt, dass eine Behandlung ausgebracht wurde, und sagt, dass sie nicht prüfbar ist, wenn er das nicht sagt
- Ein Ernteplan ordnet Pflanzen deterministisch und zählt die Arbeit, die er zählen kann, ohne einen Ertrag, eine Lagergrenze oder eine Aufwandsschätzung zu erfinden
- Unsicherheit ist ausdrücklich: was jedes Ergebnis nicht weiß und was es ändern würde

## Nicht-Ziele

- Eine Ernte, einen Ertrag oder eine Behandlung erfassen: kein `-apply`-Rezept. Upstream führt die Ernte-Schreib-Tools als spezifiziert, aber nicht umgesetzt, und keines ist im gemessenen Katalog
- Eine Behandlung empfehlen oder Schädlings- oder Krankheitsdruck beurteilen; das ist die [Beurteilung des Schädlingsdrucks](../pest-pressure-assessment/de.md), und Pflanzengesundheit ist nolte/kamerplanter-goose#48
- Das Wachstumsstadium oder das Wetter beurteilen; das ist die [Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md)
- Die Erntereife in die tägliche Gartenprüfung einbinden
- Eine Tabelle von Reifemerkmalen je Art, ein Lagermodell oder ein Ertragsmodell: Keines hat eine Quelle
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikationen und sagen, dass sie nicht neu gemessen wurden

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** den Pflanzenkontext-Block von `plant-context-collect` so übernehmen, wie er ist, und **DARF NICHT [MUST NOT]** ein Tool aufrufen, um zu holen, was er schon enthält; **DARF [MAY]** den Leseberichts-Block und die Messwerte von `diary-measurements-read`, die Befunde von `plant-photo-read`, die Beurteilung des Wachstumsstadiums mit ihrem Übergabeblock für die Ernteplanung, die Wetterbefunde und den Gartenkontext-Block von `garden-context` so übernehmen, wie sie sind
- **MUSS [MUST]** als vom Aufrufer geliefert, mit `caller` gekennzeichnet, nur Tatsachen annehmen, für die der Server keine Quelle hat: die eigene Beobachtung der Person an der Pflanze, die vorgesehene Verwendung, Wetter und Vorhersage, die ausgebrachten Behandlungen als `treatment_key:YYYY-MM-DD`, die Lagerbedingungen, die verfügbare Erntekapazität und das Beurteilungsdatum
- **MUSS [MUST]** das Beurteilungsdatum vom Aufrufer nehmen oder, ohne eines, so, wie die Beurteilung des Wachstumsstadiums es festgelegt hat, **MUSS [MUST]** weder die Position im Monatsfenster noch die Erntesperre berechnen, wenn die eigene Beobachtung der Person ohne ein Beurteilungsdatum vom Aufrufer geliefert wird, beide als `not computed (observation undated)` melden und dafür nie auf ein älteres Tagebuchdatum zurückgreifen, und **DARF NICHT [MUST NOT]** das aktuelle Datum lesen
- **MUSS [MUST]** jede fehlende Eingabe als fehlend mit Grund melden, `no source` oder `not collected`, und **DARF NICHT [MUST NOT]** sie auffüllen

### B. Das Ergebnis zur Erntereife

- **MUSS [MUST]** genau eines von `ready`, `approaching`, `not ready`, `not harvestable` und `insufficient evidence` liefern
- **MUSS [MUST]** `not harvestable` liefern, wenn der Artdatensatz `allows_harvest: false` trägt, und **MUSS [MUST]** dann nichts weiter über die Reife urteilen
- **MUSS [MUST]** `ready`, `approaching` und `not ready` auf ein beobachtetes Reifemerkmal der Stufe 1 bis 3 stützen (ein Tagebuch-Messwert, eine erfasste Inspektion oder die eigene Beobachtung der Person, mit `caller` gekennzeichnet) oder auf eine Fotolesung, die eine zeitliche Erwartung bestätigt, **MUSS [MUST]** dieses Merkmal nennen und **MUSS [MUST]** die Konfidenz eines Ergebnisses, das auf einer Fotolesung und einer Vorannahme der Stufe 4 ruht, als `level 4 prior + photo reading (level 3 corroboration)` angeben
- **MUSS [MUST]** das Monatsfenster aus den `harvest_months` des gewählten Eintrags von `growing_periods[]`, die Position gegenüber `days_to_maturity` und Ergebnis und Richtung des Wachstumsstadiums als Vorannahmen der Stufe 4 lesen, die **DÜRFEN NICHT [MUST NOT]** allein entscheiden, und eine Fotolesung als Lesung ohne Stufe, die **DARF NICHT [MUST NOT]** allein entscheiden
- **MUSS [MUST]** `insufficient evidence` liefern, wenn `allows_harvest` fehlt, wenn kein Reifemerkmal vorliegt oder wenn nur Vorannahmen oder eine unbestätigte Fotolesung etwas zur Reife sagen, und **MUSS [MUST]** die Beobachtung nennen, die es liefern würde
- **MUSS [MUST]** ein verwendungsbezogenes Merkmal (etwa für die Lagerung oder für die Saatgutgewinnung) nur vom Aufrufer oder als Allgemeinwissen der Stufe 8, gekennzeichnet als nicht aus dem Datenbestand, nennen und **DARF NICHT [MUST NOT]** es allein entscheiden lassen
- **MUSS [MUST]** jedem Ergebnis seinen Beleg, seine Konfidenz, seine Unsicherheit und die fehlenden Daten geben, wie es die Entscheidungsrichtlinie verlangt

### C. Zeitliche Vorannahmen

- **MUSS [MUST]** das Erntefenster nur aus den `harvest_months` des zutreffenden Eintrags von `growing_periods[]` nehmen und sagen, welcher es ist, und **DARF NICHT [MUST NOT]** die Monate der obersten Ebene verwenden, wenn Perioden vorhanden sind
- **MUSS [MUST]** die Tage seit `planted_on` gegenüber dem `days_to_maturity` der Sorte als Position führen, **MUSS [MUST]** sagen, dass weder festgehalten ist, ab wann `days_to_maturity` zählt, noch was `planted_on` bezeichnet, und **DARF NICHT [MUST NOT]** daraus ein Erntedatum berechnen
- **MUSS [MUST]** die Position des Wachstumsstadiums aus dem Übergabeblock so übernehmen, wie sie geliefert wird, und **MUSS [MUST]** sie mit Grund als fehlend melden, wenn die Beurteilung des Wachstumsstadiums nicht lief
- **MUSS [MUST]** die aufsummierten Wachstumsgradtage aus dem Übergabeblock mit ihren Eingaben als Vorannahme mit `no level` führen, **MUSS [MUST]** `GDD target for maturity: no source` nennen und **DARF NICHT [MUST NOT]** sie entscheiden lassen

### D. Lesezugriffe

- **MUSS [MUST]** `get_harvest_readiness` einmal je Pflanze, nur mit der Pflanze und dem Garten, aufrufen, wenn das Tool vorhanden ist, und **MUSS [MUST]** ein fehlendes Tool als ausdrückliches Ergebnis mit seinem Namen melden; **MUSS [MUST]** seine Antwort so melden, wie sie zurückkam, ohne einen Feldnamen anzunehmen und ohne eine Stufe zuzuweisen, und **MUSS [MUST]** einen `validation.error` wörtlich melden und ohne ihn weitermachen
- **MUSS [MUST]** `get_treatment` für jede vom Aufrufer gelieferte Behandlung aufrufen, und nur für diese, und **MUSS [MUST]** nur ihr `safety_interval_days` lesen

### E. Wetter und Wartezeit

- **MUSS [MUST]** Wetter nur vom Aufrufer nehmen, über die Beurteilung der Wetterwirkung ohne Home-Assistant-Lesezugriff, und **MUSS [MUST]** nur Expositionen, deren Wirkung den Erntezeitpunkt betrifft, in die Erntereife einfließen lassen, als Risiko und nie als Reifemerkmal
- **MUSS [MUST]** über dem Ergebnis eine Erntesperre melden: `blocked until <date>`, wenn das Datum einer ausgebrachten Behandlung zuzüglich ihres `safety_interval_days` nach dem Beurteilungsdatum liegt, `unknown (<reason>)`, wenn keine Behandlung sperrt und die Wartezeit irgendeiner gelieferten Behandlung unbekannt ist (ihr Lesezugriff schlug fehl oder sie trägt kein `safety_interval_days`), `clear` nur, wenn die Wartezeit jeder gelieferten Behandlung bekannt und abgelaufen ist, und `unknown (no treatment date supplied)` ohne Behandlungsangabe, mit dem Vorrang `blocked` vor `unknown` vor `clear`
- **DARF NICHT [MUST NOT]** aus dem Pflegeprotokoll, den Inspektionen oder dem Tagebuch schließen, dass eine Behandlung ausgebracht wurde oder nicht

### F. Der Ernteplan

- **MUSS [MUST]** für höchstens fünf genannte Pflanzen planen, die ersten fünf nach Pflanzenschlüssel als Text, **MUSS [MUST]** die übrigen mit Grund als nicht geplant aufführen und **MUSS [MUST]** eine Pflanze, die nicht gelesen werden kann, als `not planned (<error verbatim>)` aufführen
- **MUSS [MUST]**, wenn keine Pflanzen genannt sind, die Kulturen und Pflanzläufe des Gartens aus dem Gartenkontext nur als Kontext melden, kein Fenster und keine Erntereife berechnen und den Parameter nennen, der die Pflanzen liefern würde
- **MUSS [MUST]** die geplanten Pflanzen nach dem Startmonat des Fensters ordnen, eine Pflanze mit unbekanntem Fenster nach jeder bekannten, dann nach Erntereife (`ready`, `approaching`, `not ready`, `insufficient evidence`, `not harvestable`), dann nach Pflanzenschlüssel, sodass die Ordnung eine totale Ordnung auf dem Inhalt ist; der Fensterbeginn ist der Kalendermonat des ersten Fenstermonats innerhalb der Saison, daher wird ein Fenster, das die Jahresgrenze überschreitet, nach diesem Kalendermonat eingeordnet
- **MUSS [MUST]** die Arbeitslast als Pflanzen je Startmonat des Fensters und Pflanzen mit `ready` oder `approaching` zählen, **MUSS [MUST]** Stunden oder Aufwand nur aus einer vom Aufrufer gelieferten Kapazität nennen und **MUSS [MUST]** „über der Kapazität“ nur dann nennen, wenn diese Kapazität in derselben Einheit wie die Zählungen angegeben ist
- **MUSS [MUST]** Lager- und Verwendungsbedingungen als `not modeled in the measured catalog` melden, sofern der Aufrufer sie nicht geliefert hat, und sie dann mit `caller` kennzeichnen
- **MUSS [MUST]** die Erntesperre jeder Pflanze in den Plan übernehmen und **DARF NICHT [MUST NOT]** eine gesperrte Pflanze vor ihrem Sperrdatum als erntbar einordnen

### G. Einklinkform

- **MUSS [MUST]** neben dem Ergebnis oder dem Plan Befunde in der Form liefern, die die Spezifikation zur Pflegeplanung in ihrem Abschnitt C festlegt
- **MUSS [MUST]** `ready` und `approaching`, die auf einem Merkmal der Stufe 1 bis 3 ruhen, als Empfehlungen ausgeben und jedes andere Ergebnis als Beobachtung
- **MUSS [MUST]** die Folge eines Befunds fehlen lassen, sofern keine Eingabe eine nennt, und **MUSS [MUST]** die Mutation als `no tool measured` nennen, weil der Katalog kein Ernte-Schreib-Tool enthält

### H. Determinismus

- **MUSS [MUST]** jedes Ergebnis und die Reihenfolge des Plans zu einer Funktion der gelieferten Blöcke und der in Abschnitt D genannten Lesezugriffe machen, sodass zwei Läufe über dieselbe Eingabe dieselben Ergebnisse, Sperren, Reihenfolge, Belegstufen und Fehlliste liefern
- **DARF NICHT [MUST NOT]** das aktuelle Datum in die Fakten lesen; Abrufzeiten werden neben den Fakten gemeldet und nicht verglichen
- **MUSS [MUST]** sagen, dass byte-gleiche Prosa außerhalb der Fakten nicht zugesichert wird und dass die Eigenschaft an einer festen, als Text ausgeschriebenen Vorlage von Eingabeblöcken geprüft wird

### I. Trennung und verbotene Tools

- **MUSS [MUST]** den Skill und beide Rezepte frei von jedem zustandsändernden Tool halten und **MUSS [MUST]** alle zwölf, die die Kamerplanter-Server-Spezifikation aufführt, einzeln im Prompt jedes Rezepts als verboten nennen
- **DARF NICHT [MUST NOT]** ein Home-Assistant-Tool aus dem Skill oder einem der Rezepte aufrufen und **MUSS [MUST]** `TimeTillErnte` und `time_till` im Prompt jedes Rezepts als verboten nennen, weil sie der verlockendste falsche Ersatz sind und ihre Wirkung nicht eingestuft ist
- **DARF NICHT [MUST NOT]** ein `-apply`-Geschwister eines der beiden Rezepte ausliefern

## Akzeptanzkriterien

- [ ] Ein Ergebnis zur Erntereife ist eines von `ready`, `approaching`, `not ready`, `not harvestable` und `insufficient evidence`
- [ ] Ein Ergebnis `ready`, `approaching` oder `not ready` nennt das Reifemerkmal der Stufe 1 bis 3 oder die bestätigte Fotolesung, auf dem es ruht
- [ ] Kein Ergebnis ruht allein auf den Erntemonaten, der Position gegenüber `days_to_maturity`, den aufsummierten Wachstumsgradtagen, dem Wachstumsstadium oder einer Fotolesung, und eine undatierte Beobachtung berechnet keine Position im Monatsfenster und keine Sperre
- [ ] Kein Erntedatum wird aus `days_to_maturity` berechnet, und das Erntefenster stammt aus den `harvest_months` der gewählten Wachstumsperiode
- [ ] Die Antwort von `get_harvest_readiness` wird so gemeldet, wie sie zurückkam, ohne Stufe und ohne angenommenes Feld, und ein Fehler daraus hält den Lauf nicht an
- [ ] Wetter kommt nur vom Aufrufer, nur als Risiko für den Erntezeitpunkt, und kein Home-Assistant-Tool wird aufgerufen
- [ ] Die Erntesperre ist `blocked until <date>`, `unknown (<reason>)` oder `clear`, in diesem Vorrang, ist nur dann `clear`, wenn die Wartezeit jeder gelieferten Behandlung bekannt ist, und ruht nur auf `get_treatment` und vom Aufrufer gelieferten Daten
- [ ] Ein Ernteplan umfasst höchstens fünf Pflanzen, ausgewählt nach Pflanzenschlüssel als Text, nennt die übrigen und jede nicht lesbare Pflanze als nicht geplant und meldet ohne Pflanzen nur den Gartenkontext
- [ ] Die Reihenfolge des Plans ist Fensterstart, dann Erntereife, dann Pflanzenschlüssel, und ändert sich nicht, wenn sich die Reihenfolge der Eingabe ändert
- [ ] Die Arbeitslast besteht nur aus Zählungen, sofern der Aufrufer keine Kapazität geliefert hat, und die Lagerung ist `not modeled in the measured catalog`, sofern der Aufrufer sie nicht geliefert hat
- [ ] Jedes Ergebnis nennt Beleg, Konfidenz, Unsicherheit und fehlende Daten und liefert Befunde in der Einklinkform der Pflegeplanung
- [ ] Zwei Läufe über dieselbe Eingabe liefern an einer festen Vorlage dieselben Fakten, und das Ergebnis sagt, was nicht zugesichert wird
- [ ] Weder der Skill noch ein Rezept ruft ein zustandsänderndes Tool auf, der Prompt jedes Rezepts verbietet alle zwölf namentlich sowie `TimeTillErnte` und `time_till`, und kein `-apply`-Geschwister wird ausgeliefert
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl an Anforderungspunkten und dieselbe Anzahl an Akzeptanz-Checkboxen

## Quelle

- [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, die sechs Regeln und die Ausgabe einer Empfehlung
- [Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) — Abschnitt F, der Übergabeblock für die Ernteplanung, und die Wetterexpositionen mit dem Wirkungsbereich Erntezeitpunkt
- [Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) — das Erntefenster aus `harvest_months[]` der gewählten Wachstumsperiode und kein Erntedatum aus `days_to_maturity`
- [Spezifikation zur Beurteilung des Schädlingsdrucks](../pest-pressure-assessment/de.md) — die Wartezeit als Karenz vor der Ernte
- [Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) — die Einklinkform eines Befunds und die Obergrenze von fünf Pflanzen
- [Spezifikation zur Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md) — die Felder des Pflegeprotokolls
- [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — `get_harvest_readiness`, `get_treatment` mit `safety_interval_days`, die nicht umgesetzten Ernte-Schreibzugriffe und die zwölf zustandsändernden Tools, gemessen 2026-08-16
- [Spezifikation des Home-Assistant-MCP-Servers](../../mcp/home-assistant-mcp-server/de.md) — die nicht eingestuften `TimeTillErnte` und `time_till`, gemessen 2026-08-04
- [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie hier ein Rezept gebaut wird, einschließlich der namentlichen Verbote
- Issue nolte/kamerplanter-goose#50 — Umfang und Akzeptanzkriterien stammen aus seinem Text

## Offene Fragen

- **Die Argumente und Antwortfelder von `get_harvest_readiness`.** Am 2026-08-16 einmal aufgerufen und nirgends festgehalten. Ein Lesezugriff auf eine erreichbare Instanz würde sie klären; bis dahin übergibt der Aufruf nur die Pflanze und den Garten, und die Antwort wird gemeldet, wie sie zurückkam.
- **Ab wann `days_to_maturity` zählt.** Aussaat oder Auspflanzen ist nicht festgehalten, ebenso wenig, ob `planted_on` eines davon bezeichnet. Bis dahin ist der Reifevergleich eine Position, nie ein Datum.
- **Eine Quelle für Ausbringungsdaten von Behandlungen.** Kein beschriebenes Feld hält fest, wann eine Behandlung ausgebracht wurde; ob ein `reminder_type` im Pflegeprotokoll eine Behandlung nennen kann, ist nicht festgehalten. Bis eine existiert, liefert der Aufrufer das Datum.
- **Eine Quelle für Ertrag, Lagerung und Aufwand.** Keine ist festgehalten. Bis eine existiert, besteht die Arbeitslast aus Zählungen und die Lagerung aus Text des Aufrufers.
- **Wo die eigene Beobachtung der Reife durch eine Person steht.** Sie wird hier als bestätigte Beobachtung gelesen, Stufe 3, mit `caller` gekennzeichnet, und trägt die offene Frage weiter, die die Spezifikation zum Wachstumsstadium bereits festhält.
- **Ob `TimeTillErnte` oder `time_till` eine Erntefrage beantwortet.** Nicht eingestuft; der Betreiber müsste sie einstufen, bevor ein Rezept sie liest.
- **Ob fünf Pflanzen die richtige Obergrenze sind.** Aus der täglichen Prüfung übernommen, nicht gemessen.
