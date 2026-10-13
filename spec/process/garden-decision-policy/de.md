# Entscheidungsregeln für den Garten

Status: Entwurf
Portfolio-Scope: local

## Kontext

Jeder Garten-Skill in diesem Repository endet damit, einer Person zu sagen, was sie mit einer lebenden Pflanze tun soll, und jeder entscheidet für sich, was er glaubt. Der Nährstoffprozess ordnet fünf Belegstufen, der Schädlingsprozess fünf andere, und die Skills, die ein Foto oder ein Pflegeprotokoll lesen, tragen den Rest in Prosa. Das funktioniert, solange jeder Skill genau eine Frage beantwortet. Es funktioniert nicht mehr, wenn eine Empfehlung mehrere Fragen verbinden muss — Gießen gegen einen Nährstoffwert gegen einen Schädlingsverdacht —, weil sich die Stufen des einen Prozesses nicht mit denen des anderen vergleichen lassen und nichts sagt, was gewinnt, wenn sie sich widersprechen.

Diese Spezifikation legt dafür eine Regel fest: wie Belege geordnet werden, welche Regeln eine Empfehlung nie brechen darf, was eine Empfehlung offenlegen muss und was eine normalisierte Sicht auf einen Garten über die Felder sagen muss, die sie nicht füllen konnte. Sie legt die Regeln fest; die Skills `decision-policy` und `garden-context` wenden sie an, und das Rezept `garden-context-check` berichtet, was der zweite gefunden hat.

Die Regeln gibt es wegen dreier Fehlerformen, die in einer Nachbarspezifikation jeweils beobachtet wurden. Ein auf dem Foto gelesenes Symptom wird für die Ursache gehalten. Eine fällige Erinnerung wird für einen Bedarf gehalten. Eine fehlende Messung wird durch eine plausible ersetzt. Jede ist billig zu begehen und teuer zu bemerken, weil die Ausgabe weiterhin wie eine Antwort aussieht.

Alles zur Werkzeugoberfläche stammt aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md), zuletzt am 2026-08-16 an der Referenzinstanz gemessen. **Nichts in dieser Spezifikation wurde beim Schreiben erneut an einer laufenden Instanz gemessen**: Der `kamerplanter`-MCP-Server war in der Sitzung, die sie entworfen hat, nicht erreichbar (`INVALID_CONFIG`). Werkzeugnamen sind deshalb aus jener Spezifikation übernommen; ob ein Name noch existiert und was seine Antwort trägt, bleibt unbelegt, bis ein `tools/list` und ein lesender Aufruf an einer erreichbaren Instanz es sagen.

Grenzen: [Der Nährstoffprozess](../nutrient-imbalance-detection/de.md) und [der Schädlingsprozess](../pest-pressure-assessment/de.md) besitzen ihre eigenen Belegleitern und die damit getroffenen Entscheidungen. Diese Spezifikation ändert keine von beiden; sie setzt sie zu einer gemeinsamen Rangfolge in Beziehung und listet, wo sie sich widersprechen. Das Audit, das entscheidet, welches Artefakt was besitzt und ob eines davon umbenannt, zusammengelegt oder abgelöst wird, ist eine eigene Arbeit und wird als nolte/kamerplanter-goose#39 geführt; nichts hier greift ihm vor. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt die Rezeptmechanik, und [die Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md) besitzt Transport, Authentifizierung und Mandantenfähigkeit.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository sowie alle, die eine von ihnen erzeugte Empfehlung prüfen, bevor sie danach handeln.

## Ziele

- Jede Empfehlung benennt, worauf sie ruht, und die Leserin kann einen gemessenen Wert von einem Katalog-Standardwert und von Allgemeinwissen unterscheiden
- Belege niedrigeren Rangs stützen oder widersprechen Belegen höheren Rangs und überstimmen sie nie
- Eine fehlende Eingabe wird als fehlend gemeldet; die Empfehlung verschlechtert sich auf eine benannte Weise, statt die Lücke zu füllen
- Konfidenz und Unsicherheit sind Teil der Ausgabe, kein Tonfall
- Ein normalisierter Gartenkontext sagt, welche Felder er enthält und welche er nicht füllen konnte, samt Grund

## Nicht-Ziele

- Eine bestimmte Frage entscheiden — Richtung eines Nährstoffproblems, Haltbarkeit eines Schädlingsverdachts, ein Gießintervall. Das tun die Prozesse, denen sie gehören
- Eine Empfehlung ausführen, eine Aufgabe bestätigen oder einen Datensatz ändern
- Einen bestehenden Skill, ein Rezept oder eine Spezifikation umbenennen, zusammenlegen, aufteilen oder ablösen — das ist das als nolte/kamerplanter-goose#39 geführte Audit
- Ein Werkzeug spezifizieren, das der Server-Katalog nicht nennt. Wo ein Feld im gemessenen Katalog keine Quelle hat, sagt diese Spezifikation es
- Eine Laboranalyse, ein gartenbauliches Nachschlagewerk oder das Urteil einer Person ersetzen

## Anforderungen

### A. Die Belegrangfolge

Belege werden in acht Stufen geordnet, höchste zuerst. Der Rang wandert mit jeder Aussage in die Ausgabe.

| Stufe | Beleg | Quelle im gemessenen Katalog | Nicht belegt |
|-------|-------|------------------------------|--------------|
| 1 | Eine aktuelle Messung: ein Wert mit erkennbarer Einheit, für diese Pflanze erfasst, für die Frage aktuell genug | Tagebucheinträge mit `measurements`: `list_diary_entries`, `get_diary_entry` | Was „aktuell genug“ je Frage heißt (siehe Offene Fragen). Das Objekt `measurements` hat keinen festen Schlüsselsatz, der Schlüssel wird also normalisiert oder abgelehnt, nie angenommen |
| 2 | Eine historische Messung dieser Pflanze, zu alt, um jetzt zu beschreiben, aber noch beschreibend für die Pflanze | Dieselben Tagebucheinträge; `get_plant_diagnostics` | Die Felder, die `get_plant_diagnostics` liefert, sind in der Server-Spezifikation nicht aufgezählt |
| 3 | Eine bestätigte Beobachtung: etwas, das eine Person oder ein erfasster Prozess über diese Pflanze festgestellt hat | `get_plant_inspections` (IPM-Historie), `get_plant_care_log` (`confirmed_at`, `interval_at_time_days`), Tagebucheinträge vom Beobachtungstyp | Ob ein Tagebucheintrag von einer Person bestätigt wurde, ist kein Feld, das die Server-Spezifikation nennt |
| 4 | Kamerplanter-Art- und Sortendaten, die Sorte vor der Art | `get_cultivar`, `list_cultivars`, `get_species_info`, `get_species_lifecycle`, `get_species_phase_sequence`, `list_phase_definitions`, `get_plant_phase_status`, `get_plant_nutrient_plan` | `get_plant_phase_status` kann mit `phase_state: unresolved` antworten, was wie ein Normalergebnis aussieht und keines ist |
| 5 | Standortdaten: was darüber bekannt ist, wo die Pflanze steht | `site_key` und `location_key` einer Pflanze aus `list_plants` / `get_plant`; `list_plants_at_location`; `list_substrates`; `list_hardiness_zones` | **Im gemessenen Katalog ist kein lesendes Werkzeug für die eigenen Eigenschaften eines Standorts genannt.** Die Schlüssel bezeichnen einen Standort; wie er beschaffen ist, ist nicht gemessen |
| 6 | Wetter | **Keine Quelle gemessen.** Der Server-Katalog nennt kein Wetterwerkzeug; der Home-Assistant-Server veröffentlicht Entitätszustände über `GetLiveContext`, und ob eine Wetterentität bereitsteht, ist nicht gemessen | Alles |
| 7 | Eine dokumentierte Fachquelle: eine zitierte Referenz, nicht die Erinnerung des Modells | `search_plant_knowledge` ist deklariert; am 2026-08-16 gemessen antwortete es mit `service.unavailable`, weil die Wissensbasis eine optionale, auf der Referenzinstanz nicht bereitgestellte Komponente ist. `search_glossary` liefert die projekteigenen Begriffsdefinitionen, das ist Vokabular, kein Beleg | Ob irgendeine Instanz die Wissensbasis bereitstellt |
| 8 | Allgemeinwissen des Modells, das in keinem Datensatz steht | Keine, per Definition | Wird stets als nicht aus dem Datensatz gekennzeichnet |

- **MUSS [MUST]** jede Aussage einer Empfehlung genau einer Stufe zuordnen und die Stufe mit der Aussage in die Ausgabe mitführen
- **DARF NICHT [MUST NOT]** Belege einer niedrigeren Stufe Belege einer höheren Stufe überstimmen lassen; niedrigere Belege stützen oder widersprechen, und ein Widerspruch wird als solcher gemeldet, nicht stillschweigend zugunsten des niedrigeren aufgelöst
- **MUSS [MUST]** Belege der Stufe 8 überall, wo sie auftreten, als nicht aus dem Datensatz kennzeichnen
- **MUSS [MUST]** innerhalb von Stufe 4 Sortendaten vor Artdaten für dasselbe Attribut bevorzugen
- **DARF NICHT [MUST NOT]** eine Stufe, für die der gemessene Katalog keine Quelle nennt, als verfügbar behandeln; das Feld wird mit dem Grund „keine Quelle gemessen“ als fehlend gemeldet

### B. Kernregeln

- **DARF NICHT [MUST NOT]** aus einem einzelnen Symptom diagnostizieren. Eine Diagnose nennt mindestens einen weiteren Beleg, der nicht dieses Symptom ist, oder wird als Verdacht gekennzeichnet
- **DARF NICHT [MUST NOT]** allein deshalb Gießen empfehlen, weil eine Erinnerung fällig ist. Eine fällige Aufgabe ist eine Anforderung des Plans; die Empfehlung nennt zusätzlich den Beleg über den aktuellen Zustand der Pflanze, der sie stützt, oder sagt, dass es keinen gibt
- **MUSS [MUST]** einen gemessenen Wert dem Allgemeinwissen über dieselbe Größe vorziehen und sagen, wenn sie eine Messung als veraltet ablehnt
- **MUSS [MUST]** sortenspezifische Daten den Artstandardwerten vorziehen, wenn beide für dasselbe Attribut vorliegen, und benennen, welche sie verwendet hat
- **MUSS [MUST]**, wenn eine Umweltursache unter den Kandidaten ist, sie benennen und ihre Korrektur vor einer Behandlung der Pflanze vorschlagen, und sagen, warum, wenn sie es nicht tut
- **DARF NICHT [MUST NOT]** eine Messung erfinden. Ein Wert, der nicht im Datensatz steht, wird als fehlend gemeldet, zusammen mit der Beobachtung, die ihn liefern würde

### C. Die Ausgabe einer Empfehlung

- **MUSS [MUST]** mit jeder Empfehlung eine Belegliste zurückgeben, in der jeder Eintrag seine Stufe, seine Quelle (Werkzeug oder Dokument) und den Abrufzeitpunkt trägt
- **MUSS [MUST]** eine Konfidenz für die Empfehlung zurückgeben und **MUSS [MUST]** sie aus der höchsten Stufe ableiten, die sie stützt, nicht aus der Flüssigkeit des Textes
- **MUSS [MUST]** eine Unsicherheitsaussage zurückgeben, die benennt, was die Empfehlung ändern würde
- **MUSS [MUST]** eine Liste fehlender Daten zurückgeben, die jede Eingabe benennt, die die Empfehlung verwendet hätte und nicht hatte
- **MUSS [MUST]**, wo der Prozess, dem die Frage gehört, unterhalb einer benannten Belegstufe keine Handlung vorschlägt, diesem Prozess folgen; diese Spezifikation setzt keine eigene Schwelle
- **DARF NICHT [MUST NOT]** eine Empfehlung als Anweisung an ein Gerät oder als Schreibzugriff formulieren; eine Empfehlung ist ein Vorschlag an eine Person

### D. Der Gartenkontext

Ein Gartenkontext ist eine normalisierte Sicht auf einen Garten. Er ist ein Wert, der zwischen Schritten weitergereicht wird, kein Speicher.

| Feld | Quelle im gemessenen Katalog | Nicht belegt |
|------|------------------------------|--------------|
| Standort und Ort | `site_key`, `location_key` aus `list_plants` / `get_plant`; `list_plants_at_location` | Eigenschaften des Standorts selbst: kein lesendes Werkzeug genannt |
| Beete und Gefäße | Keine Quelle gemessen | Ob ein Ort ein Beet oder ein Gefäß ist, ist kein Feld, das die Server-Spezifikation nennt |
| Kulturen und Sorten | `list_plants` (`species_key`), `get_species_info`, `list_cultivars`, `get_cultivar` | — |
| Pflanzdurchläufe | `list_planting_runs` | Das Paginierungsverhalten ist nicht gemessen |
| Wachstumsstadium | `current_phase_key` aus `list_plants`; `get_plant_phase_status`, `get_plant_phase_history` | Ein Phasenzustand `unresolved` ist ein fehlendes Stadium, kein normales |
| Aktuelle Messungen | Tagebucheinträge (`list_diary_entries`, `get_diary_entry`) | Der Schlüsselsatz von `measurements` |
| Historische Beobachtungen | `get_plant_inspections`, `list_diary_entries`, `get_plant_care_log` | — |
| Wetter | Keine Quelle gemessen | Alles |
| Boden und Substrat | `substrate_key` aus `list_plants`; `list_substrates` | — |
| Gieß- und Düngezustand | `get_plant_care_log`, `get_due_care_tasks`, `list_tasks`, `get_plant_nutrient_plan` | Dosismengen: Das Pflegeprotokoll hält eine Bestätigung fest, keine Menge |
| Ziele und Einschränkungen der Nutzerin | Keine Quelle gemessen; kann vom Aufrufer geliefert werden | Ob irgendeine Instanz Ziele speichert |

- **MUSS [MUST]** jedes Feld des Kontexts als `present` oder `absent` melden und **MUSS [MUST]** jedem `present`-Feld sein Quellwerkzeug und den Abrufzeitpunkt mitgeben
- **MUSS [MUST]** jedem `absent`-Feld den Grund mitgeben: „keine Quelle gemessen“, die typisierte Absage des Servers oder das leere Ergebnis, und **DARF NICHT [MUST NOT]** es mit einem Standardwert füllen
- **MUSS [MUST]** den Garten ausdrücklich bestimmen, bevor irgendetwas gesammelt wird, über `list_tenants` oder eine `tenant`-Eingabe, gemäß der [Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md), und **DARF NICHT [MUST NOT]** annehmen, ein Schlüssel decke genau einen Garten ab
- **DARF NICHT [MUST NOT]** beim Sammeln eines Kontexts ein zustandsänderndes Werkzeug aufrufen; das Sammeln ist rein lesend
- **SOLLTE [SHOULD]** die Liste der fehlenden Felder als eigenen Block getrennt von den Daten ausgeben, damit ein nachgelagerter Schritt nicht daran vorbeiliest
- **KANN [MAY]** ein Feld vom Aufrufer annehmen — etwa Nutzerziele — und **MUSS [MUST]** dann dessen Quelle als den Aufrufer kennzeichnen, nicht als Werkzeug

### E. Beziehung zu den bestehenden Leitern

Die Leitern im [Nährstoffprozess](../nutrient-imbalance-detection/de.md) und im [Schädlingsprozess](../pest-pressure-assessment/de.md) ordnen Belege für je eine Frage. Sie bleiben für diese Frage maßgeblich.

| Bestehende Stufe | Nährstoffprozess | Schädlingsprozess | Stufe der Rangfolge |
|------------------|------------------|-------------------|---------------------|
| Messwert aus einem Tagebucheintrag | Stufe 1 | — | 1, oder 2, wenn nicht mehr aktuell |
| Erfasste Inspektion, die den Organismus nennt | — | Stufe 1 | 3 |
| Plansoll gegen rekonstruierte Versorgung | Stufe 2 | — | Keine Stufe: abgeleitet aus 3 und 4 (siehe Offene Fragen) |
| Katalogfelder | — | Stufe 2 | 4 |
| Muster im Pflegeprotokoll | Stufe 3 | — | 3 |
| Situationspassung: Kategorie, Phase, Jahreszeit, Pflegehistorie, Umgebung | — | Stufe 3 | 4 und 5, mit der Pflegehistorie bei 3 |
| Sichtbare Symptome aus einem Bild | Stufe 4 | Stufe 4 | Keine Stufe (siehe Offene Fragen) |
| Nährstoffbedarfsstufe der Art und Phasenerwartung | Stufe 5 | — | 4 |
| Allgemeinwissen über das Taxon, als nicht aus dem Datensatz gekennzeichnet | — | Stufe 5 | 8 |

- **MUSS [MUST]** die eigene Leiter eines Prozesses für die Entscheidungen maßgeblich halten, die ihm gehören, und **DARF NICHT [MUST NOT]** seine Stufen mit dieser Rangfolge neu ordnen
- **MUSS [MUST]** diese Rangfolge nutzen, um Belege prozessübergreifend zu vergleichen, wo zwei Leitern sonst nach Stufennummer verglichen würden
- **MUSS [MUST]**, wo diese Spezifikation und eine Prozessleiter sich widersprechen, den Widerspruch als Offene Frage festhalten und **DARF NICHT [MUST NOT]** ihn durch eine Änderung der anderen Spezifikation auflösen

## Akzeptanzkriterien

- [ ] Ein Skill, der diese Regeln anwendet, gibt zu jeder Empfehlung eine Belegliste mit Stufe, Quelle und Abrufzeitpunkt, eine Konfidenz, eine Unsicherheitsaussage und eine Liste fehlender Daten zurück
- [ ] Keine Empfehlung in einem geprüften Lauf ruht auf einem einzelnen Symptom, auf einer fälligen Erinnerung allein oder auf einer Messung, die nicht im Datensatz steht
- [ ] Ein Lauf folgt der Schwelle des Prozesses, dem seine Frage gehört, und die Ausgabe dieser Spezifikation fügt keine hinzu
- [ ] Ein Gartenkontext führt jedes Feld aus Abschnitt D als vorhanden oder fehlend; jedes fehlende Feld nennt seinen Grund; kein fehlendes Feld enthält einen Standardwert
- [ ] Beete und Gefäße, Wetter und Nutzerziele werden mit „keine Quelle gemessen“ als fehlend gemeldet, es sei denn, ein in der Server-Spezifikation genanntes Werkzeug oder der Aufrufer liefert sie
- [ ] Der Sammelschritt ruft kein zustandsänderndes Werkzeug auf und bestimmt den Mandanten, bevor er etwas liest
- [ ] Keine der beiden bestehenden Leitern wird durch die Arbeit geändert, die diese Spezifikation umsetzt, und jeder Widerspruch zwischen den beiden Regelwerken steht unter Offene Fragen
- [ ] Jede Aussage über die Werkzeugoberfläche zitiert die Server-Spezifikation; eine nicht erneut gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Zahl an Anforderungs-Aufzählungspunkten und dieselbe Zahl an Akzeptanz-Kontrollkästchen

## Quelle

- [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — Werkzeugkatalog, Vorbehalte und Mandantenfähigkeit, am 2026-08-16 an der Referenzinstanz gemessen
- [Nährstoffprozess](../nutrient-imbalance-detection/de.md) — §„Die Belegleiter“
- [Schädlingsprozess](../pest-pressure-assessment/de.md) — §„Die Belegleiter“
- [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Issue nolte/kamerplanter-goose#40 — die acht Stufen und sechs Regeln stammen aus seinem Text; nolte/kamerplanter-goose#39 — das Audit, dem die Zuständigkeitsgrenzen gehören

## Offene Fragen

- **Wo ein Fotobefund einzuordnen ist.** Beide bestehenden Leitern ordnen ein aus einem Bild gelesenes Symptom an vierter Stelle ein; diese Rangfolge hat dafür keine Stufe. Ein durch eine Person oder eine erfasste Inspektion bestätigter Befund gehört auf Stufe 3, ein unbestätigter Befund eines Modells ist aber weder eine bestätigte Beobachtung noch Allgemeinwissen. Offen, weil die Einordnung ändert, was ihn überstimmt: Auf Stufe 3 würde er Artdaten überstimmen, was beide bestehenden Prozesse ihm verwehren. Gemeinsam mit dem Audit zu entscheiden, nolte/kamerplanter-goose#39.
- **Wo abgeleiteter Beleg einzuordnen ist.** Stufe 2 des Nährstoffprozesses verbindet ein Plansoll, eine bestätigte Häufigkeit und eine Substratbasis zu einer rekonstruierten Versorgung. Die Rangfolge ordnet Quellen, keine Ableitungen, und gibt einer solchen Ableitung keine Stufe. Offen, weil die Ableitung dem Nährstoffprozess selbst gehört und ihre Einordnung hier seine Leiter neu ordnen würde. Ob die offene Frage des Nährstoffprozesses zu Stufe 2 ohne Dosisaufzeichnungen daran etwas ändert, wird hier nicht entschieden.
- **Ob die Rangfolge global oder je Frage gilt.** Die bestehenden Leitern ordnen Belege für eine Frage und lassen einen Artwert die niedrigste Stufe sein; diese Rangfolge stellt Artdaten über Standortdaten und Wetter. Für eine Frage, bei der das Wetter entscheidet — ein Frost, eine Hitzespitze —, kann eine globale Ordnung die falsche sein. Offen, weil bisher kein Prozess in diesem Repository beide Ordnungen zugleich brauchte.
- **Ob eine gemeinsame Handlungsschwelle nötig ist.** Der Nährstoffprozess schlägt keine Dosisänderung vor, wenn sein bester Beleg auf seiner Stufe 3 oder darunter liegt, und der Schädlingsprozess schlägt eine Behandlung nur vor, wenn die Bestimmung auf seiner Stufe 1 oder auf seiner Stufe 4 plus einer nicht widerlegten Stufe 2 ruht; das sind Schwellen auf zwei verschiedenen Leitern, und diese Spezifikation setzt keine. Offen, weil eine auf der Rangfolge formulierte Schwelle mit beiden abgestimmt werden müsste und die Zuordnung in Abschnitt E durch Lesen entstand, nicht dadurch, dass ein Fall durch beide geführt wurde.
- **Was „aktuell genug“ für Stufe 1 heißt.** Der Nährstoffprozess sagt „wenn aktuell genug“ ohne Schwelle; kein Prozess nennt eine je Größe. Offen, weil die Schwelle davon abhängt, wie schnell sich die Größe ändert (ein Bodenfeuchtewert und ein EC-Wert altern nicht gleich), und es dafür keine gemessene Quelle im Datensatz gibt.
- **Ob eine laufende Instanz Quellen bietet, die diese Spezifikation mit „keine Quelle gemessen“ markiert.** Niemand hat ein `tools/list` an einer erreichbaren Instanz auf Beet-, Gefäß-, Wetter- oder Zielwerkzeuge ausgeführt; der Server war beim Schreiben dieser Spezifikation nicht erreichbar. Die Felder bleiben fehlend, bis eine Messung etwas anderes sagt, und ein gefundenes Werkzeug verschiebt das Feld, nicht den Vertrag.
- **Ob die Wissensbasis bereitstellbar ist.** `search_plant_knowledge` ist deklariert und wurde als nicht verfügbar gemessen; Stufe 7 hat auf der gemessenen Instanz keine funktionierende Quelle. Offen, weil sie eine optionale Komponente ist und nichts im Datensatz sagt, ob der Betreiber sie bereitstellen will.
- **Welches Artefakt was besitzt.** `plant-context-collect` sammelt den Kontext einer Pflanze, und der Kontextvertrag in Abschnitt D sammelt den Kontext eines Gartens; wo das eine endet und das andere beginnt und ob die bestehenden Leitern in einen gemeinsamen Skill wandern, entscheidet das Audit, nolte/kamerplanter-goose#39.
