# Erkennung von Nährstoff-Ungleichgewichten

Status: Entwurf
Portfolio-Scope: local

## Kontext

Zu wenig Dünger und zu viel Dünger sehen auf einem Blatt gleich aus. Randnekrose, Interkostalchlorose, gestauchter Neutrieb, eine stumpfe Blattoberfläche — jedes davon tritt auf, wenn ein Nährstoff fehlt, und ebenso, wenn der Wurzelraum zu konzentriert ist, um ihn aufzunehmen. Ein Prozess, der das Foto liest und zur vertrauteren Erklärung greift, empfiehlt, eine bereits überversorgte Pflanze zu düngen, und diese Empfehlung verschlechtert ihren Zustand.

**Die Richtung eines Nährstoffproblems ist im Bild nicht sichtbar. Sie ist eine Eigenschaft der Versorgungsbilanz**, und diese Bilanz lässt sich aus Kamerplanter rekonstruieren: Ein Düngeplan nennt Ziel-EC und NPK-Verhältnis je Phase, das Substrat nennt seinen eigenen Ausgangs-EC, pH und seine Pufferung, das Pflegeprotokoll nennt bestätigte Düngungen, und Tagebucheinträge können Messwerte tragen. Diese Spec legt fest, wie daraus eine Richtung, eine Konfidenz und eine Korrektur mit dem richtigen Vorzeichen werden.

Sie ist das Gegenstück zur [bildgestützten Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md), nicht ein Teil davon. Dort ist eine Mangel-Lesart ein möglicher Befund neben Schädlingen, Krankheit und Trockenheit, und das Bild ist der primäre Beleg. Hier ist die Nährstofffrage der ganze Gegenstand, die Versorgungsakte ist der primäre Beleg, und das Bild ist eine Eingangsgröße, die sie stützen oder ihr widersprechen kann. Beide sollen zusammenspielen: Der Bildprozess kann einen Mangelverdacht an diesen übergeben, und dieser liefert eine Richtung zurück, die das Bild allein nicht begründen konnte.

Ein dritter Fall liegt zwischen beiden und ist überhaupt der Grund für diese Spec. Eine Pflanze kann einen lehrbuchmäßigen Mangel zeigen und dabei korrekt versorgt sein, weil der Nährstoff vorhanden und nicht verfügbar ist — blockiert durch pH-Drift, durch einen EC, der hoch genug ist, die Aufnahme zu behindern, oder durch Antagonismus zwischen Ionen. Das sichtbare Symptom ist ein Mangel; die richtige Korrektur ist das Gegenteil von Düngen.

Alles als *gemessen* Gekennzeichnete wurde am 2026-08-05 von der Referenzinstanz gelesen.

Leserschaft: alle, die das Nährstoff-Rezept in diesem Repository schreiben, sowie alle, die eine vorgeschlagene Korrektur prüfen, bevor danach gehandelt wird.

## Ziele

- Die Richtung eines Ungleichgewichts — Unterversorgung, Überversorgung oder Nichtverfügbarkeit bei ausreichender Versorgung — wird aus der Versorgungsakte entschieden, nie aus dem Symptom allein
- Eine Korrektur weist in die richtige Richtung, und ein Lauf, der die Richtung nicht klären kann, schlägt gar keine Korrektur vor
- Das Substrat ist Teil der Diagnose, denn dasselbe Düngeregime ist im einen Medium unbedenklich und im anderen schädlich
- Jede Aussage benennt die Belegstufe, auf der sie ruht, sodass ein gemessener EC von einem erschlossenen unterscheidbar bleibt
- Das Fehlen eines Düngeplans schwächt die Analyse auf benannte Weise, statt still Zielwerte zu erfinden
- Was der Prozess aus der Akte nicht wissen kann — wie viel tatsächlich ausgebracht wurde — wird benannt statt geschätzt

## Nicht-Ziele

- Dünger ausbringen, eine Düngeaufgabe bestätigen oder den Düngeplan einer Pflanze ändern
- Eine Substrat- oder Blattanalyse im Labor ersetzen; dieser Prozess schließt aus der Akte, die Kamerplanter führt
- Düngepläne oder Düngerprodukte verfassen — der Katalog gehört dem Backend
- Schädlinge, Krankheiten oder Trockenheit diagnostizieren, außer um sie als konkurrierende Erklärung desselben Symptoms auszuschließen — das ist die [bildgestützte Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md)
- Rezept-Mechanik sowie MCP-Transport, -Authentifizierung und -Mandanten — festgelegt im [Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md) und in der [Server-Spec](../../mcp/kamerplanter-mcp-server/de.md)
- Bewässerungsplanung; die Gießhäufigkeit geht nur dort ein, wo sie die Salzbilanz verschiebt

## Gemessene Ausgangslage

### Die Soll-Seite

`get_plant_nutrient_plan` liefert den einer Pflanze zugewiesenen Plan, `get_nutrient_plan` einen nach Schlüssel. Gemessen trägt ein Plan `is_template`, `is_global_template`, `recommended_substrate_type`, `version`, `tags` sowie ein Array `phases`, dessen Einträge `phase_name`, `sequence_order`, `week_start`, `week_end`, `is_recurring`, `npk_ratio` als `[N, P, K]` und `target_ec_ms` tragen. Die Referenzinstanz führt 38 Pläne, überwiegend globale Vorlagen.

**Ein Plan ist nicht garantiert.** An der Referenzpflanze gemessen antwortete `get_plant_nutrient_plan` mit `{"plan": null}` — kein Plan zugewiesen. Das ist der Normalfall für eine Pflanze, die nie auf ein Düngeprogramm gesetzt wurde, und der Prozess muss dennoch etwas Brauchbares liefern.

### Die Ist-Seite und ihre Grenzen

Drei Quellen beschreiben, was die Pflanze tatsächlich erhalten hat, und keine davon ist ein Dosierprotokoll:

| Quelle | Was sie gibt | Was sie nicht gibt |
|--------|--------------|--------------------|
| `get_plant_care_log` | Bestätigte Erinnerungen mit `reminder_type`, `action` (`confirmed` / `snoozed`), `confirmed_at`, `interval_at_time_days`, `notes` | Welches Produkt, welche Konzentration, welches Volumen — eine bestätigte Düngung ist ein Wahrheitswert, keine Dosis |
| Tagebuch-`measurements` | Frei geformte Messwerte | Überhaupt ein Schema: Das Feld ist ein offenes Objekt, dokumentiert nur durch das Beispiel `{'height_cm': 42, 'ph': 6.3}` |
| Einträge vom Typ `measurement` oder `problem` | Beobachtertext und Tags um einen Messwert herum | Einheiten, Methode oder Kalibrierung des Messgeräts |

**`measurements` hat keinen festen Schlüsselsatz.** Gemessen lautet sein Schema `additionalProperties: true` ohne deklarierte Eigenschaften. Ein Prozess, der es liest, muss Schlüssel normalisieren und mehrdeutige verwerfen, statt anzunehmen, `ec` bedeute mS/cm oder `ph` sei im Ablauf statt im Tank gemessen worden.

Das `action: "snoozed"` des Pflegeprotokolls ist für sich genommen ein Beleg. An der Referenzpflanze gemessen wurde `repotting` zweimal verschoben — eine Pflanze, die in erschöpftem Substrat bleibt, sammelt ein anderes Problem an als eine planmäßig umgetopfte.

### Das Substrat

`list_substrates` liefert je Medium `type`, `ph_base`, `ec_base_ms`, `buffer_capacity`, `cec_meq_per_100g`, `water_retention`, `water_holding_capacity_percent`, `easily_available_water_percent`, `air_porosity_percent`, `irrigation_strategy`, `composition`, `reusable` und `max_reuse_cycles`.

Diese entscheiden, wie schwer ein Düngefehler wiegt. Ein Medium mit hoher `cec_meq_per_100g` und hoher `buffer_capacity` nimmt einen Überschuss auf und gibt ihn langsam ab; ein inertes reicht ihn direkt an die Wurzeln weiter. Dieselbe Wochengabe ist im ersten unauffällig und im zweiten eine Überversorgung, und der `recommended_substrate_type` eines Plans ist dessen eigene Aussage darüber, welches er unterstellt hat.

### Das Korrekturwerkzeug

`calculate_mixing_protocol` berechnet Dosen je Dünger für ein Zielvolumen und einen Ziel-EC, in Mischreihenfolge. Gemessen verlangt es `fertilizer_keys`, `target_volume_liters` und `target_ec_ms` und nimmt `base_water_ec` („vom Ziel abgezogen — EC-netto"), `target_ph`, `base_water_ph`, `alkalinity_ppm`, `substrate_type` und `phase` an. Es trägt **kein** `dry_run` und keinen `idempotency_key`, was es von den Schreib-Tools unterscheidet: Es rechnet und speichert nichts.

## Die Belegleiter

Aussagen werden danach eingestuft, worauf sie ruhen, und die Stufe wandert mit der Aussage ins Ergebnis. Eine niedrigere Stufe hebt eine höhere nie auf; sie stützt sie oder widerspricht ihr.

| Stufe | Beleg | Gewicht |
|-------|-------|---------|
| 1 | Ein Messwert aus einem Tagebucheintrag — EC, pH, Ablaufmessung — mit erkennbarer Einheit | Entscheidet die Richtung allein, sofern hinreichend aktuell |
| 2 | Planziel gegen rekonstruierte Zufuhr: `target_ec_ms` und `npk_ratio` der Phase gegen bestätigte Düngehäufigkeit und Substratbasis | Entscheidet die Richtung, wenn Stufe 1 fehlt, mit verringerter Konfidenz |
| 3 | Muster im Pflegeprotokoll allein — häufig, selten oder verschoben bestätigte Düngung; überfälliges Umtopfen | Stützt eine Richtung, begründet sie nie |
| 4 | Sichtbare Symptome aus dem Bildprozess | Verortet, welcher Nährstoff und wie weit fortgeschritten, nie die Richtung |
| 5 | `nutrient_demand_level` der Art und Phasenerwartung | Setzt nur die Vorannahme; ein `heavy_feeder` im Fruchtansatz hat deshalb keinen Mangel |

Ein Lauf, dessen höchste verfügbare Stufe 3 oder darunter liegt, meldet einen Verdacht mit ausdrücklich unbestimmter Richtung und schlägt keine Dosisänderung vor. Die fehlende Messung zu benennen, ist in diesem Fall das Ergebnis.

## Die Richtung bestimmen

Drei Zustände sind zu unterscheiden, denn ihre Korrekturen gehen auseinander und zwei von ihnen teilen sich ein Symptom.

**Unterversorgung.** Symptome, die zu einem bestimmten Nährstoff passen, Zufuhr unterhalb des Phasenziels — niedriger gemessener EC, längere Düngeintervalle als im Plan oder ein Medium mit niedriger CEC, das nichts hält — und kein Hinweis auf eine Aufnahmeblockade. Die Korrektur bewegt sich auf das Phasenziel zu.

**Überversorgung.** Gemessener EC oberhalb des Phasenziels oder eine Zufuhrhäufigkeit über dem Plan in einem schwach puffernden Medium, typischerweise mit Rand- oder Spitzennekrose an älteren wie neueren Blättern, sichtbarer Kruste oder Ablagerung auf der Medienoberfläche und ausbleibender Besserung nach dem Düngen. Die Korrektur senkt die Konzentration oder spült; Düngen ist kontraindiziert.

**Nichtverfügbarkeit bei ausreichender Versorgung.** Mangelsymptome, während die Zufuhr das Phasenziel erreicht. Als Ursachen kommen in Frage: ein pH außerhalb dessen, was `ph_base` und `buffer_capacity` des Substrats erwarten ließen, ein EC, der trotz passender Verhältnisse die Aufnahme behindert, oder Antagonismus, bei dem ein im Überschuss vorliegendes Ion ein anderes unterdrückt. **Die Korrektur ist hier nicht mehr vom fehlenden Nährstoff.** Ein Lauf, der diesen Zustand nicht von Unterversorgung trennen kann, sagt das und schlägt keine Düngung vor.

Was den ersten vom dritten Zustand trennt, ist fast nie das Blatt. Es ist ein pH- oder EC-Messwert, und wo keiner existiert, ist dessen Erhebung die empfohlene Maßnahme.

## Was Art und Pflanze verändern

Die Art setzt die Vorannahme; sie setzt nicht die Diagnose.

| Quelle | Verschiebt |
|--------|------------|
| `nutrient_demand_level` aus `get_species_info` | Die Plausibilität einer Unterversorgung bei gegebener Düngehäufigkeit — ein `medium_feeder` und ein Starkzehrer vertragen verschiedene Intervalle |
| Aktuelle Phase und ihr `target_ec_ms` im Plan | Das Ziel, gegen das das Ist verglichen wird; derselbe EC ist in einer Phase richtig und in der nächsten zu hoch |
| `phase_started_at` gegen `week_start` / `week_end` des Plans | Welche Planphase jetzt tatsächlich gilt, was einen Zielvergleich erst berechtigt statt bloß ungefähr macht |
| Substrat-`ph_base`, `buffer_capacity`, `cec_meq_per_100g` | Wie weit ein Messwert driften darf, bevor er ein Befund ist, und wie schnell eine Korrektur wirkt |
| `recommended_substrate_type` gegen das tatsächliche Medium | Ob die Planziele überhaupt für die Lage dieser Pflanze geschrieben wurden; eine Abweichung ist ein eigener Befund |
| `allows_harvest` und `harvest_months` der Art | Ob eine Korrektur auf eine nahende Ernte Rücksicht nehmen muss, samt Karenzzeit einer beteiligten Behandlung |
| Sorten-`days_to_maturity` und Merkmale | Der Phasenzeitplan, gegen den die Wochenfenster des Plans gelesen werden |

Ist kein Plan zugewiesen — ein gemessen realer und häufiger Zustand —, fällt der Prozess auf `nutrient_demand_level` der Art und die Phasendefinition zurück, sagt, dass er das tat, und beschränkt sich auf eine qualitative Richtung. Er erfindet keinen `target_ec_ms`.

## Ausgabe und Grenzen

Der Prozess ist standardmäßig nur lesend: Er liest die Akte, darf `calculate_mixing_protocol` aufrufen, weil dieses Tool ausschließlich rechnet, und berichtet. Eine Variante, die ihr Ergebnis über `add_plant_diary_entry` als Tagebucheintrag festhält, schreibt und ist damit ein eigenes `-apply`-Rezept nach der Namensregel des Rezept-Projektmusters.

Eine vorgeschlagene Korrektur nennt das angestrebte Ziel, die Belegstufe dahinter und ihre Annahme über das Ausgangswasser. Sie ist ein Vorschlag an einen Menschen, nie eine Anweisung an ein Gerät.

## Anforderungen

- **MUSS [MUST]** die Richtung — Unterversorgung, Überversorgung oder Nichtverfügbarkeit bei ausreichender Versorgung — bestimmen, bevor eine Korrektur vorgeschlagen wird, und **DARF NICHT [MUST NOT]** diese Richtung allein aus sichtbaren Symptomen ableiten
- **MUSS [MUST]** jede Aussage mit der Belegstufe kennzeichnen, auf der sie ruht, und **DARF NICHT [MUST NOT]** eine niedrigere Stufe eine höhere aufheben lassen
- **MUSS [MUST]** keine Dosisänderung vorschlagen, wenn die höchste verfügbare Belegstufe 3 oder darunter liegt, und **MUSS [MUST]** stattdessen die Messung benennen, die die Richtung klären würde
- **MUSS [MUST]** `ph_base`, `ec_base_ms`, `buffer_capacity` und `cec_meq_per_100g` des Substrats lesen, bevor beurteilt wird, ob eine Zufuhrhöhe übermäßig ist, da dieselbe Gabe je Medium anders wirkt
- **MUSS [MUST]** gegen die Planphase vergleichen, die zum Datum des Eintrags gilt, aufgelöst über `phase_started_at` und `week_start` / `week_end` der Phase, nicht gegen den Plan als Ganzes
- **MUSS [MUST]** benennen, dass kein Plan zugewiesen ist, und auf `nutrient_demand_level` und die Phasendefinition zurückfallen, wenn `get_plant_nutrient_plan` `plan: null` liefert, und **DARF NICHT [MUST NOT]** in diesem Fall einen `target_ec_ms` konstruieren
- **MUSS [MUST]** eine bestätigte Düngung im Pflegeprotokoll als Beleg dafür behandeln, dass gedüngt wurde, und **DARF NICHT [MUST NOT]** als Dosis; wo die Dosis zählt und nicht erfasst ist, wird die Lücke gemeldet
- **MUSS [MUST]** `measurements`-Schlüssel vor der Verwendung normalisieren und **MUSS [MUST]** einen Wert verwerfen, dessen Einheit oder Herkunft mehrdeutig ist, statt eine Konvention anzunehmen, die das offene Schema nicht festlegt
- **MUSS [MUST]** Nichtverfügbarkeit in Betracht ziehen, sobald Mangelsymptome mit einer Zufuhr auf oder über dem Phasenziel zusammenfallen, und **DARF NICHT [MUST NOT]** empfehlen, den betroffenen Nährstoff zu erhöhen, solange dieser Zustand nicht ausgeschlossen ist
- **MUSS [MUST]** seine Annahme über das Ausgangswasser (`base_water_ec`, `alkalinity_ppm`) nennen, wann immer es `calculate_mixing_protocol` aufruft, da das Ergebnis eine EC-Netto-Rechnung ist
- **DARF NICHT [MUST NOT]** in der nur lesenden Variante ein zustandsänderndes Tool aufrufen; die schreibende Variante **MUSS [MUST]** das Suffix `-apply` tragen, ihre Wirkung deklarieren und ihre Schreibvorgänge auf `add_plant_diary_entry` beschränken
- **DARF NICHT [MUST NOT]** Bewässerung, Dosierung oder irgendein Home-Assistant-Gerät ansteuern, wie eindeutig die Korrektur auch sein mag
- **SOLLTE [SHOULD]** Trockenheit, Wurzelschäden, Schädlingsdruck und Lichtstress als konkurrierende Erklärungen ausschließen, bevor eine Nährstoffursache festgelegt wird, gestützt auf `get_plant_inspections` und den Bildprozess, statt deren Arbeit zu wiederholen
- **SOLLTE [SHOULD]** eine Abweichung zwischen dem `recommended_substrate_type` des Plans und dem tatsächlichen Medium als Befund melden, da sie jeden nachgelagerten Zielvergleich untergräbt
- **SOLLTE [SHOULD]** das Pflegeprotokoll auf `snoozed`-Aktionen lesen, besonders beim Umtopfen, und Substraterschöpfung als Ursache scheinbarer Unterversorgung abwägen
- **SOLLTE [SHOULD]** eine nahende Ernte in jeder empfohlenen Korrektur berücksichtigen, wenn die Art `allows_harvest` trägt, und die Karenzzeit nennen, wo eine Behandlung beteiligt ist
- **SOLLTE [SHOULD]** angeben, wie lange eine Korrektur bis zur Wirkung braucht, abgeleitet aus der Pufferung des Substrats, damit ein Mensch nicht zu früh nachkorrigiert
- **KANN [MAY]** `calculate_mixing_protocol` aufrufen, um eine Korrektur zu beziffern, da es nichts speichert, und **KANN [MAY]** `list_fertilizers` mit `organic_only` lesen, wenn das Regime der anbauenden Person es verlangt
- **KANN [MAY]** einen Mangelverdacht zur Symptomverortung an den Bildprozess zurückgeben und **KANN [MAY]** umgekehrt von diesem aufgerufen werden

## Akzeptanzkriterien

- [ ] Jede vorgeschlagene Korrektur nennt eine Richtung und die Belegstufe, die sie begründet hat
- [ ] Ein Lauf ohne Messwert und ohne Plan schlägt keine Dosis vor und benennt die benötigte Messung
- [ ] Eine Pflanze mit `plan: null` ergibt dennoch eine qualitative Einschätzung, ausdrücklich als planlos gekennzeichnet
- [ ] Kein Ergebnis empfiehlt, einen Nährstoff zu erhöhen, solange Nichtverfügbarkeit bei ausreichender Versorgung nicht ausgeschlossen ist
- [ ] Substrateigenschaften erscheinen in der Begründung jeder Aussage über einen Überschuss
- [ ] Zielvergleiche nennen die konkrete Planphase und ihr Wochenfenster, nicht den Plan als Ganzes
- [ ] Ein `measurements`-Wert mit mehrdeutiger Einheit wird mit angegebener Begründung verworfen, nicht still gedeutet
- [ ] Das nur lesende Rezept ruft kein zustandsänderndes Tool auf; die schreibende Variante trägt `-apply` und schreibt ausschließlich Tagebucheinträge
- [ ] Kein Rezept unter dieser Spec ruft ein Home-Assistant-Aktuierungstool auf
- [ ] Jeder `calculate_mixing_protocol`-Aufruf in einem Ergebnis ist von seinen Annahmen zum Ausgangswasser begleitet

## Offene Fragen

- Welche `measurements`-Schlüssel in den Tagebucheinträgen der Instanz tatsächlich vorkommen. Das Schema deklariert keine, sodass die von dieser Spec geforderte Normalisierungstabelle noch nicht aus Daten geschrieben werden kann, sondern nur aus Konvention.
- Ob Ablauf-EC und Tank-EC in der Akte unterscheidbar sind. Die Unterscheidung entscheidet, ob ein Messwert beschreibt, was die Pflanze erhält, oder was im Medium zurückbleibt, und nichts im offenen Schema trennt beides.
- Ob Home Assistant Sensoren für Bodenfeuchte oder Leitfähigkeit führt, die Belege der Stufe 1 je Pflanze liefern könnten, und wie ein Sensor an eine Pflanzeninstanz gebunden würde. `GetLiveContext` liefert Entity-Zustände, eine Zuordnung Pflanze-zu-Entity wurde nicht gefunden.
- Ob die nennenswerten Antagonismen (welches Ion welches unterdrückt) in diese Spec gehören, in das über `search_glossary` erreichbare Glossar des Backends oder in die Wissensbasis. Sie hier zu kodieren, birgt dieselbe Drift, die dieses Repository bei Artdaten vermeidet.
- Wie ein Plan zu gewichten ist, dessen `is_global_template` wahr ist und dessen `tags` eine andere Kultur nennen als die Art der Pflanze — gemessen sind die Pläne der Referenzinstanz weitgehend cannabis-spezifische Vorlagen, ihre Pflanzen jedoch nicht.
- Ob sich „Zufuhr über dem Ziel" ohne Dosierprotokolle überhaupt rekonstruieren lässt oder ob Stufe 2 in der Praxis auf Stufe 3 zusammenfällt für alle, die Erinnerungen bestätigen, aber keine Mengen erfassen.

## Quelle

- Gemessen gegen die Kamerplanter-Referenzinstanz am 2026-08-05 über `POST /api/v1/mcp`, nur lesend: `get_plant_nutrient_plan` (lieferte `plan: null`), `list_nutrient_plans` (38 Pläne), `get_nutrient_plan` für die Phasenstruktur einer globalen Vorlage, `get_plant_care_log`, `list_substrates` und `get_species_info`. Kein Schreib-Tool wurde aufgerufen.
- Eingabeschemata von `calculate_mixing_protocol` und `add_plant_diary_entry` live gelesen, einschließlich des offenen Objekts `measurements` und des Enums `DiaryEntryType` (`observation`, `problem`, `milestone`, `measurement`, `photo`, `note`)
- Begleitender Prozess: [bildgestützte Pflanzengesundheitsanalyse](../plant-health-image-analysis/de.md)
- Rezept-Mechanik: [Goose-Rezept-Projektmuster](../../goose/recipe-project-pattern/de.md)
- Server-Vertrag: [Spec zum Kamerplanter-MCP-Server](../../mcp/kamerplanter-mcp-server/de.md)
