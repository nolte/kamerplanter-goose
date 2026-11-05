# Garten- und Saisonrückschau

Status: Entwurf
Portfolio-Scope: local

## Kontext

Eine Saison endet mit einer Frage, die nach hinten blickt und um der nächsten willen gestellt wird: Was hat funktioniert, was nicht, und was sollte sich ändern. Sie hat drei verlockende falsche Antworten. Eine Rückschau aus der Erinnerung an die Saison meldet, was die Person erwartet hat, statt was erfasst wurde. Eine Rückschau, die Pflege mit Ergebnis verknüpft („die Pflanze ist eingegangen, weil sie zu spät gedüngt wurde“), nennt eine Ursache, die kein Datensatz tragen kann. Eine Rückschau, die nur die noch lebenden Pflanzen sieht, verbirgt die gescheiterten. Diese Spezifikation legt fest, wie eine Rückschau auf einen Garten, bis zu einem Beurteilungsdatum oder über eine begrenzte Saison, aus erfasster Geschichte und Aussagen des Aufrufers zusammengesetzt wird, was über die Leistung von Sorten und über Pflegeergebnisse gesagt werden darf und in welcher Form die Rückschau ihr Ergebnis an den nächsten Planungszyklus übergibt.

Eine Rückschau ist hier eine Aussage an eine Person. Sie ändert nichts und speichert nichts: Keine Datei wird geschrieben und kein Tagebucheintrag hinzugefügt. Sie wird von einem werkzeugfreien Skill aus Blöcken zusammengesetzt, die andere Skills bereits gesammelt haben; der einzige zusätzliche Lesezugriff ist die Auflistung archivierter Pflanzen im Saisonumfang, unten genannt.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-16 und für diese Spezifikation nicht neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Fünf Tatsachen, auf denen die Anforderungen ruhen, wurden aus der Arbeitskopie gelesen und nicht gemessen: Historische Beobachtungen stammen aus `get_plant_inspections`, `list_diary_entries` und `get_plant_care_log` ([Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md), ihre Tabelle zum Gartenkontext); `list_plants` nimmt `include_archived` an, wie es `recipes/plant-master-data-check.yaml` und `.claude/skills/garden-context/SKILL.md` verwenden, doch der Parameter ist in der Server-Spezifikation nicht festgehalten; `diary-measurements-read` öffnet höchstens acht Einträge je Pflanze (`.claude/skills/diary-measurements-read/SKILL.md`), und die Signatur von `list_diary_entries` ist nicht gemessen, daher ist nicht bekannt, dass das Tagebuch einer Saison vollständig lesbar ist; kein Feld für Ertrag oder Erntemenge ist festgehalten (eine Suche in `spec/mcp` nach „yield“ findet keines); und die Planungsrezepte nehmen `crops`, `goals`, `harvest_window` und `constraints` als Zeichenketten des Aufrufers an (`recipes/garden-plan.yaml`, `recipes/crop-selection.yaml`).

Grenzen: Die [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln und die Form einer Empfehlung; diese Spezifikation nennt keine eigene Stufe. Die [Spezifikation zu Erntereife und Ernteplanung](../harvest-readiness-and-planning/de.md) besitzt jedes Ernteergebnis, das diese Rückschau übernimmt, und die [Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) jedes Ergebnis zum Wachstumsstadium und jede Wetterexposition; keine wird wiederholt. Der [Nährstoff-](../nutrient-imbalance-detection/de.md) und der [Schädlingsprozess](../pest-pressure-assessment/de.md) besitzen ihre Ergebnisse; eine Rückschau übernimmt sie nur, wenn der Aufrufer sie liefert. Die [Spezifikation zu Pflanzengesundheit und IPM-Planung](../plant-health-and-ipm-planning/de.md) besitzt den Befund der Pflanzengesundheit; eine Rückschau übernimmt ihn nur, wenn der Aufrufer ihn liefert, und führt ihn nie selbst aus. Die [Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) und die [Spezifikation zu Standortanalyse und Kulturwahl](../site-analysis-and-crop-selection/de.md) besitzen die Parameter, auf die der Block für den nächsten Zyklus zugeschnitten ist; sie werden nicht geändert. Fruchtfolge (nolte/kamerplanter-goose#47) ist keine Abhängigkeit. Das [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt, wie ein Rezept gebaut wird, einschließlich der namentlichen Verbote.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository und die Personen, die auf einen Garten oder eine Saison zurückblicken und dann die nächste planen.

## Ziele

- Eine Rückschau sagt je Pflanze, was erfasst wurde, was von der Person geliefert wurde und was fehlt, mit der Quelle von jedem
- Die Leistung von Sorten wird nebeneinander auf erfassten Feldern genannt, nie als Punktzahl oder als Durchschnitt über Einheiten hinweg
- Ein Pflegeergebnis wird mit der Pflege nur als „passt zu“ verknüpft, nie als Ursache
- Die Pflanzen, die gescheitert sind oder archiviert wurden, gehören zu einer Saisonrückschau, und die Grenzen dessen, was gelesen wurde, werden genannt
- Die Rückschau endet in einem Block, den der nächste Planungslauf als seine Parameter übernehmen kann, ohne dass etwas geschrieben wird

## Nicht-Ziele

- Eine Rückschau speichern, als Datei oder als Tagebucheintrag: kein `-apply`-Rezept
- Den gegenwärtigen Zustand einer Pflanze beurteilen: Die Rückschau führt keine eigene Nährstoff-, Schädlings-, Bewässerungs-, Dünge- oder Gesundheitsbeurteilung aus
- Die Pflanzengesundheit beurteilen oder Schädlingsmanagement planen (die Spezifikation zu Pflanzengesundheit und IPM-Planung), über die erfassten Inspektionen und vom Aufrufer gelieferte Ergebnisse hinaus
- Fruchtfolge (nolte/kamerplanter-goose#47); die Zeilen zur Standortgeschichte sind als Zeichenkette verträglich, wo Standortnamen Beetnamen entsprechen, und sind kein Vertrag
- Die Rückschau in die tägliche Gartenprüfung einbinden oder die Planungsspezifikationen ändern
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikation und sagen, dass sie nicht neu gemessen wurden

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** den Gartenkontext-Block von `garden-context`, die Pflanzenkontext-Blöcke von `plant-context-collect` (einschließlich Pflegeprotokoll und Inspektionen) und die Leseberichte von `diary-measurements-read` so übernehmen, wie sie sind, und **DARF [MAY]** Übergabeblöcke des Wachstumsstadiums und vom Aufrufer gelieferte Nährstoff- oder Schädlingsergebnisse so übernehmen, wie sie sind; die Rückschau-Rezepte **DÜRFEN NICHT [MUST NOT]** die Ernteplanung selbst ausführen
- **MUSS [MUST]** als vom Aufrufer geliefert, mit `caller` gekennzeichnet, nur Tatsachen annehmen, für die der Server keine Quelle hat: Erträge als `plant_key:amount unit`, Ernteergebnisse als `plant_key:<readiness result>[:YYYY-MM-DD]` (meist aus den Schlusszeilen von Prüfungen der Erntereife übernommen), Notizen zu einer Pflanze oder zur Saison, das Wetter der Saison und das Beurteilungsdatum, und **MUSS [MUST]** das Ernteergebnis einer Pflanze nur aus einem solchen Ernteergebnis füllen, sonst fehlt es
- **MUSS [MUST]** einen Ertrag des Aufrufers als Stufe 3 lesen, eine bestätigte Beobachtung, und dabei die offene Frage zum Gewicht einer Aussage des Aufrufers weitertragen, und **DARF NICHT [MUST NOT]** einen `measurements`-Schlüssel des Tagebuchs als Ertrag lesen
- **MUSS [MUST]** jede fehlende Eingabe als fehlend mit Grund melden, `no source` oder `not collected`, und **DARF NICHT [MUST NOT]** sie auffüllen

### B. Umfänge und Zeitspanne

- **MUSS [MUST]** zwei Umfänge anbieten: `garden`, den Garten bis zum Beurteilungsdatum, und `season`, eine begrenzte Zeitspanne
- **MUSS [MUST]** die Zeitspanne im Saisonumfang als Jahr `YYYY` annehmen, gelesen als `YYYY-01-01..YYYY-12-31`, oder als `YYYY-MM-DD..YYYY-MM-DD` mit einem Beginn nicht nach dem Ende, und **MUSS [MUST]** den Lauf anhalten und das Problem nennen, wenn die Zeitspanne fehlt oder ungültig ist
- **MUSS [MUST]** im Saisonumfang die Pflanzen des Gartens mit `include_archived: true` auflisten, die Auflistung als `complete`, `partial: <reason>` oder `failed: <error verbatim>` melden jede Pflanze so als `archived` oder `live` kennzeichnen, wie die Auflistung sie liefert, und **MUSS [MUST]** jede archivierte Pflanze der Auflistung melden, auch wenn Pflanzen genannt wurden
- **MUSS [MUST]** höchstens fünf genannte Pflanzen betrachten, die ersten fünf nach Pflanzenschlüssel als Text, und **MUSS [MUST]** die übrigen mit Grund als nicht betrachtet aufführen; ohne genannte Pflanzen **MUSS [MUST]** sie nur die Gartenebene betrachten und den Parameter nennen, der die Pflanzen liefern würde
- **MUSS [MUST]** je Pflanze den ältesten und den jüngsten geöffneten Tagebucheintrag gegenüber der Zeitspanne nennen und **MUSS [MUST]** sagen, wenn die Zeitspanne nicht abgedeckt ist, ohne weiter zu blättern

### C. Der Verlaufsdatensatz

- **MUSS [MUST]** je betrachteter Pflanze einen Datensatz liefern, geordnet nach Pflanzenschlüssel, mit festen Feldern: Pflanzenschlüssel, Artschlüssel, Sortenschlüssel, Standortname, `planted_on`, erfasste Phase, archiviert, Pflegebestätigungen je Erinnerungstyp, Aufschübe, Inspektionen, Tagebuchabdeckung, Wachstumsstadium, Ernteergebnis, Ertrag und Notizen
- **MUSS [MUST]** jedem Feld seine Quelle, Stufe und Abrufzeit geben, wenn es vorliegt, und seinen Grund, wenn es fehlt

### D. Leistung der Sorten

- **MUSS [MUST]** die betrachteten Pflanzen nach `species_key:cultivar_key` gruppieren und **MUSS [MUST]** die Felder jeder Gruppe nebeneinander nennen
- **DARF NICHT [MUST NOT]** eine Punktzahl, eine Rangfolge oder einen Durchschnitt über Einheiten hinweg berechnen und **MUSS [MUST]** zwei Sorten nur auf demselben Feld in derselben Einheit vergleichen

### E. Pflegeergebnisse und Lehren

- **MUSS [MUST]** Ergebnisse von Bewässerung und Düngung nur aus den Bestätigungen und Aufschüben des Pflegeprotokolls nehmen und **MUSS [MUST]** Pflege mit einem Ergebnis nur als „passt zu“ verknüpfen, nie als Ursache
- **MUSS [MUST]** die Schädlings-, Nährstoff- und Gesundheitsgeschichte nur aus den erfassten Inspektionen und vom Aufrufer gelieferten Ergebnissen nehmen, **MUSS [MUST]** einen gelieferten Befund der Pflanzengesundheit als die Beobachtung übernehmen, die er ist, und **MUSS [MUST]** die Pflanzengesundheit als `not supplied` melden, wenn keiner geliefert wurde
- **MUSS [MUST]** jeder Lehre genau eine Art geben: eine Beobachtung mit ihrer Quelle oder eine Empfehlung für den nächsten Zyklus mit den vier Blöcken der Entscheidungsrichtlinie, und **MUSS [MUST]** die Lehren nach Pflanzenschlüssel, dann Feld, dann Art nummerieren, nie nach dem Text der Aussage
- **MUSS [MUST]** eine Empfehlung auf mindestens einen Posten der Stufe 1 bis 3 oder eine Aussage des Aufrufers stützen und **DARF NICHT [MUST NOT]** sie allein auf Allgemeinwissen stützen

### F. Der Block für den nächsten Zyklus

- **MUSS [MUST]** `crops` im Format liefern, das die Planungsrezepte annehmen (`species_key[:cultivar_key]`, durch Kommas getrennt), jede Kultur gekennzeichnet mit `keep`, `reconsider` oder `no evidence` und dem Beleg, auf dem das ruht: `reconsider`, wenn ein Posten der Stufe 1 bis 3 oder eine Aussage des Aufrufers ein Problem festhält, mit Vorrang vor `keep`; `keep` nur, wenn der Aufrufer einen Erfolg meldet (einen Ertrag, den der Aufrufer als Erfolg kennzeichnet, oder eine Notiz) und kein Problem festgehalten ist; sonst `no evidence`, auch für eine bloße Ertragszahl
- **MUSS [MUST]** `goals` als freien Text liefern, nur aus den Lehren und den Notizen des Aufrufers gezogen, `constraints` als freien Text, der nur erfasste oder vom Aufrufer genannte Beobachtungen zu Standort und Umgebung trägt und nie eine Lehre, und `harvest_window` in den Monatsworten des Aufrufers, nur aus Ernteergebnissen und Aussagen des Aufrufers gezogen, jedes mit Grund als fehlend, wenn nichts es liefert; `;` und `:` sind reservierte Trennzeichen in den Parametern des Aufrufers, und freier Text, der sie enthält, wird wörtlich und ungeparst gemeldet
- **MUSS [MUST]** Zeilen zur Standortgeschichte `location_name:season:species_key[:cultivar_key]` liefern, gekennzeichnet mit „location, not bed“
- **DARF NICHT [MUST NOT]** den Block irgendwohin schreiben; er wird als Text übergeben

### G. Determinismus

- **MUSS [MUST]** die Rückschau zu einer Funktion der gelieferten Blöcke und, im Saisonumfang, der in Abschnitt B genannten Auflistung machen, sodass zwei Läufe über dieselbe Eingabe dieselben Datensätze, Gruppen, Lehren, Arten, Zeichenketten für den nächsten Zyklus und Fehlliste liefern
- **DARF NICHT [MUST NOT]** das aktuelle Datum in die Fakten lesen; Abrufzeiten werden neben den Fakten gemeldet und nicht verglichen
- **MUSS [MUST]** sagen, dass byte-gleiche Prosa außerhalb der Fakten nicht zugesichert wird und dass die Eigenschaft an einer festen, als Text ausgeschriebenen Vorlage von Eingabeblöcken geprüft wird

### H. Trennung und verbotene Tools

- **MUSS [MUST]** den Skill werkzeugfrei halten, sodass er nur mit den Blöcken arbeitet, die ihm übergeben werden
- **MUSS [MUST]** den Skill und beide Rezepte frei von jedem zustandsändernden Tool halten und **MUSS [MUST]** jedes, das die Kamerplanter-Server-Spezifikation aufführt, einzeln im Prompt jedes Rezepts als verboten nennen
- **DARF NICHT [MUST NOT]** ein Home-Assistant-Tool aufrufen und **DARF NICHT [MUST NOT]** ein `-apply`-Geschwister eines der beiden Rezepte ausliefern

## Akzeptanzkriterien

- [ ] Eine Rückschau hat den Umfang `garden` oder `season`, und eine fehlende oder ungültige Saisonspanne hält den Lauf an und nennt das Problem
- [ ] Eine Saisonrückschau listet archivierte Pflanzen auf, auch wenn Pflanzen genannt sind, meldet die Auflistung als vollständig, teilweise oder fehlgeschlagen und kennzeichnet jede Pflanze als archiviert oder lebend
- [ ] Höchstens fünf Pflanzen werden betrachtet, ausgewählt nach Pflanzenschlüssel als Text, die übrigen werden als nicht betrachtet genannt, und ohne Pflanzen wird nur die Gartenebene betrachtet
- [ ] Jede betrachtete Pflanze hat einen Verlaufsdatensatz mit den festen Feldern, geordnet nach Pflanzenschlüssel, jedes vorhanden mit seiner Quelle oder fehlend mit seinem Grund
- [ ] Die Tagebuchabdeckung wird gegenüber der Zeitspanne genannt, und eine Zeitspanne, die der Tagebuch-Lesezugriff nicht abdeckt, wird benannt
- [ ] Ertrag kommt nur vom Aufrufer, auf Stufe 3, und kein Tagebuchschlüssel wird als Ertrag gelesen
- [ ] Die Leistung der Sorten steht nebeneinander, ohne Punktzahl, Rangfolge oder Durchschnitt, und zwei Sorten werden nur auf demselben Feld in derselben Einheit verglichen
- [ ] Kein Pflegeergebnis wird als durch Pflege verursacht genannt; eine Verknüpfung lautet „passt zu“
- [ ] Ein gelieferter Befund der Pflanzengesundheit wird als Beobachtung übernommen und nie neu ausgeführt; ohne ihn wird die Pflanzengesundheit als `not supplied` gemeldet, und die Rückschau führt keine Beurteilung des gegenwärtigen Zustands aus
- [ ] Jede Lehre ist eine Beobachtung oder eine Empfehlung mit Beleg, Konfidenz, Unsicherheit und fehlenden Daten
- [ ] Der Block für den nächsten Zyklus trägt `crops`, `goals`, `constraints` und `harvest_window` in den Formaten der Planungsrezepte, `reconsider` hat Vorrang vor `keep`, `keep` braucht einen vom Aufrufer gemeldeten Erfolg, `constraints` trägt keine Lehre, und Zeilen zur Standortgeschichte sind mit „location, not bed“ gekennzeichnet
- [ ] Nichts wird geschrieben: keine Datei, kein Tagebucheintrag
- [ ] Zwei Läufe über dieselbe Eingabe liefern an einer festen Vorlage dieselben Fakten, und das Ergebnis sagt, was nicht zugesichert wird
- [ ] Der Skill ruft kein Tool auf, keines der Rezepte ruft ein zustandsänderndes oder ein Home-Assistant-Tool auf, der Prompt jedes Rezepts verbietet jedes zustandsändernde Tool namentlich, und kein `-apply`-Geschwister wird ausgeliefert
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl an Anforderungspunkten und dieselbe Anzahl an Akzeptanz-Checkboxen

## Quelle

- [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, die sechs Regeln, die Ausgabe einer Empfehlung und die Quellen historischer Beobachtungen
- [Spezifikation zu Erntereife und Ernteplanung](../harvest-readiness-and-planning/de.md) — die Ernteergebnisse, die eine Rückschau übernimmt
- [Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) — die Übergabe des Wachstumsstadiums und die Wetterexpositionen
- [Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) — der Umgang mit noch nicht gebauten Domänen als nicht verfügbar und die Obergrenze von fünf Pflanzen
- [Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) und [Spezifikation zu Standortanalyse und Kulturwahl](../site-analysis-and-crop-selection/de.md) — die Planungsparameter, auf die der Block für den nächsten Zyklus zugeschnitten ist
- [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Tool-Katalog und die zustandsändernden Tools
- [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie hier ein Rezept gebaut wird, einschließlich der namentlichen Verbote
- Issue nolte/kamerplanter-goose#50 — Umfang und Akzeptanzkriterien stammen aus seinem Text; #47 und #48 — die Domänen, von denen diese Rückschau nicht abhängt

## Offene Fragen

- **Ob `list_plants` `include_archived` annimmt und was eine archivierte Pflanze trägt.** Von zwei Dateien hier verwendet und in der Server-Spezifikation nicht festgehalten; ob ein Archivierungsdatum geliefert wird, ist nicht festgehalten. Ein Lesezugriff auf eine erreichbare Instanz würde beides klären.
- **Wie viel vom Tagebuch einer Saison lesbar ist.** Höchstens acht Einträge werden je Pflanze geöffnet, und die Signatur der Auflistung ist nicht gemessen; bis sie es ist, wird die Abdeckung genannt statt angenommen.
- **Eine Quelle für Ertrag.** Keine ist festgehalten; bis eine existiert, ist Ertrag eine Aussage des Aufrufers auf Stufe 3.
- **Wo die Aussage einer Person steht.** Als Stufe 3 gelesen, mit `caller` gekennzeichnet, und trägt die offene Frage weiter, die die Spezifikation zum Wachstumsstadium festhält.
- **Ob eine Rückschau gespeichert werden sollte.** Ein `-apply`-Geschwister mit Tagebucheintrag wäre eine Folgearbeit, sobald sich die Regel zu Schreibzugriffen ändert.
- **Ob die Standortgeschichte zur Beetgeschichte wird.** Nur, wenn die Arbeit zur Fruchtfolge (nolte/kamerplanter-goose#47) einen Vertrag festlegt; bis dahin sind die Zeilen mit „location, not bed“ gekennzeichnet.
- **Ob fünf Pflanzen die richtige Obergrenze für eine Saison sind.** Aus der täglichen Prüfung übernommen, nicht an der Größe eines Gartens gemessen.
