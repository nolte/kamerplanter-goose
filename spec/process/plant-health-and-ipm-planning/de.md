# Pflanzengesundheit und IPM-Planung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Eine Pflanze, die falsch aussieht, lädt zu einer einzigen Antwort ein: „Es ist Stickstoffmangel“, „es sind Spinnmilben“, „der Frost hat sie erwischt“. Jede Domäne in diesem Repository beantwortet schon eine engere Frage gut, und jede verweigert die Antwort, wenn der Beleg dünn ist: [Der Nährstoffprozess](../nutrient-imbalance-detection/de.md) lässt eine Richtung unterhalb seiner Schwelle unbestimmt, [der Schädlingsprozess](../pest-pressure-assessment/de.md) nennt einen überlebenden Kandidaten *nicht widerlegt* statt *bestimmt*, und [die Wetterbeurteilung](../growth-stage-and-weather-impact/de.md) hält eine Exposition von einem Symptom getrennt. Was keine von ihnen tut, ist, die Kandidaten-Erklärungen für eine Pflanze nebeneinanderzustellen, zu sagen, welche überleben, und zu sagen, was die Überlebenden unterscheiden würde. Eine Schicht, die das schlecht macht, macht die Sorgfalt der Domänen zunichte: Sie mittelt eine Vermutung und einen gestützten Befund zu einer selbstsicheren „Diagnose“, oder sie zählt denselben Nährstoffbefund doppelt. Und sobald ein Schädlings- oder Krankheitskandidat überlebt, ordnet noch nichts, was dagegen zu tun ist, vom genaueren Hinsehen bis zu einer gezielten Behandlung, mit der Wartezeit und den Voraussetzungen der Behandlung.

Diese Spezifikation legt zwei Dinge fest. Eine **Beurteilung der Pflanzengesundheit** fasst, was die bestehenden Skills für eine Pflanze bereits geliefert haben, zu einer Differenzialbetrachtung zusammen: eine feste Menge von Kandidatenklassen, jede mit genau einem Status, und ein Gesamtergebnis, nie eine Diagnose. Ein **IPM-Plan** nimmt einen Schädlings- oder Krankheitskandidaten so, wie der Schädlingsprozess ihn hinterlassen hat, und ordnet die Maßnahmen in vier Stufen; eine gezielte Behandlung erreicht er nur an der eigenen Schwelle des Schädlingsprozesses und nur mit ihren Sicherheitsauflagen und Voraussetzungen.

Eine Beurteilung oder ein Plan ist hier eine Aussage an eine Person. Sie ändert nichts. Die Gesundheitsbeurteilung macht keinen eigenen Lesezugriff; der IPM-Plan macht höchstens die in Abschnitt D genannten Katalog-Lesezugriffe.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-07 und am 2026-08-16, und wurde für diese Spezifikation nicht neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Fünf Tatsachen, auf denen die Anforderungen ruhen, wurden aus der Arbeitskopie gelesen und nicht gemessen: `get_pest` trägt verschachtelt `treatments[]` mit `treatment_key`, `name`, `treatment_type`, `active_ingredient`, `application_method`, `safety_interval_days`, `dosage_per_liter` und `protective_equipment[]` sowie `beneficials[]` mit `preys_on[]`, festgehalten an einem Schädling ([der Schädlingsprozess](../pest-pressure-assessment/de.md), „Der Katalog, und wo er endet“); `get_disease` trägt `environmental_triggers[]`, und `get_pest` trägt kein Feld zu Luftfeuchte, Wirtsspektrum oder Überwachung (derselbe Abschnitt); keine Spezifikation hält den Wertebereich von `treatment_type` fest (eine Suche in `spec/` und `.claude/` nach `treatment_type` findet nur Zeilen mit dem Feldnamen); keine Spezifikation hält die Antwortfelder von `get_harvest_readiness` fest, und auch nicht die von `get_plant_inspections` an einer inspizierten Pflanze (die Server-Spezifikation nennt das erste nur in ihrer Katalogtabelle, und der Schädlingsprozess führt das zweite als offene Frage); und `create_inspection` steht im gemessenen Schreibkatalog, während kein Tool darin steht, das eine Behandlung festhält (die Schreibtabelle der Server-Spezifikation), obwohl die Nicht-Ziele der Server-Spezifikation IPM-Schreibtools noch als nicht umgesetzt führen (Offene Fragen).

Abgrenzung: [Die Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln (Regel 1, nie aus einem einzelnen Symptom diagnostizieren; Regel 5, eine Umweltursache korrigieren, bevor die Pflanze behandelt wird) und die Form einer Empfehlung; diese Spezifikation nennt keine eigene Stufe. [Der Schädlingsprozess](../pest-pressure-assessment/de.md) besitzt die Bestimmung, ihre Belegleiter, die Falsifikationstests, die Behandlungsschwelle und die Prüfungen zu Nützlingen, Wartezeit und Wirkstoffwechsel; diese Spezifikation zitiert sie und wiederholt keine. [Der Nährstoffprozess](../nutrient-imbalance-detection/de.md) besitzt die Nährstoffrichtung. [Die Spezifikation zur bildgestützten Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md) besitzt die Foto-Warteschlange und ihren Claim-und-Submit-Zyklus, einen Schreibzyklus; diese Spezifikation besitzt nur die lesende Zusammenschau und übernimmt Fotobefunde so, wie sie sind. [Die Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) besitzt das Wachstumsstadium, die Expositionen und ihre Übergabe an die Pflanzengesundheit. [Die Spezifikation zur Pflegeplanung](../care-planning-and-daily-check/de.md) besitzt die Einklinkform eines Befunds und die tägliche Prüfung, die diese Beurteilungen ausführt. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt, wie ein Rezept gebaut wird, einschließlich der namentlichen Verbote, und warum die Zusammensetzung in einem Rezept geschieht statt über Unterrezepte.

Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository und die Personen, die eine Gesundheitsbeurteilung oder einen IPM-Plan lesen, bevor sie an einer Pflanze handeln.

## Ziele

- Mehrere Belegquellen werden zu einem Bild der Gesundheit einer Pflanze zusammengefasst, und jede Kandidaten-Erklärung sagt, worauf sie ruht
- Konkurrierende Erklärungen bleiben nebeneinander stehen, wenn der Beleg sie nicht trennt, mit der Beobachtung, die es täte
- Konfidenz und Unsicherheit sind für jeden Kandidaten und für das Ergebnis als Ganzes ausdrücklich
- Die bestehenden Diagnose-Skills werden wiederverwendet, und kein Urteil einer Domäne wird neu ausgeführt, aufgewertet oder doppelt gezählt
- Ein IPM-Plan bevorzugt Bestätigung, dann Umweltkorrektur, dann kulturelle und mechanische Maßnahmen, und erreicht eine gezielte Behandlung nur, wenn die Schwelle des Schädlingsprozesses erreicht ist
- Jede Behandlung in einem Plan trägt ihre Sicherheitsauflagen und Voraussetzungen, aus dem Datenbestand zitiert, und wird ausgeschlossen, wenn sie sich nicht prüfen lassen

## Nicht-Ziele

- Etwas festhalten: kein `-apply`-Rezept, kein Inspektionseintrag, kein Behandlungseintrag. Ein Schritt, den ein späterer Anwendungsschritt festhalten würde, nennt die Mutation und ruft nichts auf
- Einen Schädling oder eine Krankheit bestimmen, eine Nährstoffrichtung beurteilen, ein Foto lesen, das Wachstumsstadium oder das Wetter beurteilen: Das gehört den eigenen Prozessen, die diese Schicht zusammensetzt
- Ernteplanung (nolte/kamerplanter-goose#50), über die Zeit bis zur Ernte hinaus, die die Sicherheitsprüfung braucht
- Eine Tabelle von Unverträglichkeiten zwischen Behandlungen, von Wirtsspektren, von Überwachungsmethoden oder eine Zuordnung von `treatment_type` zu einer Stufe: Keine hat eine Quelle im Datenbestand
- Das veraltete Nicht-Ziel der Server-Spezifikation berichtigen, das IPM-Schreibtools als nicht umgesetzt führt (Offene Fragen)
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikation und sagen, dass sie nicht neu gemessen wurden

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** für die Gesundheitsbeurteilung den Pflanzenkontext-Block von `plant-context-collect` (der das Pflegeprotokoll, die Inspektionen, die Art- und Sortendaten und die Phase bereits enthält), den Lesebericht und die Messwerte von `diary-measurements-read`, das Ergebnis und die Übergaben von `growth-stage-assessment`, die Übergabe an die Pflanzengesundheit von `weather-impact-analysis` und die Berichte von `nutrient-imbalance-assess` und `pest-pressure-assess` übernehmen, jeweils so, wie sie geliefert wurden
- **DARF [MAY]** für die Gesundheitsbeurteilung die Befunde von `plant-photo-read` übernehmen, wenn der Aufrufer einen Tagebucheintrag mit Fotos nennt, und die Befunde von `watering-decision` und `fertilization-decision`, jeweils so, wie sie geliefert wurden
- **MUSS [MUST]** aus dem Skill der Gesundheitsbeurteilung keinen Tool-Aufruf machen: Alles, was er verwendet, steht in den Blöcken, die er bekommt
- **MUSS [MUST]** für den IPM-Plan den Bericht von `pest-pressure-assess` so übernehmen, wie er geliefert wurde, und **DARF [MAY]** die IPM-Übergabe der Gesundheitsbeurteilung und die Ernte-Übergabe von `growth-stage-assessment` übernehmen
- **MUSS [MUST]** als vom Aufrufer geliefert, mit `caller` gekennzeichnet, nur Tatsachen annehmen, für die der Server keine Quelle hat: die eigene Beobachtung der Person an der Pflanze, den zu prüfenden Verdacht, das Wetter, wo die Pflanze steht (geschlossen oder offen, draußen, geschützt oder drinnen), das geplante Erntedatum und das Beurteilungsdatum, und **DARF NICHT [MUST NOT]** das aktuelle Datum lesen
- **MUSS [MUST]** jede fehlende Eingabe als fehlend mit Grund melden, `not collected` oder `no source`, und **DARF NICHT [MUST NOT]** sie auffüllen

### B. Die Differenzialbetrachtung

- **MUSS [MUST]** genau diese Kandidatenklassen betrachten: `nutrient`, `pest`, `disease`, `water`, `environment`, `development` und `abiotic handling/site`
- **MUSS [MUST]** jedem Kandidaten genau einen Status geben: `supported`, `suspicion`, `contradicted` oder `not assessable`
- **MUSS [MUST]** `supported` nur geben, wenn die zuständige Domäne ihr eigenes positives Ergebnis geliefert hat und mindestens ein weiteres Belegstück, das nicht das auffällige Symptom ist, ihn stützt, ohne Widerspruch auf einer höheren Stufe
- **MUSS [MUST]** `suspicion` einem Kandidaten geben, der nur auf einem einzelnen Symptom, einer Fotolesung, Vorannahmen oder einer „consistent with“-Verknüpfung ruht, `contradicted` einem Kandidaten, dem das eigene negative Ergebnis der zuständigen Domäne oder ein benanntes Belegstück einer höheren Stufe widerspricht, und `not assessable` einem Kandidaten, dessen Domäne nicht lief oder nichts lieferte, mit dem Grund
- **MUSS [MUST]** genau ein Gesamtergebnis liefern: `leading explanation`, `competing explanations`, `suspicion only`, `no abnormality reported` oder `insufficient evidence`
- **DARF NICHT [MUST NOT]** das Ergebnis einer Domäne aufwerten: Ein Schädlingskandidat, den der Schädlingsprozess `not contradicted` ließ, bleibt `not contradicted`, eine Nährstoffrichtung, die er unbestimmt ließ, bleibt unbestimmt, und die Gesundheitsschicht führt keine Leiter, keinen Falsifikationstest und keine Verweigerungsschwelle eines anderen Prozesses erneut aus
- **DARF NICHT [MUST NOT]** ein Ergebnis eine Diagnose nennen und **MUSS [MUST]** einen Kandidaten, der auf einem Symptom ruht, als Vermutung kennzeichnen, wie Regel 1 der Entscheidungsrichtlinie es verlangt

### C. Konfidenz und Unsicherheit

- **MUSS [MUST]** jedem Kandidaten seine Belegeinträge (Stufe, Quelle, Abrufzeit), seine Konfidenz aus der höchsten Stufe der Entscheidungsrichtlinie, die ihn stützt, seine Unsicherheit und seine fehlenden Daten geben und **MUSS [MUST]** sagen, dass keine Stufe gilt, wenn keine gilt
- **MUSS [MUST]** für jedes Paar überlebender Kandidaten die Beobachtung nennen, die zwischen ihnen unterscheiden würde
- **MUSS [MUST]** die Stufen der Domänenberichte aus der Tabelle „Wie sich die bestehenden Leitern verhalten“ der Entscheidungsrichtlinie lesen und **DARF NICHT [MUST NOT]** eine Stufe vergeben, wo diese Tabelle keine nennt
- **MUSS [MUST]** einen eigenen Widerspruch oder eine eigene Verweigerung einer Domäne so in das Ergebnis tragen, wie die Domäne sie genannt hat, und **DARF NICHT [MUST NOT]** einen Widerspruch zwischen zwei Domänen zugunsten der flüssiger klingenden auflösen

### D. IPM-Stufen

- **MUSS [MUST]** einen IPM-Plan in genau diesen vier Stufen ordnen, in dieser Reihenfolge: Bestätigung und Überwachung; Umweltkorrektur; kulturelle und mechanische Maßnahmen; gezielte Behandlung
- **DARF NICHT [MUST NOT]** einen Kandidaten bestimmen oder die Falsifikationstests des Schädlingsprozesses erneut ausführen und **MUSS [MUST]** nur für einen Kandidaten planen, den der Schädlingsbericht nennt, mit dem Status und der Stufe, die der Bericht gab
- **MUSS [MUST]** die eigenen Lesezugriffe des Plans auf `get_pest` und `get_disease` für die Kandidatenschlüssel, die der Schädlingsbericht nennt, auf `get_treatment` für einen Behandlungsschlüssel, den diese Datensätze nennen, und auf `search_glossary` für einen Begriff beschränken und **MUSS [MUST]** `treatments[]`, `beneficials[]` und `environmental_triggers[]` so zitieren, wie sie zurückkamen
- **MUSS [MUST]** die Stufe der gezielten Behandlung nur erreichen, wenn die Behandlungsschwelle des Schädlingsprozesses erreicht ist, und **MUSS [MUST]** unterhalb davon nach der Stufe der kulturellen und mechanischen Maßnahmen enden und die Überwachungsmethode nennen, die den Beleg anheben würde, gekennzeichnet als Allgemeinwissen, das nicht im Datenbestand steht
- **MUSS [MUST]** für eine Umweltkorrektur gegen eine Krankheit `environmental_triggers` zitieren und **MUSS [MUST]** eine gegen einen Schädling als Allgemeinwissen kennzeichnen, das nicht im Datenbestand steht, weil der Schädlingsdatensatz keine Feuchte-Ökologie trägt
- **MUSS [MUST]** die Stufe der gezielten Behandlung biologisch vor chemisch ordnen, eine Nützlingsfreilassung dort einordnen und die Schonung natürlicher Gegenspieler im offenen Bereich in der kulturellen Stufe, und jeden Nützling gegen `preys_on` prüfen, wie der Schädlingsprozess es verlangt
- **MUSS [MUST]** einen Wert von `treatment_type`, den er keiner Stufe zuordnen kann, als „stage not determinable from the record“ melden, weil der Wertebereich nicht festgehalten ist, und **DARF NICHT [MUST NOT]** die Stufe raten
- **MUSS [MUST]** „no pest or disease candidate“ als gültigen leeren Plan liefern, wenn der Schädlingsbericht keinen nennt

### E. Voraussetzungen und Sicherheitsauflagen einer Behandlung

- **MUSS [MUST]** jeder Maßnahme in der Stufe der gezielten Behandlung einen Block der Voraussetzungen geben: Die Bestimmung erreicht die Schädlingsschwelle, mit benannter Stufe; jede frühere Stufe ist erledigt oder nicht verfügbar, mit dem Grund; und die Erntesituation, `allows_harvest` und die Zeit bis zur Ernte
- **MUSS [MUST]** die Zeit bis zur Ernte nur aus dem geplanten Erntedatum des Aufrufers oder aus der Ernte-Übergabe des Wachstumsstadiums nehmen (Tage seit `planted_on` gegen `days_to_maturity`) und **DARF NICHT [MUST NOT]** sie aus `get_harvest_readiness` nehmen, dessen Antwortfelder nicht festgehalten sind
- **MUSS [MUST]** jeder solchen Maßnahme einen Block der Sicherheitsauflagen geben, der `safety_interval_days`, `protective_equipment[]`, `dosage_per_liter`, `application_method` und `active_ingredient` wörtlich aus dem Datenbestand zitiert, und **DARF NICHT [MUST NOT]** einen davon skalieren, umrechnen oder erfinden
- **MUSS [MUST]** eine Maßnahme ausschließen, deren `safety_interval_days` die verbleibende Zeit bis zur Ernte übersteigt, und **MUSS [MUST]** eine Maßnahme als „not recommendable: interval cannot be checked“ melden, wenn `allows_harvest` wahr ist und die Zeit bis zur Ernte nicht feststeht
- **DARF NICHT [MUST NOT]** zwei Maßnahmen mit demselben `active_ingredient` als Alternativen anbieten und **MUSS [MUST]** sagen, dass die Aussage zum Wirkstoffwechsel nicht getroffen werden kann, wo `active_ingredient` `null` ist
- **MUSS [MUST]** den Konflikt zwischen einer Nützlingsfreilassung und einer breit wirkenden Maßnahme als nicht festgehalten nennen, und das Produktetikett und die örtlichen Pflanzenschutzregeln als Voraussetzung außerhalb des Datenbestands
- **MUSS [MUST]** den geschlossenen oder offenen Bereich vom Aufrufer nehmen oder als erschlossen nennen, wie der Schädlingsprozess es verlangt

### F. Trennung von Exposition und Symptom

- **MUSS [MUST]** Wetter nur über die Übergabe an die Pflanzengesundheit der Wetterbeurteilung in die Gesundheitsbeurteilung nehmen und **MUSS [MUST]** die Expositionen in einem eigenen Block halten, getrennt von den Symptomen
- **MUSS [MUST]** ein Symptom mit einer Exposition nur als „consistent with“ verknüpfen, was den Kandidaten `environment` eine Vermutung bleiben lässt, wie es [die Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) in Abschnitt E verlangt

### G. Einklinkform und Arten

- **MUSS [MUST]** neben dem Ergebnis Befunde in der Form liefern, die die Spezifikation zur Pflegeplanung in ihrem Abschnitt C festlegt
- **MUSS [MUST]** die Gesundheitsbeurteilung nur als Beobachtungen liefern, ein Befund je Pflanze mit der Differenzialbetrachtung, der die Befunde der anderen Domänen nach Domäne zitiert und keine ihrer Empfehlungen wiederholt
- **MUSS [MUST]** einen Übergabeblock für den IPM-Plan liefern, der die Kandidaten `environment` und `water` und den Schädlings- oder Krankheitskandidaten so enthält, wie der Schädlingsbericht ihn geliefert hat
- **MUSS [MUST]** einem Überwachungsschritt für einen vorhandenen Kandidaten die Art Empfehlung geben, einem Umwelt- oder Kulturschritt die Art Empfehlung nur, wenn der Kandidat im Schädlingsbericht mindestens `not contradicted` ist, und sonst Beobachtung, und einer gezielten Behandlung die Art Empfehlung nur, wenn die Schwelle erreicht ist und jede Voraussetzung gilt
- **MUSS [MUST]** die Folge eines Befunds fehlen lassen, wenn keine Eingabe eine nennt
- **MUSS [MUST]** das Tool zum Festhalten einer Inspektion, `create_inspection`, als die Mutation nennen, die ein späterer Anwendungsschritt für einen Überwachungsschritt aufrufen würde, und `no tool measured` für eine Behandlung, und **DARF NICHT [MUST NOT]** eines davon aufrufen

### H. Determinismus

- **MUSS [MUST]** jedes Ergebnis zu einer Funktion der gelieferten Blöcke und der in Abschnitt D genannten Lesezugriffe machen, sodass zwei Läufe über dieselbe Eingabe dieselben Kandidatenstatus, dasselbe Gesamtergebnis, dieselben Stufen, dieselben Ausschlüsse, dieselben Belegstufen und dieselbe Liste fehlender Daten ergeben
- **DARF NICHT [MUST NOT]** das aktuelle Datum innerhalb der Fakten lesen; Abrufzeiten stehen neben den Fakten und werden nicht verglichen
- **MUSS [MUST]** sagen, dass byte-identische Prosa außerhalb der Fakten nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage von als Text ausgeschriebenen Eingabeblöcken geprüft wird

### I. Trennung und verbotene Tools

- **MUSS [MUST]** beide Skills und beide Rezepte frei von jedem zustandsändernden Tool halten und **MUSS [MUST]** alle zwölf, die die Kamerplanter-Server-Spezifikation führt, einzeln im Prompt jedes Rezepts als verboten nennen
- **DARF NICHT [MUST NOT]** aus einem der beiden Skills oder Rezepte ein Home-Assistant-Tool aufrufen und **MUSS [MUST]** im Prompt jedes Rezepts das Ansteuern nach Kategorien verbieten (ein Gerät ein- oder ausschalten, einen Wert setzen, ein Skript, eine Szene oder eine Automatisierung ausführen) sowie `TimeTillErnte` und `time_till`, deren Wirkung nicht eingeordnet ist
- **MUSS [MUST]** die Unter-Skills im Rezept zusammensetzen, nach Namen, und **DARF NICHT [MUST NOT]** sich auf `sub_recipes:` oder `--sub-recipe` verlassen, die unter dem Provider `claude-code` nicht funktionieren
- **DARF NICHT [MUST NOT]** ein `-apply`-Gegenstück zu einem der beiden Rezepte ausliefern

## Akzeptanzkriterien

- [ ] Eine Gesundheitsbeurteilung fasst Kontext, Messwerte, Wachstumsstadium, Wetterexpositionen und die Nährstoff- und Schädlingsberichte zusammen und nennt jede fehlende Eingabe mit ihrem Grund
- [ ] Jede Kandidatenklasse trägt genau eines von `supported`, `suspicion`, `contradicted` und `not assessable`, und das Ergebnis ist genau eines der fünf Gesamtergebnisse
- [ ] Zwei überlebende Kandidaten werden nebeneinander als `competing explanations` gemeldet, mit der Beobachtung, die zwischen ihnen unterscheiden würde
- [ ] Kein Ergebnis wird Diagnose genannt, und kein Kandidat, der auf einem Symptom ruht, ist mehr als eine Vermutung
- [ ] Jeder Kandidat nennt seinen Beleg, seine Konfidenz, seine Unsicherheit und seine fehlenden Daten
- [ ] Kein Ergebnis einer Domäne wird aufgewertet, erneut ausgeführt oder wiederholt: Der Gesundheitsbefund ist eine Beobachtung, die die Domänen nach Namen zitiert
- [ ] Wetter kommt nur als Expositionen hinein, getrennt von Symptomen gehalten und nur als „consistent with“ verknüpft
- [ ] Ein IPM-Plan hat die vier Stufen in Reihenfolge und erreicht eine gezielte Behandlung nur an der Schwelle des Schädlingsprozesses
- [ ] Unterhalb der Schwelle nennt der Plan eine Überwachungsmethode, als nicht festgehalten gekennzeichnet
- [ ] Jede gezielte Behandlung trägt ihre Voraussetzungen und ihre wörtlich zitierten Sicherheitsauflagen und wird ausgeschlossen oder nicht empfehlbar, wenn ihre Wartezeit die Zeit bis zur Ernte übersteigt oder sich nicht daran prüfen lässt
- [ ] Keine zwei Maßnahmen mit demselben Wirkstoff werden als Alternativen angeboten, und ein nicht zuordenbares `treatment_type` wird als solches gemeldet
- [ ] Beide Skills liefern Befunde in der Einklinkform der Pflegeplanung, und ein Überwachungsschritt nennt `create_inspection` als Mutation, die nichts aufruft
- [ ] Zwei Läufe über dieselbe Eingabe ergeben an einer festen Vorlage dieselben Fakten, und das Ergebnis sagt, was nicht beansprucht wird
- [ ] Weder Skill noch Rezept ruft ein zustandsänderndes Tool oder ein Home-Assistant-Tool auf, und der Prompt jedes Rezepts verbietet alle zwölf zustandsändernden Tools namentlich, das Ansteuern nach Kategorien sowie `TimeTillErnte` und `time_till`
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl Anforderungspunkte und dieselbe Anzahl Akzeptanz-Checkboxen

## Quelle

- [Die Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, die sechs Regeln, die Ausgabe einer Empfehlung und die Tabelle „Wie sich die bestehenden Leitern verhalten“
- [Die Spezifikation zur Beurteilung des Schädlingsdrucks](../pest-pressure-assessment/de.md) — die Belegleiter, die Behandlungsschwelle, die Falsifikationstests, die Prüfungen zu Nützlingen, Wartezeit und Wirkstoffwechsel sowie die gemessenen Schädlings- und Krankheitsdatensätze
- [Die Spezifikation zur Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md) — die Nährstoffrichtung und ihre Verweigerungsschwelle
- [Die Spezifikation zur bildgestützten Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md) — die Fotolesung und ihr Schreibzyklus, den diese Spezifikation nicht besitzt
- [Die Spezifikation zu Wachstumsstadium und Wetterwirkung](../growth-stage-and-weather-impact/de.md) — das Wachstumsstadium, seine Ernte-Übergabe und die an die Pflanzengesundheit übergebenen Expositionen
- [Die Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) — die Einklinkform und die tägliche Prüfung
- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Tool-Katalog, `get_pest`, `get_disease`, `get_treatment`, `create_inspection` und die zustandsändernden Tools, gemessen 2026-08-07 und 2026-08-16
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie ein Rezept hier gebaut wird, die namentlichen Verbote und warum keine Unterrezepte verwendet werden
- Issue nolte/kamerplanter-goose#48 — der Umfang, die IPM-Reihenfolge und die fünf Akzeptanzkriterien stammen aus seinem Text

## Offene Fragen

- **Der Wertebereich von `treatment_type`.** Nicht festgehalten. Bis ein Aufruf von `get_pest` über mehrere Schädlinge ihn zeigt, wird ein Wert nur dort einer Stufe zugeordnet, wo seine Bedeutung offensichtlich ist, und sonst als „stage not determinable from the record“ gemeldet.
- **Die Felder von `get_plant_inspections` an einer inspizierten Pflanze.** Nur an einem leeren Verlauf gemessen. Eine gefüllte Antwort würde klären, ob eine Befallsstärke mehr als einen benannten Organismus in die Differenzialbetrachtung tragen kann.
- **Eine Quelle für Unverträglichkeiten zwischen Behandlungen.** Keine ist festgehalten; der Konflikt zwischen einer Freilassung und einer breit wirkenden Maßnahme bleibt Allgemeinwissen, bis das Backend, das Glossar oder eine zitierte Quelle ihn trägt.
- **Rechtliche und Etikett-Auflagen.** Produktzulassung, Etikettbedingungen und örtliche Pflanzenschutzregeln stehen nicht im Datenbestand. Ein Plan nennt sie als Voraussetzung außerhalb davon; ob eine Quelle für sie hierher gehört, ist offen.
- **Ob das Gesundheitsergebnis je eine Empfehlung sein darf.** Es ist hier eine Beobachtung, damit der Pflegeplan keine Empfehlung einer Domäne doppelt zählt. Eine Empfehlung, die der Zusammenschau eigen ist, etwa „die Blattunterseiten ansehen“, trägt stattdessen die unterscheidende Beobachtung; ob das eine Empfehlung werden soll, ist offen.
- **Das veraltete Nicht-Ziel der Server-Spezifikation.** Ihre Nicht-Ziele führen IPM-Schreibtools als spezifiziert, aber nicht umgesetzt, während ihre eigene Schreibtabelle `create_inspection` als gemessen festhält. Eine Folgearbeit sollte das berichtigen; diese Spezifikation tut es nicht.
- **Ob der Hinweis „gleichmäßiger Schaden über mehrere Pflanzen“ der Foto-Checkliste je Pflanze verfügbar ist.** Er deutet auf eine abiotische Ursache, aber eine Beurteilung einer einzelnen Pflanze sieht eine Pflanze. Der erste Live-Lauf über mehrere Pflanzen würde zeigen, ob er in den Kandidaten `abiotic handling/site` eingehen kann.
