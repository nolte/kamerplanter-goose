# Beetaufteilung und Folgesaatplanung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Ein Pflanzplan sagt, wann jede Kultur in den Boden kommt und wann sie ihn verlässt; ein Fruchtfolgeplan sagt, welche Pflanzenfamilie in einer Saison in welchem Beet stehen darf. Keiner von beiden sagt, wie viel eines Beets eine Kultur beansprucht, ob die Kulturen, die einem Beet zugeteilt sind, Monat für Monat hineinpassen, welche Kulturen nebeneinander stehen oder welche Kultur im selben Beet auf eine andere folgt. Das ist Beetaufteilung und Folgesaat. Hier ist ein Verfahren, das aus Allgemeinwissen arbeitet, auch am stärksten versucht, Zahlen zu ergänzen: ein erinnerter Abstand, eine erinnerte Liste schlechter Nachbarn, ein erinnertes „alle zwei Wochen säen“. Eine Aufteilung, die darauf ruht, liest sich wie der Plan eines Gärtners und ruht auf nichts, was der Garten ihr gesagt hat.

Das Issue, das dies angefordert hat, nolte/kamerplanter-goose#46, ging davon aus, dass Abstände, Licht, Zugang, Bewässerung und unverträgliche Nachbarn Katalogdaten sind. Die gemessene Oberfläche enthält viel weniger. Beete und Gefäße haben keine Quelle ([die Entscheidungsregeln für den Garten](../garden-decision-policy/de.md)); Licht und Exposition, Fläche und Volumen sowie Wasser haben keine ([Standortanalyse](../site-analysis-and-crop-selection/de.md) §A); ein Feld für den Zugang kommt in den Spezifikationen dieses Repositorys nirgends vor. `get_species_info` trägt `compatible_companions[]` mit einem `score`, dessen Wertebereich und Richtung nicht festgehalten sind, und kein Feld für unverträgliche oder gegnerische Arten; ein Paar, das nicht aufgeführt ist, ist unbekannt, nie unverträglich. `seed_profile.sowing_density_per_m2` existiert, gemessen an einer Art, und ob es Samen oder Pflanzen zählt, ist nicht festgehalten. Kein Feld für den Abstand in der Reihe, zwischen den Reihen oder zwischen Pflanzen ist benannt. Diese Spezifikation nimmt daher Beete, Kapazität, Abstände, Mengen, Beetmerkmale und Unverträglichkeiten vom Aufrufer, nutzt die Nachbarliste des Katalogs nur als Eingabe für die Rangfolge und meldet alles andere als unbekannt.

Diese Spezifikation legt drei Schritte fest. Das Sammeln von Nachbarn und Saatdichte liest einmal je unterschiedlicher Art die Nachbarliste mit ihren Werten und die Saatdichte als Kontext. Die Folgesaatplanung findet in den Pflanzdurchläufen der [Spezifikation zur Pflanzplanung](../plant-planning-and-planting-calendar/de.md) und in den Feldern des [Fruchtfolgeplans](../crop-rotation-planning/de.md) die Durchläufe, die in einem Beet aufeinander folgen können, und die Durchläufe, die gestaffelt gesät werden können. Die Beetaufteilung verteilt Durchläufe und Folgesaaten auf die Beete des Aufrufers, prüft die Kapazität je Beet und Monat und begründet jede Platzierung und jeden ausgelassenen Durchlauf. Alle drei sind rein lesend. Eine Beetaufteilung ist ein Dokument; sie festzuhalten ist ein eigener Schritt, und der gemessene Katalog hat kein Werkzeug, das das könnte (Abschnitt G).

Alles zur Werkzeugoberfläche unten ist zitiert aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) und aus dem [Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md), deren Messungen am 2026-08-07 und 2026-08-16 an der Referenzinstanz gemacht wurden. **Nichts davon wurde beim Schreiben dieser Spezifikation erneut gemessen**: Der `kamerplanter`-MCP-Server war in der Sitzung, die sie entworfen hat, nicht erreichbar (`INVALID_CONFIG`). Werkzeug- und Feldnamen sind aus jenen Spezifikationen übernommen; ob sie noch existieren und was eine Antwort darüber hinaus trägt, bleibt unbelegt, bis ein `tools/list` und ein lesender Aufruf an einer erreichbaren Instanz es sagen.

Grenzen: Die [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) besitzen das Gewicht einer Aussage, die Form einer Empfehlung und den Gartenkontext; die [Spezifikation zur Pflanzplanung](../plant-planning-and-planting-calendar/de.md) besitzt die Pflanzdurchläufe und ihre Fenster; die [Spezifikation zur Fruchtfolgeplanung](../crop-rotation-planning/de.md) besitzt die Familie je Beet und Saison und die Fruchtfolgeurteile. Diese Spezifikation liest alle drei und wiederholt keine: Sie berechnet nie ein Fenster neu und leitet nie eine Fruchtfolge neu ab. Die `-apply`-Hälfte von nolte/kamerplanter-goose#46 ist in nolte/kamerplanter-goose#74 ausgelagert, blockiert. Das Audit, das entscheidet, welches Artefakt was besitzt, ist nolte/kamerplanter-goose#39, und nichts hier greift ihm vor. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt die Rezeptmechanik, und [die Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md) besitzt Transport, Authentifizierung und Mandantenfähigkeit.

Leser: Autoren von Garten-Skills und -Rezepten in diesem Repository und alle, die eine Beetaufteilung oder eine Folgesaat prüfen, bevor sie danach handeln.

## Ziele

- Jede Platzierung und jede Folgesaat nennt die Regel, die sie ergeben hat, die Eingaben, auf denen sie ruht, deren Quellen und die Belegstufe
- Eine Kapazität, die sich aus den Eingaben des Aufrufers nicht berechnen lässt, wird als `not validated` mit der fehlenden Eingabe gemeldet, nie geschätzt
- Eine Nachbarschaft ist eine Eingabe für die Rangfolge und wird als keine Garantie benannt; eine Unverträglichkeit gibt es nur, wo der Aufrufer sie nennt
- Eine Fruchtfolge wird übernommen, nie neu abgeleitet: Eine Kultur steht nur dort, wo der Fruchtfolgeplan sie zulässt
- Die Beetaufteilung ist eine Funktion ihrer Eingabeblöcke, sodass zwei Läufe über dieselben Blöcke dieselben Plan-Fakten ergeben
- Rein lesendes Planen und Festhalten sind getrennt, und eine Beetaufteilung kann geprüft werden, bevor etwas festgehalten wird

## Nicht-Ziele

- Eine Beetaufteilung, ein Beet, eine Beetzuordnung, eine Folgesaat oder einen Pflanzdurchlauf festhalten. Der gemessene Katalog hat dafür kein Werkzeug (Abschnitt G)
- Geometrie: Reihen, Positionen, Koordinaten oder Zeichnungen. Eine Beetaufteilung verteilt Fläche oder Volumen je Beet, nicht Positionen darin
- Licht, Zugang und Bewässerung als Platzierungsregeln. Kein Artfeld hält den Bedarf einer Kultur daran fest, daher sind die Beetmerkmale des Aufrufers Kontext, und ein Ausschluss ist das Regelmittel des Aufrufers
- Ein Pflanzfenster oder ein Fruchtfolgeurteil neu berechnen oder ändern, was die [Pflanzplanung](../plant-planning-and-planting-calendar/de.md) oder die [Fruchtfolgeplanung](../crop-rotation-planning/de.md) verlangen
- Ein Abstand, eine Dichte, eine Unverträglichkeit, ein Staffelabstand oder eine Nachbarwirkung aus Allgemeinwissen
- Eine Beetaufteilung über mehrere Saisons. Ein Lauf plant eine Saison

## Anforderungen

### A. Eingaben

| Eingabe | Quelle | Nicht belegt |
|---------|--------|--------------|
| Pflanzdurchläufe | [Pflanzplanung](../plant-planning-and-planting-calendar/de.md), ihre Blöcke `PLANTING RUNS` und `NOT PLANNED` | — |
| Fruchtfolgeplan | [Fruchtfolgeplanung](../crop-rotation-planning/de.md), ihre Blöcke `ROTATION PLAN` und `CONFLICTS`, für die eine Saison | — |
| Saison | Der Aufrufer: ein Jahr | — |
| Beete | Der Aufrufer: Einträge `name`, `name:<n>m2` (ein Beet, nach Fläche) oder `name:<n>l` (ein Gefäß, nach Volumen), durch Kommas getrennt; und jedes weitere Beet, für das der Fruchtfolgeplan in der Saison ein Feld hat, mit Kapazität `unknown` und Quelle `rotation plan` | Keine Quelle im gemessenen Katalog |
| Beetmerkmale | Der Aufrufer: Einträge `bed:light=<text>`, `bed:access=<text>` oder `bed:irrigation=<text>`, durch Semikolons getrennt | Keine Quelle; kein Artfeld hält den Bedarf fest |
| Abstände | Der Aufrufer: Einträge `species_key[:cultivar_key]=<n>/m2` (Pflanzen je m²) oder `species_key[:cultivar_key]=<n>l` (Liter je Pflanze), durch Kommas getrennt | Im Katalog ist kein Abstandsfeld benannt |
| Mengen | Der Aufrufer: Einträge `species_key[:cultivar_key]=<plants>`, durch Kommas getrennt | Keine Quelle |
| Staffelabstand | Der Aufrufer: `stagger_weeks`, eine ganze Zahl | Keine Quelle; keine Zahl ist eingebaut |
| Bedingungen | Der Aufrufer: Einträge durch Semikolons getrennt, `avoid=species_key[:cultivar_key]+species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]`, das `pin=` der Fruchtfolge oder freier Text | — |
| Nachbarn | `get_species_info`: `compatible_companions[]` mit `score`, Stufe 4 | Wertebereich und Richtung von `score`; die Form eines Eintrags über die Art hinaus, die er nennt |
| Saatdichte | `get_species_info`: `seed_profile.sowing_density_per_m2`, Stufe 4 | Ob sie Samen oder Pflanzen zählt und ob eine Sorte sie trägt |

- **MUSS [MUST]** jede Liste an ihrem Trennzeichen und jeden Eintrag an seinen Doppelpunkten, Gleichheitszeichen und Pluszeichen trennen und **DARF NICHT [MUST NOT]** den zusammengesetzten Text als Namen weitergeben; ein Beetname ist der Text vor dem ersten Doppelpunkt eines `beds`-Eintrags
- **MUSS [MUST]** die Kapazität eines Beets nur aus den Formen `<n>m2`, `<n>m²` und `<n>l` lesen, **MUSS [MUST]** jeden anderen Kapazitätstext wörtlich mit Kapazität `unknown` melden und **MUSS [MUST]** einen bloßen Namen als Beet unbekannter Kapazität behandeln
- **MUSS [MUST]** Beete, Beetmerkmale, Abstände, Mengen, den Staffelabstand, die Saison und die Bedingungen als Quelle `caller` kennzeichnen und **MUSS [MUST]** jede als nicht geliefert melden, wenn der Aufrufer sie leer ließ
- **MUSS [MUST]** Abstand und Menge einer Kultur aus ihrem Sorteneintrag nehmen, wenn es einen gibt, und sonst aus ihrem Arteintrag, und **MUSS [MUST]** sagen, welcher es war
- **MUSS [MUST]** jeden Eintrag, der sich nicht zerlegen lässt, und jede Bedingung in freiem Text wörtlich als `not evaluated` aufführen und **DARF NICHT [MUST NOT]** freien Text als Regel auslegen
- **MUSS [MUST]** anhalten und den fehlenden Block benennen, wenn die Pflanzdurchläufe oder der Fruchtfolgeplan nicht geliefert sind

### B. Nachbarn und Saatdichte

- **MUSS [MUST]** `get_species_info` einmal je unterschiedlicher Art unter den Kulturen der Pflanzdurchläufe lesen, mit `include_cultivars`, wenn eine Sorte genannt ist, und **DARF NICHT [MUST NOT]** für diesen Schritt ein anderes Werkzeug aufrufen
- **MUSS [MUST]** `compatible_companions[]` mit der Art und dem `score` jedes Eintrags wie festgehalten aufzeichnen, die Liste der Sorte vor der Liste der Art, mit ihrer Herkunft, und **MUSS [MUST]** eine fehlende Liste als `absent — not populated` melden
- **MUSS [MUST]** `sowing_density_per_m2` nur als Kontext melden, mit seiner Herkunft und dem Hinweis, dass die Bedeutung seiner Einheit nicht festgehalten ist, und **DARF NICHT [MUST NOT]** es als Kapazität, Abstand oder Pflanzenzahl verwenden
- **DARF NICHT [MUST NOT]** ein nicht aufgeführtes Paar als unverträglich lesen, **DARF NICHT [MUST NOT]** eine Unverträglichkeit aus irgendeinem Feld ableiten und **DARF NICHT [MUST NOT]** einen Abstand oder eine Dichte ergänzen

### C. Folgesaat

Die **Belegung** eines Durchlaufs sind die Monate von seinem ersten Saatmonat (`direct_sow`: der niedrigste Monat des Saatfensters) oder seinem Umpflanzmonat (`indoor_then_transplant`: der Monat des Umpflanzbeginns) bis zum höchsten Monat seines Erntefensters, innerhalb der Saison. Eine unbekannte Grenze macht die Belegung `unknown`. Ein Erntemonat, der niedriger ist als der Anfangsmonat, oder ein Saat- oder Umpflanzmonat, der höher ist als der höchste Erntemonat (Direktsaat in den Monaten 4, 5 und 8 mit Ernte in 6 und 7; Saat in 11, 12, 1 und 2 mit Ernte in 5 und 6), bedeutet, dass der Durchlauf über die Saisongrenze reicht, und seine Belegung ist `unknown — spans the season boundary`. Eine Kultur ist in einem Beet **zulässig**, wenn eine von zwei Klauseln gilt, in dieser Reihenfolge gelesen: erstens nennt ein `pin=` dieses Beet, die Saison und die Kultur, gleich in welchem Zustand das Feld ist, `occupied` eingeschlossen; sonst ist das Feld nicht festgelegt, und die Kultur gehört zu seiner gewählten Familiengruppe. Abgesehen von einer Festlegung lässt ein Feld, das `open` oder `occupied` ist, nichts zu.

- **MUSS [MUST]** eine **aufeinanderfolgende** Folgesaat nur für zwei Durchläufe vorschlagen, deren Kulturen beide im selben Fruchtfolgefeld zulässig sind, deren Belegungen beide bekannt sind und bei denen der höchste Erntemonat des früheren Durchlaufs niedriger ist als der Anfangsmonat des späteren
- **MUSS [MUST]** in jeder aufeinanderfolgenden Folgesaat beide Durchlaufkennungen nennen, **MUSS [MUST]** jedes Fenster, auf dem sie ruht, mit seiner Regel, seinen Feldern, seiner Quelle und seiner Stufe übernehmen und **MUSS [MUST]** die eigenen Hinweise `precedes` und `follows` der Pflanzplanung wörtlich mitführen
- **MUSS [MUST]** eine **gestaffelte** Folgesaat nur innerhalb eines bekannten Direktsaatfensters, nur für einen Durchlauf mit bekannter Belegung, nur innerhalb seiner Belegungsmonate und nur mit dem `stagger_weeks` des Aufrufers vorschlagen, die Saattermine als Abstände von so vielen Wochen ab dem ersten Tag jedes zusammenhängenden Blocks der Fenstermonate in der Saison aufführen, und **MUSS [MUST]** ohne ihn `staggering possible within <months> — interval not supplied` melden
- **DARF NICHT [MUST NOT]** eine Folgesaat aus Allgemeinwissen, aus Monaten, die sich nicht vergleichen lassen, oder über Kulturen hinweg vorschlagen, die das Fruchtfolgefeld nicht zulässt
- **MUSS [MUST]** jeden Durchlauf, der in keiner aufeinanderfolgenden Folgesaat steht, unter `NOT SUCCEEDED` mit einem Grund aufführen, dem ersten, der zutrifft: `method not chosen — set planting_method`, `outside rotation plan`, `occupancy unknown — <missing>`, `spans the season boundary`, `no other run in <slot>` oder `no run follows or precedes it in <slot>`

### D. Beetaufteilung und Kapazität

Der **Bedarf** eines Durchlaufs ist seine Menge geteilt durch die Pflanzen je m² für ein Beet oder seine Menge mal die Liter je Pflanze für ein Gefäß, wobei die Einheit des Abstands zur Einheit des Beets passt. Die **Kapazität je Monat** eines Beets ist geprüft, wenn die Kapazität des Beets, der Bedarf jedes Durchlaufs, der es in diesem Monat belegt, und deren Belegungen alle bekannt sind; sie ist dann `within` oder `over by <x>` und sonst `not validated — <missing input>`.

Ein Durchlauf ist in einem Beet **zulässig**, wenn seine Kultur dort zulässig ist (Abschnitt C), kein `exclude` dieses Beet und diese Kultur nennt, kein `avoid`-Paar ihn mit einem Durchlauf im Beet verbindet, dessen Belegung seine überlappt oder unbekannt ist, und seine Methode gewählt ist. Der Planer platziert in zwei Durchgängen, die jeweils die Durchläufe nach dem Anfangsmonat ihrer Belegung, unbekannte zuletzt, und dann nach Durchlaufkennung als Text durchgehen. Der erste Durchgang platziert die Durchläufe einer festgelegten Kultur im festgelegten Beet, im ersten nach Namen, wenn die Kultur in mehreren festgelegt ist. Die Beete der Beetaufteilung sind die `beds`-Einträge des Aufrufers und jedes weitere Beet, für das der Fruchtfolgeplan in der Saison ein Feld hat, letztere mit Kapazität `unknown`. Der zweite Durchgang platziert jeden anderen Durchlauf im ersten zulässigen Beet nach diesen Schlüsseln, streng in dieser Reihenfolge angewandt: Das Beet enthält einen aufeinanderfolgenden Vorgänger des Durchlaufs aus dem Folgesaatblock; geprüfte Kapazität passt, vor nicht geprüfter Kapazität; die höhere Summe numerischer Nachbarwerte mit den Durchläufen im Beet, deren Belegung seine überlappt; der Beetname als Text. Ein Beet, dessen geprüfte Kapazität überschritten würde, ist kein Kandidat für einen nicht festgelegten Durchlauf.

- **MUSS [MUST]** einen Durchlauf nur in einem Beet platzieren, dessen Fruchtfolgefeld seine Kultur zulässt, und **MUSS [MUST]** einen Durchlauf, dessen Kultur kein Feld zulässt, als `not placed — outside rotation plan` melden
- **MUSS [MUST]** die Durchläufe einer festgelegten Kultur im festgelegten Beet platzieren, auch wenn die Kapazität überschritten wird, **DARF NICHT [MUST NOT]** eine Festlegung verschieben und **MUSS [MUST]** die Überschreitung und jedes `avoid` oder `exclude`, das die Festlegung bricht, unter `CONFLICTS` aufführen; die Methodenregel unten hat Vorrang: Eine festgelegte Kultur, deren Methode nicht gewählt ist, wird nicht platziert und unter `CONFLICTS` als `pinned crop: method not chosen — set planting_method` aufgeführt, die Festlegung ungelöst, nicht verschoben
- **MUSS [MUST]** einen Durchlauf, den kein Beet aufnehmen kann, als `not placed — capacity` melden, wenn allein die Kapazität ihn aufhielt, und sonst als `not placed — no admissible bed`, und dabei je Beet die Prüfung nennen, die ihn aufhielt
- **MUSS [MUST]** die Kapazität je Beet und je Monat der Saison nur aus Kapazität, Abständen und Mengen des Aufrufers prüfen, **MUSS [MUST]** `not validated` mit der fehlenden Eingabe melden, wenn eine davon fehlt oder ihre Einheiten nicht passen, und **DARF NICHT [MUST NOT]** die Lücke aus `sowing_density_per_m2` oder aus Allgemeinwissen füllen
- **MUSS [MUST]** `avoid` als harte Bedingung durchsetzen: Zwei gemiedene Kulturen belegen nie ein Beet in überlappenden Monaten, wobei eine unbekannte Belegung als überlappend zählt
- **MUSS [MUST]** die Nachbarliste des Katalogs nur als Eingabe für die Rangfolge verwenden: Ein numerischer `score` zählt zur Summe, ein nicht numerischer zählt 0 und wird als `score not comparable` aufgeführt, ein nicht aufgeführtes Paar ist `unknown`, und der Plan **MUSS [MUST]** wörtlich angeben, dass eine Nachbarschaft eine Planungseingabe aus dem Katalog ist und keine Garantie für irgendein Ergebnis
- **MUSS [MUST]** eine höhere Nachbarsumme zuerst einreihen und **MUSS [MUST]** in der Begründung jeder Platzierung den festen Satz "companion score assumed higher = more favourable; the record does not state its direction" angeben
- **MUSS [MUST]** keinen der beiden Durchläufe platzieren, wenn die Pflanzplanung dieselbe Art, Sorte und Wachstumsperiode unter beiden Methoden anbietet, und **MUSS [MUST]** beide als `method not chosen — set planting_method` aufführen; Durchläufe verschiedener Wachstumsperioden sind getrennte Pflanzungen
- **MUSS [MUST]** die Beetmerkmale des Aufrufers je Beet und in der Begründung jeder Platzierung als Kontext melden und **DARF NICHT [MUST NOT]** sie über eine Platzierung entscheiden lassen
- **MUSS [MUST]** jeder Platzierung eine Begründung geben, die die Werte der Rangfolge, jedes nicht gewählte Beet mit seinem Grund, das übernommene Fruchtfolgeurteil mit seiner Stufe, die Beetmerkmale und die Aussage zur Nachbarschaft nennt; und **MUSS [MUST]** jedem nicht platzierten Durchlauf genau einen Grund geben

### E. Die Pläne und ihre Verbraucher

Der Folgesaatplan hat vier Blöcke, in dieser Reihenfolge und unter diesen Namen: `SUCCESSION HEADER` (der Garten, die Saison, der Staffelabstand oder `not supplied`, die Blöcke, aus denen er gemacht wurde), `SUCCESSIONS`, `NOT SUCCEEDED` und `APPLY CONTRACT`. Die Beetaufteilung hat sechs: `LAYOUT HEADER` (der Garten, die Saison, die Beete mit ihrer Kapazität und Quelle, die Abstände, die Mengen, die nicht ausgewerteten Einträge), `BED LAYOUT` (je Beet: seine Kapazität, seine Merkmale, seine Platzierungen mit ihrem Bedarf und ihrer Begründung), `CAPACITY` (je Beet und Monat), `CONFLICTS`, `NOT PLACED` und `APPLY CONTRACT`.

| Verbraucher | Liest |
|-------------|-------|
| Beetaufteilung | aus dem Folgesaatplan: das Feld jeder aufeinanderfolgenden Folgesaat und ihre beiden Durchlaufkennungen |
| Eine Person, die eine Beetaufteilung prüft | je Beet: die Platzierungen, die Kapazität je Monat, die Konflikte; je Durchlauf: wo er steht oder warum nicht |
| Das blockierte `-apply`-Folge-Issue (nolte/kamerplanter-goose#74) | den Block `APPLY CONTRACT` einer freigegebenen Beetaufteilung |

- **MUSS [MUST]** die Blöcke in diesen Reihenfolgen mit diesen Namen zurückgeben und **DARF NICHT [MUST NOT]** ein Feld zurückgeben, das nicht gelesen wurde, sondern ein ungelesenes Feld als fehlend mit seinem Grund aufführen
- **MUSS [MUST]** jeder Platzierung und jeder Folgesaat ihre Begründung, Zuversicht, Unsicherheit und fehlenden Daten nach den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) geben und **MUSS [MUST]** ihr die Stufe `caller` geben, wann immer ein Element von ihr vom Aufrufer stammt, und sonst die schwächste Stufe unter ihren Elementen
- **MUSS [MUST]** die Konflikte des Fruchtfolgeplans für die Saison in `CONFLICTS` übernehmen, neben die eigenen der Beetaufteilung

### F. Determinismus

- **MUSS [MUST]** jeden Plan zu einer Funktion der gelieferten Eingabeblöcke und der Regeln machen, sodass zwei Läufe über dieselben Blöcke dieselben Plan-Fakten ergeben: die Platzierungen, die Bedarfe, die Kapazität je Beet und Monat, die Konflikte, die Gründe für „nicht platziert“, die Folgesaaten und die Belegstufen
- **DARF NICHT [MUST NOT]** die Reihenfolge der Eingabe oder das aktuelle Datum über einen Plan-Fakt entscheiden lassen; Abrufzeitpunkte werden neben den Fakten berichtet und nicht verglichen
- **MUSS [MUST]** angeben, dass bytegleicher Text außerhalb der Plan-Fakten nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage aus Eingabeblöcken geprüft wird und nicht an einem laufenden Garten

### G. Trennung und Anwendungsvertrag

- **MUSS [MUST]** Beetaufteilung und Folgesaatplanung rein lesend halten: Die Skills und Rezepte dieser Spezifikation rufen kein Werkzeug auf, das Zustand ändert
- **MUSS [MUST]** in jeden Plan einen Block `APPLY CONTRACT` aufnehmen, der je Platzierung oder Folgesaat angibt, was ein späteres `-apply`-Rezept festhalten müsste (das Beet, seine Kapazität, den Durchlauf, seinen Bedarf, die Saison, seine Vorgänger), und **MUSS [MUST]** angeben, dass der gemessene Katalog kein Werkzeug hat, das ein Beet anlegt, eine Beetzuordnung oder eine Beetaufteilung festhält oder einen Pflanzdurchlauf anlegt: Die Schreibwerkzeuge, die er verzeichnet, sind `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` und `create_inspection`, dazu das Einrichtungswerkzeug `create_site`, und keines davon tut es; `set_plant_location` verschiebt eine Pflanze, die existiert, eine Beetaufteilung platziert Kulturen, die noch keine Pflanzen sind, und `create_site` legt einen Standort-Stamm an, kein Beet mit einer Fläche
- **MUSS [MUST]** nolte/kamerplanter-goose#74 als den Ort nennen, an dem `bed-layout-plan-apply` geführt wird, und **DARF NICHT [MUST NOT]** ein Rezept mit der Endung `-apply` ausliefern, das nicht schreibt, was seine Beschreibung sagt
- **MUSS [MUST]** das Festhalten einer Beetaufteilung einem eigenen Rezept überlassen, das eine freigegebene Beetaufteilung entgegennimmt, nachdem eine Person sie geprüft hat

## Akzeptanzkriterien

- [ ] Jede Platzierung und jede Folgesaat nennt ihre Regel, ihre Eingaben mit ihren Quellen und Stufen und die fehlenden Daten; eine, die auf einer Eingabe des Aufrufers ruht, sagt das
- [ ] Eine Kapazität ohne Kapazität, Abstand oder Menge des Aufrufers ist `not validated` mit der fehlenden Eingabe, und kein Abstand und keine Dichte stammt aus der Saatdichte des Katalogs oder aus der Erinnerung
- [ ] Eine Kultur steht nur in einem Beet, dessen Fruchtfolgefeld sie zulässt, und eine Kultur außerhalb des Fruchtfolgeplans wird mit diesem Grund aufgeführt
- [ ] Eine Festlegung wird nie verschoben, und eine Festlegung über der Kapazität oder gegen eine Bedingung steht unter `CONFLICTS`
- [ ] Zwei Kulturen, die der Aufrufer mit `avoid` kennzeichnet, teilen sich nie ein Beet in überlappenden Monaten, und ein nicht aufgeführtes Nachbarpaar ist `unknown`, nie unverträglich
- [ ] Der Plan gibt an, dass eine Nachbarschaft eine Eingabe ist und keine Garantie
- [ ] Eine Kultur, die für eine Wachstumsperiode unter zwei Methoden angeboten wird, wird nicht platziert, bis eine Methode gesetzt ist
- [ ] Eine aufeinanderfolgende Folgesaat nennt beide Durchlaufkennungen und die Fenster, auf denen sie ruht; eine gestaffelte Folgesaat gibt es nur mit dem Abstand des Aufrufers
- [ ] Beetmerkmale werden gemeldet und entscheiden über keine Platzierung
- [ ] Jeder nicht platzierte oder nicht nachgefolgte Durchlauf hat einen Grund
- [ ] Die Pläne haben ihre Blöcke in Reihenfolge, und der Anwendungsvertrag gibt an, dass der gemessene Katalog kein Werkzeug hat, das eine Beetaufteilung festhält
- [ ] Zwei Läufe über dieselben Eingabeblöcke ergeben an einer festen Vorlage dieselben Plan-Fakten, und der Plan sagt, was nicht beansprucht wird
- [ ] Die Skills und Rezepte für Beetaufteilung und Folgesaat rufen kein Werkzeug auf, das Zustand ändert
- [ ] Jede Aussage zur Werkzeugoberfläche zitiert eine Spezifikation in diesem Repository; eine nicht erneut gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Zahl an Anforderungspunkten und dieselbe Zahl an Akzeptanz-Checkboxen

## Quelle

- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — die Schreib- und Einrichtungswerkzeuge, `set_plant_location`, das eine vorhandene Pflanze verschiebt, `create_site`, das einen Standort-Stamm anlegt, und `sowing_density_per_m2`, gemessen an `Allium porrum`
- [Der Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md) — `compatible_companions[]` mit `score` und `seed_profile.sowing_density_per_m2` am 2026-08-07 als vorhanden beobachtet, ein fehlender Schlüssel bedeutet nicht befüllt
- [Die Spezifikation zu Standortanalyse und Kulturwahl](../site-analysis-and-crop-selection/de.md) — Licht, Fläche, Volumen und Wasser ohne Quelle und ein nicht aufgeführtes Nachbarpaar als unbekannt, nie unverträglich
- [Die Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) — Belegstufen, die Ausgabe einer Empfehlung und Beete und Gefäße als ohne Quelle
- [Die Spezifikation zur Pflanzplanung](../plant-planning-and-planting-calendar/de.md) — die Durchlaufkennung, die Fenster und die Hinweise zur Folgesaat, die diese Spezifikation liest
- [Die Spezifikation zur Fruchtfolgeplanung](../crop-rotation-planning/de.md) — die Fruchtfolgefelder, die Kulturschlüssel und die Konflikte, die diese Spezifikation liest
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Issue nolte/kamerplanter-goose#46 — die Faktoren der Beetaufteilung und die fünf Kriterien stammen aus seinem Text; nolte/kamerplanter-goose#74 — die blockierte Anwendungshälfte; nolte/kamerplanter-goose#59 und #68 — die Präzedenzfälle für eine blockierte Anwendungshälfte; nolte/kamerplanter-goose#39 — das Audit

## Offene Fragen

- **Was `score` bedeutet.** Die Nachbarliste trägt einen `score`, dessen Wertebereich und Richtung nicht festgehalten sind. Die Beetaufteilung reiht eine höhere numerische Summe zuerst ein, was annimmt, dass ein höherer Wert eine bessere Nachbarschaft ist; die Begründung sagt das. `get_species_info` an zehn oder mehr Gemüsearten, mit dem Wert gegen eine dokumentierte Quelle verglichen, würde es klären.
- **Was `sowing_density_per_m2` zählt.** Es wurde an einer Art beobachtet; ob es Samen oder Pflanzen zählt und ob eine Sorte es trägt, ist nicht festgehalten. Bis dahin ist es nur Kontext.
- **Ob eine laufende Instanz ein Werkzeug hat, das ein Beet, eine Beetaufteilung oder einen Pflanzdurchlauf festhält.** Der gemessene Katalog hat keines, die Server-Spezifikation sagt, jede Werkzeugzahl als Untergrenze zu behandeln, und niemand hat `tools/list` an einer erreichbaren Instanz ausgeführt. Das `-apply`-Rezept wartet darauf, in nolte/kamerplanter-goose#74.
- **Kulturen, die über die Saisongrenze reichen.** Ein Durchlauf, dessen Ernte ins nächste Jahr reicht, hat hier eine unbekannte Belegung, weil ein Lauf eine Saison plant. Eine Beetaufteilung über mehrere Saisons bräuchte die späteren Saisons des Fruchtfolgeplans und liegt außerhalb des Umfangs.
- **Wie Determinismus gemessen wird.** Diese Spezifikation legt die Plan-Fakten fest und verlangt, dass sie über dieselben Eingabeblöcke gleich sind. Geprüft wird das an einer festen, als Text ausgeschriebenen Vorlage, wiederholte Läufe verglichen; das zeigt die Eigenschaft für diese Vorlage und nicht für einen laufenden Garten, und die Zahl der Läufe, die nötig ist, um sie stabil zu nennen, wird hier nicht festgelegt.
- **Wo das Audit, nolte/kamerplanter-goose#39, die Beetaufteilung gegenüber Pflanzung und Fruchtfolge einordnet.** Ob Sammeln, Folgesaat und Beetaufteilung drei Skills bleiben, ist die Entscheidung des Audits.
