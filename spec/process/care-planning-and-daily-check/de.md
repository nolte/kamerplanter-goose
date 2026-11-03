# Pflegeplanung und die tägliche Gartenprüfung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Ein Garten hält viele kleine Fragen zugleich: Welche Pflanzen sind fällig, welche sehen falsch aus, welche brauchen nichts. Jede Domäne in diesem Repository beantwortet eine davon für eine Pflanze: Der [Nährstoffprozess](../nutrient-imbalance-detection/de.md) sagt, in welche Richtung ein Nährstoffungleichgewicht läuft, der [Schädlingsprozess](../pest-pressure-assessment/de.md) sagt, ob ein Schädlingskandidat seine Tests übersteht. Nichts stellt diese Antworten bisher nebeneinander, sagt, welche eine Person zuerst ansehen sollte, und sagt offen, wenn es nichts zu tun gibt. Diese Spezifikation beschreibt diese Schicht, die Pflegeplanung, und das Rezept, das sie täglich ausführt, die tägliche Gartenprüfung.

Die Schicht entscheidet nichts über eine Pflanze. Sie liest, was der Gartenkontext und die Domänenprozesse bereits geliefert haben, hält Beobachtung, Empfehlung und Mutation auseinander, ordnet die Empfehlungen und weigert sich, eine Handlung zu erzeugen, wo der Beleg zum gegenwärtigen Zustand fehlt. Eine Person liest das Ergebnis; nichts wird angewendet.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-16 und für diese Spezifikation nicht neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Die Formen der bestehenden Domänenberichte wurden aus `.claude/skills/nutrient-imbalance-assess/SKILL.md` (§5 Report) und `.claude/skills/pest-pressure-assess/SKILL.md` (§5 Report) gelesen; keiner liefert heute einen strukturierten Befund, deshalb bildet Abschnitt C sie ab. Die Bewässerungs- und die Düngeentscheidung liefern Befunde selbst in dieser Form ([ihre Spezifikation](../watering-and-fertilization-decisions/de.md), Abschnitt F). Keine Spezifikation in diesem Repository hält die Antwortfelder von `get_due_care_tasks` fest (eine Suche in `spec/`, `docs/` und `recipes/` findet den Namen des Tools und kein Feld), deshalb berechnet Abschnitt D kein Überfälligkeitsintervall.

Grenzen: Die [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln, die Form einer Empfehlung und den Gartenkontext-Block; diese Spezifikation wendet sie an und nennt keine eigene Stufe. Die [Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) besitzt den Plan, den diese Schicht lesen darf (ihre Verbrauchertabelle nennt die Pflegeplanung). Der [Nährstoff-](../nutrient-imbalance-detection/de.md) und der [Schädlingsprozess](../pest-pressure-assessment/de.md) behalten ihre eigenen Leitern und Verweigerungsschwellen; diese Schicht ordnet sie nicht neu.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Autorinnen und Autoren der Domänen für Bewässerung, Düngung, Gesundheit und Wetter, die sich in diese Schicht einklinken werden, und alle, die eine tägliche Prüfung lesen, bevor sie handeln.

## Ziele

- Eine Leserin oder ein Leser bekommt eine geordnete Liste dessen, was anzusehen ist, und jeder Eintrag sagt, worauf er ruht, wie sicher er ist und was ihn ändern würde
- Beobachtung, Empfehlung und Mutation werden nie verwechselt: Man erkennt, was gelesen wurde, was vorgeschlagen wird und was den Zustand ändern würde
- Ein Zustand ohne Beleg ergibt keine Handlung, und das Ergebnis nennt die Beobachtung, die ihn liefern würde
- Eine Domäne klinkt sich ein, indem sie Befunde in einer Form liefert, und eine Domäne, die es noch nicht gibt, wird als nicht verfügbar gemeldet und nie ersetzt
- Die tägliche Prüfung dupliziert keine Domänenlogik und ruft kein zustandsänderndes Tool auf

## Nicht-Ziele

- Die Domänen selbst: Pflanzengesundheit und Schädlingsmanagement (nolte/kamerplanter-goose#48), Wachstumsstadium und Wetter (#49). Bewässerung und Düngung sind in der [Spezifikation zu den Entscheidungen zu Bewässerung und Düngung](../watering-and-fertilization-decisions/de.md) festgelegt
- Etwas anwenden: kein `-apply`-Rezept, kein Anwendungsvertrag. Das Issue verlangt keinen, und „keine Mutation ohne ausdrückliche Anwendungsschritte“ ist erfüllt, indem keiner geliefert wird
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikation und sagen, dass sie nicht neu gemessen wurden
- Ein Überfälligkeitsintervall für eine Pflegeaufgabe berechnen. Die Antwortform von `get_due_care_tasks` ist nicht festgehalten (Abschnitt D)
- Jeden Tag jede Pflanze eines Gartens prüfen (Abschnitt F)

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** den Gartenkontext-Block von `garden-context` so übernehmen, wie er ist, und **MUSS [MUST]** ein Feld, das der Block als fehlend markiert, als fehlend melden, nie auffüllen
- **KANN [MAY]** das Plandokument von `plant-planning` übernehmen, von dem sie je Durchlauf den Durchlaufbezeichner, den Artschlüssel, den Sortenschlüssel, die Anbauweise, die Fenster und die Konfidenz liest (die Verbrauchertabelle der Plan-Spezifikation), und **MUSS [MUST]** einen nicht gelieferten Plan als fehlend behandeln, nicht als „keine Pflanzdurchläufe“
- **MUSS [MUST]** die Domänenbefunde so übernehmen, wie sie sind (Abschnitt C), **MUSS [MUST]** eine Domäne, die nichts geliefert hat, als fehlend mit Grund melden und **DARF NICHT [MUST NOT]** für eine Domäne Allgemeinwissen einsetzen

### B. Beobachtung, Empfehlung, Mutation

- **MUSS [MUST]** jedem Eintrag genau eine Art geben: Beobachtung (was ein Tool oder Dokument gesagt hat, mit Quelle und Abrufzeit), Empfehlung (ein Vorschlag an eine Person) oder Mutation (die nächste Anforderung)
- **MUSS [MUST]** jeder Empfehlung die vier Blöcke der Entscheidungsrichtlinie geben (Beleg, Konfidenz, Unsicherheit, fehlende Daten) und **DARF NICHT [MUST NOT]** eine Empfehlung ohne sie liefern
- **MUSS [MUST]** eine Mutation nur als das zustandsändernde Tool benennen, das ein späterer Anwendungsschritt aufrufen würde, mit dem Eintrag, der sie begründet, und **DARF NICHT [MUST NOT]** es aufrufen, einplanen oder eine Empfehlung als Anweisung an ein Gerät oder einen Schreibzugriff formulieren

### C. Der Einklinkvertrag

- **MUSS [MUST]** einen Befund definieren als: die Domäne, das Subjekt (ein Pflanzenschlüssel oder der Garten), die Art (Beobachtung oder Empfehlung), die Aussage, die Belegeinträge (Stufe, Quelle, Abrufzeit), die Konfidenz, was sie ändern würde, die fehlenden Daten und optional die Folge (was geschieht, wenn nichts getan wird, in den Worten der Domäne)
- **DARF NICHT [MUST NOT]** einem Befund ein Feld hinzufügen, das die Domäne nicht geliefert hat, und **MUSS [MUST]** die Folge fehlen lassen, wenn die Domäne keine genannt hat
- **MUSS [MUST]** die Berichte der beiden Domänen, die diese Form nicht liefern, `nutrient-imbalance-assess` und `pest-pressure-assess`, in Befunde abbilden, **MUSS [MUST]** die Befunde der Bewässerungs- und der Düngeentscheidung so übernehmen, wie sie sie liefern, **MUSS [MUST]** die Belegstufen der abgebildeten Berichte aus der Tabelle „Wie sich die bestehenden Leitern verhalten“ der Entscheidungsrichtlinie lesen und **DARF NICHT [MUST NOT]** eine Stufe vergeben, wo diese Tabelle keine nennt (die Nährstoff-Stufe 2 und aus einem Bild gelesene Symptome)
- **MUSS [MUST]** ein Nährstoff- oder Schädlingsergebnis, das sein besitzender Prozess mit unbestimmter Richtung lässt, als Verdacht oder unterhalb seiner Verweigerungsschwelle, als Beobachtung behandeln und nicht als Empfehlung
- **MUSS [MUST]** jede in den Nicht-Zielen genannte Domäne als nicht verfügbar melden und den Skill nennen, der sie liefern würde, bis dieser Skill existiert, und **DARF NICHT [MUST NOT]** das Ergebnis einer anderen Domäne einsetzen

### D. Priorisierung

- **MUSS [MUST]** die Handlungseinträge nach Dringlichkeit ordnen (`now`, `soon`, `routine`, `watch`), dann nach Konfidenz, höhere Belegstufe zuerst, dann nach Subjektschlüssel, dann nach Domäne, sodass die Ordnung eine Totalordnung auf dem Inhalt ist
- **MUSS [MUST]** die Dringlichkeit nur aus genannten Feldern ableiten: `now`, wenn die Folge des Befunds einen gegenwärtigen oder fortschreitenden Schaden nennt, `soon`, wenn sie einen Schaden nennt, der folgt, wenn nichts getan wird, `routine` für eine Empfehlung ohne genannte Folge und für eine fällige Pflegeaufgabe und `watch` für eine Beobachtung
- **DARF NICHT [MUST NOT]** die Dringlichkeit aus Allgemeinwissen, aus der Dauer, die eine Erinnerung fällig ist, oder aus einer fälligen Aufgabe allein über `routine` hinaus ableiten
- **MUSS [MUST]** die Konfidenz aus der höchsten Belegstufe der Entscheidungsrichtlinie ableiten, die den Eintrag stützt, nie daraus, wie sicher seine Aussage klingt, und **MUSS [MUST]** sagen, dass keine Stufe gilt, wenn keine gilt

### E. Unzureichender Beleg

- **DARF NICHT [MUST NOT]** eine Handlung für den gegenwärtigen Zustand einer Pflanze oder des Gartens ohne Beleg zu diesem Zustand erzeugen, und **MUSS [MUST]** ihn unter „keine Handlung, Beleg unzureichend“ mit der Beobachtung aufführen, die ihn liefern würde
- **MUSS [MUST]** eine fällige Pflegeaufgabe als Anfrage des Zeitplans führen und nicht als Messung, und **DARF NICHT [MUST NOT]** eine Handlung allein empfehlen, weil sie fällig ist
- **MUSS [MUST]** „keine Handlung“ als Ergebnis des ganzen Laufs zulassen und **DARF NICHT [MUST NOT]** einen Plan auffüllen, damit er nützlich aussieht

### F. Die tägliche Prüfung

- **MUSS [MUST]** ein Orchestrierungs-Einstiegspunkt sein, der den Gartenkontext ausführt, dann jede verfügbare Domäne, dann die Entscheidungsrichtlinie und die Pflegeschicht, und **DARF NICHT [MUST NOT]** die Logik einer Domäne im Rezept duplizieren
- **MUSS [MUST]** einen Parameter `plants` annehmen, durch Kommas getrennte Pflanzenschlüssel, standardmäßig leer: leer führt nur die Gartenebene aus (fällige Aufgaben und Pflanzdurchläufe aus dem Gartenkontext), angegeben führt die Nährstoff-, Schädlings-, Bewässerungs- und Düngeprüfung für diese Pflanzen aus
- **MUSS [MUST]** höchstens fünf Pflanzen prüfen und den Rest als nicht geprüft mit Grund melden, und **DARF NICHT [MUST NOT]** für jede Pflanze des Gartens ein Tool je Pflanze aufrufen
- **MUSS [MUST]** jede Domäne mit einem Status aufführen: geprüft, nicht verfügbar (mit dem Skill) oder nicht geprüft (mit Grund), und **DARF NICHT [MUST NOT]** eine Domäne auslassen
- **MUSS [MUST]** einen Tool-Fehler wörtlich melden und mit dem Rest fortfahren
- **MUSS [MUST]** mit einem festen Bericht und einer maschinenlesbaren Schlusszeile schließen, die die Anzahl der Handlungen, die Anzahl der Einträge ohne Handlung und den Garten-Slug nennt

### G. Determinismus

- **MUSS [MUST]** die Fakten des Pflegeplans zu einer Funktion der gelieferten Blöcke und Befunde machen, sodass zwei Läufe über dieselbe Eingabe dieselben Fakten in derselben Reihenfolge ergeben
- **DARF NICHT [MUST NOT]** das aktuelle Datum innerhalb der Fakten des Pflegeplans lesen; Abrufzeiten stehen neben den Fakten und werden nicht verglichen
- **MUSS [MUST]** sagen, dass byte-identische Prosa außerhalb der Fakten des Pflegeplans nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage von als Text ausgeschriebenen Eingabeblöcken geprüft wird

### H. Trennung

- **DARF NICHT [MUST NOT]** aus dem Skill oder dem Rezept ein zustandsänderndes Tool aufrufen, und **MUSS [MUST]** jedes zustandsändernde Tool, das die Server-Spezifikation nennt, einzeln im Prompt des Rezepts als verboten benennen
- **DARF NICHT [MUST NOT]** ein Home-Assistant-Tool aufrufen
- **DARF NICHT [MUST NOT]** ein `-apply`-Geschwister des Rezepts liefern und **DARF NICHT [MUST NOT]** einen Anwendungsvertrag erfinden
- **MUSS [MUST]** den Skill werkzeugfrei halten: Er arbeitet nur auf den Blöcken und Befunden, die er erhält

## Akzeptanzkriterien

- [ ] Jeder Eintrag eines Pflegeplans hat genau eine Art, und keine Mutation wird aufgerufen, eingeplant oder als Anweisung formuliert
- [ ] Jede Empfehlung trägt Beleg, Konfidenz, Unsicherheit und fehlende Daten, und keine wird ohne sie geliefert
- [ ] Ein Befund hat die Felder aus Abschnitt C und kein Feld, das die Domäne nicht geliefert hat; die Folge fehlt, wenn die Domäne keine genannt hat
- [ ] Die Nährstoff- und Schädlingsberichte werden in Befunde abgebildet, mit Stufen aus der Tabelle der Entscheidungsrichtlinie, und wo die Tabelle keine nennt, wird keine vergeben, und die Befunde der Bewässerungs- und der Düngeentscheidung werden so übernommen, wie sie sie liefern
- [ ] Ein Verdacht oder eine unbestimmte Richtung ist eine Beobachtung, keine Empfehlung
- [ ] Jede in den Nicht-Zielen genannte Domäne wird als nicht verfügbar mit dem Skill gemeldet, der sie liefern würde, und keine wird durch eine andere ersetzt
- [ ] Die Ordnung ist Dringlichkeit, dann Konfidenz, dann Subjektschlüssel, dann Domäne und ändert sich nicht, wenn sich die Reihenfolge der Eingabe ändert
- [ ] Die Dringlichkeit stammt nur aus einer genannten Folge, einer fälligen Aufgabe oder einer Beobachtung und nie aus Allgemeinwissen oder dem Alter einer Erinnerung
- [ ] Ein Zustand ohne Beleg ergibt keine Handlung und steht unter „keine Handlung, Beleg unzureichend“ mit der Beobachtung, die ihn liefern würde
- [ ] Eine fällige Pflegeaufgabe wird als Anfrage des Zeitplans geführt, und keine Handlung ruht allein darauf, dass sie fällig ist
- [ ] Die tägliche Prüfung ohne `plants` führt nur die Gartenebene aus, mit einer Pflanzenliste prüft sie höchstens fünf und nennt den Rest als nicht geprüft
- [ ] Die tägliche Prüfung führt jede Domäne mit ihrem Status auf und schließt mit der maschinenlesbaren Schlusszeile
- [ ] Zwei Läufe über dieselben Eingabeblöcke ergeben an einer festen Vorlage dieselben Fakten des Pflegeplans, und das Ergebnis sagt, was nicht beansprucht wird
- [ ] Weder der Skill noch das Rezept rufen ein zustandsänderndes Tool oder ein Home-Assistant-Tool auf, und der Prompt des Rezepts verbietet jedes zustandsändernde Tool namentlich
- [ ] Mit dieser Änderung werden kein `-apply`-Rezept und kein Anwendungsvertrag geliefert
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl Anforderungspunkte und dieselbe Anzahl Akzeptanz-Checkboxen

## Quelle

- [Die Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, die sechs Regeln, die Ausgabe einer Empfehlung, der Gartenkontext-Block und die Tabelle „Wie sich die bestehenden Leitern verhalten“
- [Die Spezifikation zu Pflanzplanung und Pflanzkalender](../plant-planning-and-planting-calendar/de.md) — das Plandokument und seine Verbrauchertabelle, in der die Pflegeplanung genannt wird
- [Die Spezifikation zur Nährstoff-Ungleichgewichts-Erkennung](../nutrient-imbalance-detection/de.md) — die Nährstoff-Leiter, ihre Verweigerungsschwelle und die Regel zu Stufe 2 (Dosismengen nötig; gemergt in nolte/kamerplanter-goose#64)
- [Die Spezifikation zur Schädlingsdruck-Bewertung](../pest-pressure-assessment/de.md) — die Schädlings-Leiter und ihre Falsifikationstests
- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Tool-Katalog und die zustandsändernden Tools, gemessen 2026-08-16
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie ein Rezept hier gebaut wird, einschließlich der Regel, verbotene Tools namentlich zu nennen
- [Die Spezifikation zu den Entscheidungen zu Bewässerung und Düngung](../watering-and-fertilization-decisions/de.md) — die beiden Domänen, die Befunde in dieser Form liefern
- Issue nolte/kamerplanter-goose#43 — der Umfang und die fünf Akzeptanzkriterien stammen aus seinem Text; #44, #45, #48 und #49 — die Domänen, die sich einklinken; #39 — das Audit

## Offene Fragen

- **Ob die Domänen-Skills ein ausdrückliches Dringlichkeitsfeld im Einklinkvertrag brauchen.** Die Dringlichkeit wird hier aus der genannten Folge abgeleitet. Die Bewässerungs- und die Düngeentscheidung lassen die Folge fehlen, wenn keine Eingabe eine nennt, und heute nennt keine eine, sodass ihre Empfehlungen `routine` einstufen; ob für sie eine Folge in einer Form genannt werden kann, bleibt offen, bis eine Domäne es tut.
- **Wie sich die Regel zu Nährstoff-Stufe 2 als Konfidenz in einem Pflegeeintrag zeigt.** Stufe 2 braucht erfasste Dosismengen und trägt keine Stufe der Entscheidungsrichtlinie (Abschnitt C), also sagt ein Pflegeeintrag, der darauf ruht, dass keine Stufe gilt. Ob das der richtige Ort dafür ist, bleibt offen.
- **Wo das Audit nolte/kamerplanter-goose#39 die Pflegeplanung relativ zum Gartenkontext einordnet.** Ob die Schicht ein Skill bleibt, entscheidet das Audit.
- **Die Antwortfelder von `get_due_care_tasks`.** Keine Spezifikation hier hält fest, ob eine Aufgabe ein Fälligkeitsdatum oder ein Intervall trägt, also ist keine Überfälligkeitsberechnung festgelegt, und eine fällige Aufgabe ist höchstens `routine`. Eine Messung an einer erreichbaren Instanz würde das klären.
- **Ob fünf Pflanzen die richtige Obergrenze ist.** Die Zahl ist gewählt, um die Aufrufe je Pflanze zu begrenzen, nicht an der Gartengröße oder den Serverlimits gemessen.
