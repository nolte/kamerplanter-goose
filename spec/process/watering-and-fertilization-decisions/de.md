# Entscheidungen zu Bewässerung und Düngung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Zwei Fragen stellen sich für jede Pflanze, die über dieses Repository betreut wird: Soll sie jetzt gegossen werden, und soll sie gedüngt werden. Jede hat eine verlockende falsche Antwort. Gießen, weil eine Erinnerung fällig ist oder ein Intervall verstrichen ist, bringt Wasser auf eine Pflanze, deren gegenwärtigen Zustand niemand gelesen hat. Düngen, weil eine Pflanze blass aussieht, behandelt eine Unterversorgung, die auch Nichtverfügbarkeit, Überversorgung oder ein pH-Problem sein kann. Diese Spezifikation legt fest, worauf jede Entscheidung ruhen darf, welche geschlossene Menge an Antworten sie geben darf, was sie verweigern muss und was ein `-apply`-Rezept dafür schreiben darf und was nicht.

Eine Entscheidung ist hier ein Vorschlag an eine Person. Sie ändert nichts und wird aus Blöcken getroffen, die andere Skills bereits gesammelt haben.

Alles zur Tool-Oberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), gemessen an der Referenzinstanz am 2026-08-16 und für diese Spezifikation nicht neu gemessen: Der Kamerplanter-MCP-Server war beim Schreiben nicht erreichbar (`INVALID_CONFIG`). Vier Tatsachen, auf denen die Anforderungen ruhen, wurden aus der Arbeitskopie gelesen und nicht gemessen: Keines der zustandsändernden Tools, die die Server-Spezifikation führt, gießt, dosiert oder steuert an (ihre Abschnitte „Schreibtools“ und „Setup-Tool“); keine Spezifikation, kein Guide, kein Skill und kein Rezept hält den Wertebereich von `reminder_type` fest (eine Suche in `spec/`, `docs/`, `.claude/` und `recipes/` findet den Feldnamen und keinen Wert); die Phasendefinition trägt ein Feld `watering_interval_days` ([Spezifikation zur Artdaten-Prüfung](../species-baseline-verification/de.md), ihre Tabelle zu `list_phase_definitions`, und `.claude/skills/plant-context-collect/SKILL.md` §4); und für Home-Assistant-Sensoren ist keine Zuordnung zu einer Pflanze festgehalten ([Nährstoff-Spezifikation](../nutrient-imbalance-detection/de.md), Offene Fragen).

Grenzen: Die [Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) besitzt die Belegstufen, die sechs Regeln und die Form einer Empfehlung und nennt die Frage „ein Bewässerungsintervall“ als eine, die der besitzende Prozess entscheidet; diese Spezifikation ist dieser Prozess für Gießen und Düngen und nennt keine eigene Stufe. Die [Spezifikation zur Nährstoff-Ungleichgewichts-Erkennung](../nutrient-imbalance-detection/de.md) besitzt die Richtung eines Nährstoffproblems, die Belegleiter und die Regel, dass Stufe 2 erfasste Dosismengen braucht; die Düngeentscheidung übernimmt ihren Bericht und leitet ihn nicht neu ab. Die [Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) besitzt die Einklinkform eines Befunds und die tägliche Prüfung, die diese Entscheidungen ausführt. Das [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt, wie ein Rezept gebaut wird, einschließlich der namentlichen Verbote.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Personen, die die Entscheidungen ausführen und ihre Ergebnisse lesen, und alle, die ein `-apply`-Rezept prüfen, bevor es schreibt.

## Ziele

- Ein Bewässerungsergebnis sagt, worauf es zum gegenwärtigen Zustand der Pflanze ruht, und sagt offen, wenn es nichts gibt
- Ein Düngeergebnis sagt, auf welchem von unzureichender Ernährung, einer Umweltursache und einer unsicheren Diagnose es ruht, oder dass unzureichende Ernährung ausgeschlossen ist, und „nicht düngen“ ist eine gewöhnliche Antwort
- Es erscheint keine Konzentration, Dosis, Mischreihenfolge und Messung, die kein Tool geliefert hat
- Eine fällige Erinnerung ist nie ein Grund zu gießen
- Ein `-apply`-Rezept hält fest, was eine Person getan hat, und lässt sich nicht mit etwas verwechseln, das gießt oder düngt

## Nicht-Ziele

- Pflanzengesundheit und Schädlingsmanagement (nolte/kamerplanter-goose#48), Wachstumsstadium und Wetter (#49)
- Etwas ansteuern: keine Bewässerung, keine Dosierpumpe, kein Home-Assistant-Gerät. Eine Entscheidung ist ein Vorschlag an eine Person
- Den Nährstoffprozess ändern: seine Richtung, seine Leiter und seine Stufenregel bleiben, wo sie sind
- Einen Gieß- oder Düngeplan berechnen
- Die Tool-Oberfläche live messen. Aussagen darüber zitieren die Server-Spezifikation und sagen, dass sie nicht neu gemessen wurden

## Anforderungen

### A. Eingaben

- **MUSS [MUST]** den Pflanzenkontext-Block von `plant-context-collect`, den Leseberichts-Block und die Messwerte von `diary-measurements-read` und den Gartenkontext-Block von `garden-context` so übernehmen, wie sie sind, und **DARF NICHT [MUST NOT]** ein Tool aufrufen, um zu holen, was einer dieser Blöcke schon enthält
- **MUSS [MUST]** nur die Tatsachen, für die der Server keine Quelle hat, als vom Aufrufer geliefert annehmen und mit `caller` kennzeichnen: Wetter und Vorhersage, das Gefäß oder Beet, Bewässerungsvorgaben, Nutzervorgaben, die EC der Wasserquelle sowie Tank- und Dosierzustand
- **MUSS [MUST]** jede fehlende Eingabe als fehlend mit Grund melden, `no source` oder `not collected`, und **DARF NICHT [MUST NOT]** sie auffüllen
- **DARF NICHT [MUST NOT]** einen Home-Assistant-Sensor als Beleg zu einer Pflanze verwenden, weil keine Zuordnung von Sensor zu Pflanze festgehalten ist

### B. Die Bewässerungsentscheidung

- **MUSS [MUST]** genau eines von `water now`, `wait` und `insufficient evidence` liefern
- **MUSS [MUST]** `water now` nur mit einem Beleg zum gegenwärtigen Zustand der Pflanze liefern und **MUSS [MUST]** diesen Beleg im Ergebnis nennen: Eine jüngste Messung in einem Tagebucheintrag dieser Pflanze zählt als Stufe 1
- **MUSS [MUST]** die bestätigten Erinnerungen des Pflegeprotokolls und ihre Intervalle als Stufe 3 lesen, und das `watering_interval_days` der Phasendefinition sowie die Art- und Phasenanforderungen als Vorannahmen der Stufe 4, die **DÜRFEN NICHT [MUST NOT]** allein entscheiden
- **DARF NICHT [MUST NOT]** `water now` liefern, weil eine Erinnerung fällig ist, ein Intervall oder ein Zeitplan verstrichen ist oder die Pflanze vermutlich trocken ist (Regel 2 der Entscheidungsrichtlinie)
- **MUSS [MUST]** `insufficient evidence` liefern, wenn über den gegenwärtigen Zustand der Pflanze nichts bekannt ist, und **MUSS [MUST]** die Beobachtung nennen, die ihn liefern würde
- **DARF NICHT [MUST NOT]** eine fehlende Messung erfinden und **DARF NICHT [MUST NOT]** Bodenfeuchte aus einem `measurements`-Schlüssel lesen, dessen Bedeutung oder Einheit mehrdeutig ist
- **MUSS [MUST]** jedem Ergebnis seinen Beleg, seine Konfidenz, seine Unsicherheit und die fehlenden Daten geben, wie es die Entscheidungsrichtlinie verlangt

### C. Die Düngeentscheidung

- **MUSS [MUST]** genau eines von `feed`, `do not feed` und `insufficient evidence` liefern
- **MUSS [MUST]** den Nährstoffbericht so übernehmen, wie er ist, und **DARF NICHT [MUST NOT]** seine Richtung oder seine Stufenregel neu ableiten, neu einordnen oder übersteuern
- **MUSS [MUST]** `feed` nur liefern, wenn der Nährstoffprozess Unterversorgung als Richtung festgestellt hat und keine Umweltursache genannt ist
- **MUSS [MUST]** `do not feed` liefern, wenn die Richtung Überversorgung oder Nichtverfügbarkeit bei ausreichender Versorgung ist oder eine Umweltursache genannt ist (Regel 5 der Entscheidungsrichtlinie), und **MUSS [MUST]** es als gewöhnliches Ergebnis behandeln
- **MUSS [MUST]** `insufficient evidence` liefern, wenn der Nährstoffprozess die Richtung unbestimmt oder bei einem Verdacht lässt
- **MUSS [MUST]** sagen, auf welchem von unzureichender Ernährung, einer Umweltursache und einer unsicheren Diagnose das Ergebnis ruht, oder dass unzureichende Ernährung ausgeschlossen ist (Überversorgung)
- **MUSS [MUST]** die jüngste Düngung aus dem Pflegeprotokoll als bestätigte Erinnerungen nehmen, die keine Menge tragen, und **DARF NICHT [MUST NOT]** eine Menge nennen, die der Datenbestand nicht hält
- **MUSS [MUST]** das konservative Ergebnis bevorzugen, wenn der Beleg unvollständig ist

### D. Sicherheit

- **DARF NICHT [MUST NOT]** eine Konzentration, eine Dosis oder eine Mischreihenfolge nennen, außer als Ergebnis von `calculate_mixing_protocol`, das auf EC-netto arbeitet, und **MUSS [MUST]** die Annahme zum Basiswasser nennen, wenn es aufgerufen wird
- **MUSS [MUST]** die Dosis als unbekannt melden, wenn dieses Ergebnis fehlt
- **DARF NICHT [MUST NOT]** eine Konzentration oder eine Messung erfinden

### E. Trennung und der Anwendungsvertrag

- **MUSS [MUST]** die Entscheidungs-Skills und die lesenden Rezepte frei von jedem zustandsändernden Tool und jedem Home-Assistant-Tool halten
- **MUSS [MUST]** ein `-apply`-Rezept eine von einer Person genehmigte Entscheidung und die Handlung, die die Person ausgeführt hat, entgegennehmen lassen, einen Eintrag dieser Handlung schreiben und sonst nichts, und es verweigern lassen, wenn eines von beiden fehlt
- **MUSS [MUST]** `watering-decision-apply` nur `confirm_care_task` aufrufen lassen, mit dem `plant_key` und dem `reminder_type`, den der Aufrufer liefert, und **DARF NICHT [MUST NOT]** den `reminder_type` raten
- **MUSS [MUST]** `fertilization-decision-apply` nur `record_feeding_event` aufrufen lassen, mit dem `plant_key`, `volume_applied_liters` und nur den weiteren Werten, die die Person geliefert hat, und **MUSS [MUST]** die Namen der optionalen Eingaben zur Laufzeit aus dem Schema des Tools lesen und keine erfinden
- **MUSS [MUST]** das Tool zuerst mit `dry_run` true aufrufen und die geplante Wirkung melden und es danach mit einem `idempotency_key` aufrufen
- **MUSS [MUST]** genau sein eines Tool namentlich als erlaubt und jedes andere zustandsändernde Tool namentlich als verboten benennen und **DARF NICHT [MUST NOT]** ein Home-Assistant-Tool aufrufen
- **DARF NICHT [MUST NOT]** behaupten, eine Pflanze sei gegossen oder gedüngt worden, **MUSS [MUST]** sagen, dass die Wirkung ein Eintrag ist, und das Düngerezept **MUSS [MUST]** sagen, dass nicht gemessen ist, ob ein Lese-Tool erfasste Düngeereignisse zurückgibt (nolte/kamerplanter-goose#54)

### F. Die Einklinkform

- **MUSS [MUST]** neben der Entscheidung Befunde in der Form liefern, die die Spezifikation zur Pflegeplanung in ihrem Abschnitt C festlegt
- **MUSS [MUST]** `water now` und `feed` als Empfehlungen und `wait`, `do not feed` und `insufficient evidence` als Beobachtungen liefern
- **MUSS [MUST]** die Folge eines Befunds fehlen lassen, wenn keine Eingabe eine nennt

### G. Determinismus

- **MUSS [MUST]** die Entscheidung zu einer Funktion der gelieferten Blöcke machen, sodass zwei Läufe über dieselben Blöcke dieselbe Entscheidung, dieselben Belegstufen und dieselbe Liste fehlender Daten ergeben
- **DARF NICHT [MUST NOT]** das aktuelle Datum innerhalb der Entscheidungsfakten lesen; Abrufzeiten stehen neben den Fakten und werden nicht verglichen
- **MUSS [MUST]** sagen, dass byte-identische Prosa außerhalb der Entscheidungsfakten nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage von als Text ausgeschriebenen Eingabeblöcken geprüft wird

### H. Was es nicht gibt

- **DARF NICHT [MUST NOT]** ein Tool annehmen, das gießt, dosiert oder ansteuert: Keines ist gemessen

## Akzeptanzkriterien

- [ ] Ein Bewässerungsergebnis ist eines von `water now`, `wait` und `insufficient evidence`, und ein Düngeergebnis ist eines von `feed`, `do not feed` und `insufficient evidence`
- [ ] `water now` nennt einen Beleg zum gegenwärtigen Zustand der Pflanze, und kein Ergebnis ruht allein auf einer fälligen Erinnerung, einem verstrichenen Intervall oder einem Zeitplan
- [ ] Das `watering_interval_days` einer Phase, die Artdaten und die Phasenanforderungen werden als Vorannahmen gelesen und entscheiden nichts allein
- [ ] Eine fehlende Messung wird als fehlend gemeldet, und Bodenfeuchte wird nicht aus einem mehrdeutigen `measurements`-Schlüssel gelesen
- [ ] Jedes Ergebnis trägt Beleg, Konfidenz, Unsicherheit und fehlende Daten
- [ ] Die Düngeentscheidung übernimmt den Nährstoffbericht so, wie er ist, und leitet weder seine Richtung noch seine Stufenregel neu ab
- [ ] `feed` erscheint nur bei festgestellter Unterversorgung ohne genannte Umweltursache, und `do not feed` wird bei Überversorgung, Nichtverfügbarkeit und genannter Umweltursache geliefert
- [ ] Das Ergebnis sagt, auf welchem von unzureichender Ernährung, einer Umweltursache und einer unsicheren Diagnose es ruht, oder dass unzureichende Ernährung ausgeschlossen ist
- [ ] Keine Konzentration, Dosis oder Mischreihenfolge erscheint außer aus `calculate_mixing_protocol`, mit genannter Basiswasser-Annahme, und ein fehlendes Ergebnis ergibt eine unbekannte Dosis
- [ ] Kein Home-Assistant-Sensor wird als Beleg verwendet, und keine Eingabe ohne Quelle wird aufgefüllt
- [ ] Die Entscheidungs-Skills und die lesenden Rezepte rufen kein zustandsänderndes Tool und kein Home-Assistant-Tool auf
- [ ] Jedes `-apply`-Rezept nimmt eine genehmigte Entscheidung und die ausgeführte Handlung entgegen, verweigert ohne sie, schreibt nur den Eintrag seines einen Tools und benennt jedes andere zustandsändernde Tool als verboten
- [ ] `watering-decision-apply` rät nie einen `reminder_type`, und `fertilization-decision-apply` übergibt keine Eingabe, die die Person nicht geliefert hat
- [ ] Jedes `-apply`-Rezept ruft zuerst `dry_run` auf, meldet die geplante Wirkung und ruft dann mit einem `idempotency_key` auf
- [ ] Kein `-apply`-Rezept behauptet, eine Pflanze sei gegossen oder gedüngt worden, und jedes sagt, dass die Wirkung ein Eintrag ist, und das Düngerezept ergänzt, dass das Zurücklesen von Düngeereignissen nicht gemessen ist
- [ ] Jede Entscheidung liefert Befunde in der Einklinkform der Pflegeplanung, mit `water now` und `feed` als Empfehlungen und den übrigen Ergebnissen als Beobachtungen
- [ ] Zwei Läufe über dieselben Eingabeblöcke ergeben an einer festen Vorlage dieselben Entscheidungsfakten, und das Ergebnis sagt, was nicht beansprucht wird
- [ ] Jede Aussage zur Tool-Oberfläche zitiert eine Spezifikation in diesem Repository, und eine nicht neu gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Anzahl Anforderungspunkte und dieselbe Anzahl Akzeptanz-Checkboxen

## Quelle

- [Die Entscheidungsrichtlinie für den Garten](../garden-decision-policy/de.md) — die Belegstufen, die sechs Regeln, die Ausgabe einer Empfehlung und der Gartenkontext-Block
- [Die Spezifikation zur Nährstoff-Ungleichgewichts-Erkennung](../nutrient-imbalance-detection/de.md) — die Richtung, die Leiter, die Regel zu Stufe 2 (Dosismengen nötig; gemergt in nolte/kamerplanter-goose#64) und die offene Frage zu Sensoren
- [Die Spezifikation zu Pflegeplanung und täglicher Prüfung](../care-planning-and-daily-check/de.md) — die Einklinkform und die tägliche Prüfung
- [Die Spezifikation zur Artdaten-Prüfung](../species-baseline-verification/de.md) — die Felder der Phasendefinition, einschließlich `watering_interval_days`
- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Tool-Katalog, die Schreib-Tools, `dry_run` und `idempotency_key`, gemessen 2026-08-16
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) — wie ein Rezept hier gebaut wird, einschließlich der namentlichen Verbote
- Issues nolte/kamerplanter-goose#44 und #45 — der Umfang und die Akzeptanzkriterien stammen aus ihren Texten; #54 — das Zurücklesen von Düngeereignissen; #59 — die Anwendungshälfte, die aus demselben Grund aus der Planung abgespalten wurde

## Offene Fragen

- **Der Wertebereich von `reminder_type` und welcher Wert das Gießen ist.** Keine Datei hier hält ihn fest, also liefert ihn der Aufrufer. Ein lesender Aufruf des Pflegeprotokolls einer erreichbaren Instanz würde die verwendeten Werte zeigen.
- **Die Eingabenamen der optionalen Felder von `record_feeding_event`.** Die Server-Spezifikation hält sie nur als Menge, EC und pH vor und nach der Gabe und Abfluss fest. Das Rezept liest sie zur Laufzeit aus dem Schema des Tools.
- **Ob Düngeereignisse zurückgelesen werden (nolte/kamerplanter-goose#54).** Davon hängt ab, ob ein von `fertilization-decision-apply` geschriebener Eintrag je Stufe 2 der Nährstoffleiter erreicht.
- **Die Quelle für Wetter und Vorhersage.** Der gemessene Katalog hat keine; bis es eine gibt, kann nur der Aufrufer sie liefern.
- **Welcher `measurements`-Schlüssel die Bodenfeuchte trägt.** Das Feld hat keinen festen Schlüsselsatz, und die Normalisierung der Nährstoff-Spezifikation gilt; hier ist kein Schlüssel festgestellt.
- **Was `watering_interval_days` zählt und ob die Art einen Wasserbedarf trägt.** Die Phasendefinition trägt das Feld; diese Spezifikation stellt nicht fest, was es zählt, und kein Wasserbedarfsfeld der Art ist festgehalten. Es wird als Vorannahme der Stufe 4 gelesen und entscheidet nichts allein.
- **Womit ein Feuchtewert verglichen wird.** Diese Spezifikation sagt es nicht, und kein Feld des Pflanzenkontext-Blocks trägt im gemessenen Datenbestand einen Feuchte-Zielwert. Die Bewässerungsentscheidung nimmt den Zielwert vom Aufrufer, als Nutzervorgabe, und endet ohne ihn bei `insufficient evidence`.
- **Was „jung genug“ für einen Feuchtewert heißt.** Die Entscheidungsrichtlinie lässt es offen, und die Entscheidungsfakten lesen das aktuelle Datum nicht. Die Bewässerungsentscheidung meldet daher das erfasste Datum des Werts und die Grundlage, auf der sie ihn als aktuell beurteilt hat, und behandelt einen Wert, den sie nicht beurteilen kann, als Stufe 2.
