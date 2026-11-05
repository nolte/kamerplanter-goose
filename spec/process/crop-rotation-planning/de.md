# Fruchtfolgeplanung

Status: Entwurf
Portfolio-Scope: local

## Kontext

Eine Fruchtfolge hält eine Pflanzenfamilie davon ab, Saison für Saison im selben Beet zu stehen, weil sich bodenbürtige Schädlinge und Krankheiten dieser Familie dort anreichern und die Familie den Boden jedes Mal auf dieselbe Weise beansprucht. Eine Fruchtfolge ist eine Entscheidung über ein Beet über mehrere Saisons: Sie muss wissen, was vorher in jedem Beet stand, zu welcher Familie jede Kultur gehört und wie viele Saisons eine Familie fernbleiben soll. Ein Verfahren, das das aus Allgemeinwissen beantwortet, liefert einen Plan, der sich wie gute Gärtnerei liest und auf nichts ruht, was der Garten ihm gesagt hat: eine erinnerte Familie für eine Art, ein erinnerter Abstand, eine erinnerte Vorgeschichte.

Das Issue, das dies angefordert hat, nolte/kamerplanter-goose#47, ging von einem Kultur- und Familiengraphen im Katalog aus. Die gemessene Oberfläche enthält viel weniger. `get_species_info` trägt `family_key`, `nutrient_demand_level` und `green_manure_suitable`. Kein Werkzeug liest eine Familie, keine Familie trägt einen Namen oder einen Rang, und keine Beziehung zwischen Familien existiert. Die Wertemengen von `nutrient_demand_level` sind über die beiden Beispiele `heavy_feeder` und `medium_feeder` hinaus nicht festgehalten. Die einzige Beziehung zwischen Arten, `compatible_companions[]`, betrifft das Pflanzen nebeneinander, nicht nacheinander. Nichts hält ein Beet, ein Gefäß oder die Vorgeschichte eines Beets fest. Diese Spezifikation nutzt daher die eine Graphkante, die existiert, Art zu `family_key`, und nimmt alles andere vom Aufrufer oder meldet es als unbekannt.

Diese Spezifikation legt zwei Schritte fest. Das Sammeln der Fruchtfolge-Vorgeschichte liest die Familie, die Nährstoffbedarfsklasse und die Gründüngungseignung jeder Kultur sowie die aktuellen und archivierten Pflanzen des Gartens je Standort mit ihren Inspektionen. Das Planen der Fruchtfolge macht aus dieser Vorgeschichte, den Beeten des Aufrufers, der Beetvorgeschichte, dem Abstand und den Bedingungen eine Familiengruppe je Beet und Saison, mit einem Urteil für jede betrachtete Kultur und jedem Konflikt benannt. Beide sind rein lesend. Ein Fruchtfolgeplan ist ein Dokument; ihn festzuhalten ist ein eigener Schritt, und der gemessene Katalog hat kein Werkzeug, das das könnte (Abschnitt G).

Alles zur Werkzeugoberfläche unten ist zitiert aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) und aus dem [Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md), deren Messungen am 2026-08-07 und 2026-08-16 an der Referenzinstanz gemacht wurden. **Nichts davon wurde beim Schreiben dieser Spezifikation erneut gemessen**: Der `kamerplanter`-MCP-Server war in der Sitzung, die sie entworfen hat, nicht erreichbar (`INVALID_CONFIG`). Werkzeug- und Feldnamen sind aus jenen Spezifikationen übernommen; ob sie noch existieren und was eine Antwort darüber hinaus trägt, bleibt unbelegt, bis ein `tools/list` und ein lesender Aufruf an einer erreichbaren Instanz es sagen.

Grenzen: Die [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) besitzen das Gewicht einer Aussage, die Form einer Empfehlung und den Gartenkontext; diese Spezifikation wendet sie an und wiederholt sie nicht. Die [Spezifikation zur Pflanzplanung](../plant-planning-and-planting-calendar/de.md) besitzt die Pflanzdurchläufe, und ihre Durchläufe bleiben `rotation: unknown`, weil einem Durchlauf kein Beet zugeordnet wird und ein Fruchtfolgeurteil nur je Beet existiert. Beetaufteilung, Fläche, Abstände, Platzierung von Nachbarn und Folgesaaten sind die [Spezifikation zu Beetaufteilung und Folgesaatplanung](../bed-layout-and-succession-planning/de.md) (nolte/kamerplanter-goose#46), die die Ausgabe dieser Spezifikation liest. Die `-apply`-Hälfte von nolte/kamerplanter-goose#47 wird in nolte/kamerplanter-goose#68 geführt. Das Audit, das entscheidet, welches Artefakt was besitzt, ist nolte/kamerplanter-goose#39, und nichts hier greift ihm vor. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt die Rezeptmechanik, und [die Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md) besitzt Transport, Authentifizierung und Mandantenfähigkeit.

Leser: Autoren von Garten-Skills und -Rezepten in diesem Repository, der Autor der Beetaufteilung, der den Fruchtfolgeplan verbraucht, und alle, die eine Fruchtfolge prüfen, bevor sie danach handeln.

## Ziele

- Jedes Urteil nennt die Regel, die es ergeben hat, die Felder, aus denen es stammt, deren Quelle und die Belegstufe, auf der es ruht
- Eine Familie, eine Bedarfsklasse, ein Abstand oder eine Beetvorgeschichte ohne Quelle wird als unbekannt mit der fehlenden Eingabe gemeldet, nie aus der Erinnerung ergänzt
- Ein Konflikt wird nie verborgen: Eine Regel, die der Plan bricht, auch eine, die die eigene Festlegung des Aufrufers bricht, wird mit den Belegen beider Seiten aufgeführt
- Der Plan ist eine Funktion seiner Eingabeblöcke, sodass zwei Läufe über dieselben Blöcke dieselben Plan-Fakten ergeben
- Rein lesendes Planen und Festhalten sind getrennt, und ein Plan kann geprüft werden, bevor etwas festgehalten wird
- Die Beetaufteilung kann den Plan lesen, ohne etwas neu abzuleiten

## Nicht-Ziele

- Eine Fruchtfolge festhalten, einem Beet eine künftige Kultur zuordnen oder einen Pflanzdurchlauf anlegen. Der gemessene Katalog hat dafür kein Werkzeug (Abschnitt G)
- Beetaufteilung, Fläche und Kapazität, Abstände, Platzierung von Nachbarn und Folgesaaten — [Beetaufteilung und Folgesaatplanung](../bed-layout-and-succession-planning/de.md)
- Pflanztermine: Das ist der [Pflanzkalender](../plant-planning-and-planting-calendar/de.md)
- Kulturen wählen: Das ist die [Kulturwahl](../site-analysis-and-crop-selection/de.md)
- Eine Familie, ein Fruchtfolgeabstand, eine Bedarfsreihenfolge oder eine Bodenwirkung aus Allgemeinwissen. Ein Wert stammt aus einem festgehaltenen Feld oder vom Aufrufer, oder er ist unbekannt
- Eine Familie während eines Laufs recherchieren. Die Drei-Quellen-Regel des [Prozesses zur Artdaten-Prüfung](../species-baseline-verification/de.md) läuft außerhalb eines Rezepts, und Garten-Rezepte rufen keine URL ab

## Anforderungen

### A. Eingaben

| Eingabe | Quelle | Nicht belegt |
|---------|--------|--------------|
| Kandidatenkulturen | Der Aufrufer: Einträge `species_key` oder `species_key:cultivar_key`, durch Kommas getrennt | — |
| Geplante Saisons | Der Aufrufer: aufeinanderfolgende Jahre, durch Kommas getrennt | — |
| Beete | Der Aufrufer: Einträge `name` oder `name:area_or_volume`, durch Kommas getrennt | Keine Quelle im gemessenen Katalog |
| Beetvorgeschichte | Der Aufrufer: Einträge `bed:season:species_key[:cultivar_key]` oder `bed:season:none`, durch Kommas getrennt; und der Katalog, Abschnitt C | Ob ein Katalogstandort ein Beet ist |
| Fruchtfolgeabstand | Nur der Aufrufer: `rotation_years`, eine ganze Zahl | Keine Quelle; keine Zahl ist eingebaut |
| Bedarfsreihenfolge | Nur der Aufrufer: `demand_sequence`, Werte durch Kommas getrennt | Die Wertemenge von `nutrient_demand_level` |
| Bedingungen | Nur der Aufrufer: Einträge durch Semikolons getrennt, `pin=bed:season:species_key[:cultivar_key]`, `exclude=bed:species_key[:cultivar_key]` oder freier Text | — |
| Die Pflanzdurchläufe des Gartens | `list_planting_runs` | Ihre Form und ihre Parameter |

- **MUSS [MUST]** jede Liste an ihrem Trennzeichen und jeden Eintrag an seinen Doppelpunkten trennen und **DARF NICHT [MUST NOT]** den zusammengesetzten Text als Namen weitergeben; ein Beetname ist der Text vor dem ersten Doppelpunkt eines `beds`-Eintrags
- **MUSS [MUST]** eine doppelt genannte Saison einmal zählen und einmal im Kopf melden, **MUSS [MUST]** anhalten und das Problem benennen, wenn die übrigen Saisons keine aufeinanderfolgenden ganzen Jahre sind, und **DARF NICHT [MUST NOT]** eine Lücke füllen
- **MUSS [MUST]** Beete, Beetvorgeschichte, Abstand, Bedarfsreihenfolge und Bedingungen als Quelle `caller` kennzeichnen und **MUSS [MUST]** jede als nicht geliefert melden, wenn der Aufrufer sie leer ließ
- **MUSS [MUST]** als Beete des Plans die Vereinigung der `beds`-Einträge, der in der Beetvorgeschichte genannten Beete und der in einer Festlegung genannten Beete behandeln und **MUSS [MUST]** melden, dass nichts zu platzieren ist, wenn diese Vereinigung leer ist
- **MUSS [MUST]** jeden Eintrag, der sich nicht zerlegen lässt, und jede Bedingung in freiem Text wörtlich als `not evaluated` aufführen und **DARF NICHT [MUST NOT]** freien Text als Regel auslegen
- **SOLLTE [SHOULD]** die Pflanzdurchläufe des Gartens nur als Kontext aufführen, da ihre Form nicht festgehalten ist, und **DARF NICHT [MUST NOT]** ein unvollständiges oder gescheitertes Lesen als Beweis behandeln, dass es keine gibt

### B. Familie, Bedarfsklasse und Gründüngung

| Feld | Werkzeug | Stufe | Nicht belegt |
|------|----------|-------|--------------|
| `family_key` | `get_species_info` | 4 | Ob jede Art es trägt; kein Werkzeug zum Lesen einer Familie, kein Name und kein Rang existiert |
| `nutrient_demand_level` | `get_species_info`, `get_cultivar` | 4 | Seine Wertemenge: Nur `heavy_feeder` und `medium_feeder` sind festgehalten |
| `green_manure_suitable` | `get_species_info`, `get_cultivar` | 4 | Welche Arten es tragen |

- **MUSS [MUST]** `get_species_info` einmal je verschiedener Art unter den Kandidaten, den Festlegungen, der Beetvorgeschichte und den Pflanzen an zugeordneten Standorten lesen und **MUSS [MUST]** `get_cultivar` nur für eine Sorte lesen, die ein Eintrag oder eine zugeordnete Katalogpflanze nennt
- **MUSS [MUST]** den Wert der Sorte verwenden, wenn die Sorte das Feld trägt, sonst den Wert der Art, und **MUSS [MUST]** je Feld festhalten, welcher von beiden es war
- **MUSS [MUST]** ein fehlendes Feld als fehlend melden, also als für diese Art nicht befüllt, und **DARF NICHT [MUST NOT]** ein fehlendes `family_key` als „gehört zu keiner Familie“ lesen
- **DARF NICHT [MUST NOT]** eine Familie aus der Erinnerung, aus einem wissenschaftlichen Namen oder aus einer Gattung nehmen und **DARF NICHT [MUST NOT]** sie während eines Laufs recherchieren; eine Kultur ohne festgehaltenes `family_key` hat die Familie `unknown`
- **DARF NICHT [MUST NOT]** `compatible_companions[]` als Fruchtfolgebeziehung lesen
- **MUSS [MUST]** `nutrient_demand_level` als Text, wie festgehalten, mit der Bedarfsreihenfolge vergleichen und **DARF NICHT [MUST NOT]** eine Konvention aus Stark-, Mittel-, Schwachzehrer und Gründüngung einbauen
- **MUSS [MUST]** `green_manure_suitable: true` nur dazu verwenden, dass eine Kultur zum Wert `green_manure` in der Bedarfsreihenfolge des Aufrufers passt, und **MUSS [MUST]** jede andere Bodenwirkung, darunter die Stickstoffbindung und das Fortbestehen bodenbürtiger Krankheiten, als `not modeled` melden

### C. Beetvorgeschichte

| Quelle | Was sie liefert | Nicht belegt |
|--------|-----------------|--------------|
| `bed_history` des Aufrufers | Beet, Saison, Kultur oder `none` | — |
| `list_plants` mit `include_archived: true` | Je Pflanze: `species_key`, `location_key`, `planted_on`, aktuelle und archivierte Pflanzen | Ob eine archivierte Pflanze `location_key` und `planted_on` behält, welches Feld sie als archiviert kennzeichnet und ob ein Enddatum existiert |
| `get_plant_inspections` | Die IPM-Historie einer Pflanze | Die Felder über Befallsstärke, Symptome und strukturierte Befunde hinaus |

- **MUSS [MUST]** die Beetvorgeschichte des Aufrufers als primäre Quelle nehmen und **MUSS [MUST]** eine Katalogpflanze nur dann einem Beet zuordnen, wenn ihr `location_key` genau dem Beetnamen entspricht; jeder andere Standort wird als `unmapped location history` aufgeführt, nur als Kontext
- **MUSS [MUST]** `list_plants` mit `include_archived: true` lesen, seitenweise und begrenzt, wie der Skill `garden-context` es seitenweise liest und begrenzt, und **MUSS [MUST]** ein unvollständiges oder gescheitertes Lesen als solches melden und **DARF NICHT [MUST NOT]** es als „keine Vorgeschichte“ behandeln
- **MUSS [MUST]** das Jahr von `planted_on` als Saison einer Katalogpflanze nehmen und **MUSS [MUST]** eine Pflanze ohne `planted_on` als Vorgeschichte mit der Saison `unknown` melden
- **MUSS [MUST]** die Vorgeschichte eines Beets ab der Saison seines frühesten Eintrags mit bekannter Saison als belegt zählen, eines Eintrags des Aufrufers (`none` eingeschlossen) oder einer zugeordneten Pflanze aus einem vollständigen Lesen des Katalogs, und sie ab dieser Saison als vollständig nehmen, eine Saison, die sie nicht nennt, trägt also keine Kultur; jede Saison davor und jede Saison eines Beets ohne einen solchen Eintrag **MUSS [MUST]** `unknown` sein, nie leer, ein einzelnes `bed:2026:none` belegt also 2026 und danach und nichts davor; der Plan **MUSS [MUST]** sagen, dass das eine Annahme ist und worauf sie ruht
- **MUSS [MUST]** einen Eintrag der Vorgeschichte in einer geplanten Saison so behandeln, dass er dieses Beet in dieser Saison belegt, und **MUSS [MUST]** ihn für die späteren Saisons als Vorgeschichte zählen
- **MUSS [MUST]** `get_plant_inspections` nur für Pflanzen an einem Standort lesen, der einem Beet zugeordnet ist, **MUSS [MUST]** eine festgehaltene Inspektion als `caution` für dieses Beet auf Stufe 3 mit der fehlenden Eingabe `host range: not recorded` melden und **MUSS [MUST]** ein gescheitertes oder unvollständiges Lesen der Inspektionen als fehlende Daten behandeln, die das `clear` des Beets zu `unknown` machen; weder `get_pest` noch `get_disease` hält einen Wirtskreis fest, daher **DARF NICHT [MUST NOT]** ein Befall zu einem Konflikt werden
- **DARF NICHT [MUST NOT]** die Beurteilung des Schädlingsdrucks einer lebenden Pflanze für eine künftige Kultur wiederverwenden

### D. Regeln und Urteile

Jede Kultur, die für ein Beet und eine Saison betrachtet wird, erhält genau ein Urteil, das erste, das in dieser Reihenfolge zutrifft:

| Regel | Urteil | Wann |
|-------|--------|------|
| 1 | `unknown` (Familie) | Die Familie der Kultur ist `unknown` |
| 2 | `conflict` | Mit `rotation_years` N: Eine Kultur derselben Familie steht im selben Beet in einer Saison 1 bis N−1 Saisons früher |
| 3 | `repeat — interval unknown` | Ohne `rotation_years`: Eine Kultur derselben Familie steht im selben Beet in irgendeiner früheren Saison |
| 4 | `unknown` (Vorgeschichte) | Eine Kultur unbekannter Familie steht im Vergleichsfenster, oder das Beet hat einen Eintrag der Vorgeschichte mit der Saison `unknown` |
| 5 | `unknown` (Abdeckung) | Das Fenster enthält eine Saison, die für das Beet `unknown` ist (Abschnitt C); ohne Abstand hat das Fenster keinen Anfang, daher trifft das immer zu |
| 6 | `unknown` (Inspektionen) | Ein Lesen der Inspektionen für eine Pflanze am Beet ist gescheitert oder unvollständig |
| 7 | `caution` | Nichts davon, und das Beet hat eine festgehaltene Inspektion |
| 8 | `clear` | Nichts davon |

Das Vergleichsfenster sind die Saisons 1 bis N−1 Saisons früher mit einem Abstand und jede frühere Saison ohne einen. Es enthält die Beetvorgeschichte und die eigenen Platzierungen des Plans in früheren geplanten Saisons.

Worauf ein Urteil ruht und welche Stufe jedes Element trägt: das `family_key` der Kultur und das `family_key` eines Eintrags, Stufe 4; ein Eintrag der Vorgeschichte des Aufrufers, N und eine festgelegte Platzierung, `caller`; eine zugeordnete Katalogpflanze, Stufe 5; eine Platzierung, die der Plan gewählt hat, die Stufe des `family_key`, nach dem sie gewählt wurde; eine Inspektion, Stufe 3. N ist, wenn geliefert, ein Element jedes Urteils, weil es das Fenster festlegt.

| Regel | Elemente |
|-------|----------|
| 1 | das Lesen von `get_species_info`, dem `family_key` fehlt; N, wenn geliefert |
| 2 | das `family_key` der Kultur; der passende Eintrag; N |
| 3 | das `family_key` der Kultur; der passende Eintrag |
| 4, 5, 6 | das `family_key` der Kultur; jeder Eintrag im Fenster, einschließlich des Eintrags mit unbekannter Familie oder Saison; N, wenn geliefert |
| 7 | das `family_key` der Kultur; jeder Eintrag im Fenster; der Eintrag, der die Vorgeschichte des Beets belegt; N; die Inspektion |
| 8 | das `family_key` der Kultur; jeder Eintrag im Fenster; der Eintrag, der die Vorgeschichte des Beets belegt, wenn das Fenster vor die erste geplante Saison reicht; N |

Die Stufe eines Urteils ist `caller`, wenn eines seiner Elemente `caller` ist, und sonst die schwächste Stufe unter ihnen, die höchste Zahl.

- **MUSS [MUST]** jedem Urteil seine Regel, die Felder beider Seiten mit ihren Quellen und Stufen und die fehlenden Daten gemäß den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) mitgeben; ein Urteil, das auf einem vom Aufrufer gelieferten Fakt ruht, **MUSS [MUST]** das sagen
- **MUSS [MUST]** N als den kleinsten Abstand in Saisons lesen, in dem eine Familie wieder in einem Beet stehen darf, und **DARF NICHT [MUST NOT]** einen Wert ergänzen, wenn der Aufrufer keinen angab
- **DARF NICHT [MUST NOT]** für eine Wiederholung derselben Familie `conflict` oder `clear` melden, wenn kein Abstand geliefert wurde
- **DARF NICHT [MUST NOT]** `clear` für eine Kultur unbekannter Familie oder für ein Fenster melden, das die Vorgeschichte nicht abdeckt
- **MUSS [MUST]** die Bedarfsreihenfolge als Präferenz behandeln, `met`, `unmet`, `unknown` oder `not evaluated`, beurteilt gegen die Bedarfsklasse der Kultur im selben Beet eine Saison früher, und **DARF NICHT [MUST NOT]** sie einen Konflikt ergeben lassen
- **MUSS [MUST]** eine Festlegung einhalten, indem ihre Kultur platziert wird, und **MUSS [MUST]** eine Festlegung, die eine Regel bricht, auf ein Beet fällt, das in der betreffenden Saison belegt ist, oder einem Ausschluss oder einer anderen Festlegung widerspricht, als Konflikt melden und **DARF NICHT [MUST NOT]** sie verschieben
- **MUSS [MUST]** einen Ausschluss einhalten, indem diese Kultur für dieses Beet in keiner Saison betrachtet wird

### E. Der Plan und seine Verbraucher

Der Planer entscheidet die Saisons der Reihe nach, jede vollständig vor der nächsten, sodass jedes Urteil einer Saison berechnet wird, nachdem alle früheren Saisons entschieden sind. Innerhalb einer Saison platziert er zuerst die Festlegungen dieser Saison, jede mit ihrem an der eigenen Stelle berechneten Urteil, und geht dann die übrigen Beete nach ihrem Namen als Text durch. Für jedes davon betrachtet er jede Familiengruppe, die Kandidatenkulturen mit gemeinsamem `family_key`, wobei jede Kultur unbekannter Familie eine eigene Gruppe ist, lässt die Kulturen weg, die von diesem Beet ausgeschlossen sind, und überspringt eine Gruppe, die die Ausschlüsse leer lassen.

- **MUSS [MUST]** je Beet und Saison höchstens eine Familiengruppe wählen, deren Urteil `clear`, `caution` oder `unknown` ist, und **MUSS [MUST]** Beet und Saison als `open` melden, mit jeder Gruppe und ihrem Urteil, wenn keine in Frage kommt
- **MUSS [MUST]** die in Frage kommenden Gruppen nach Urteil ordnen (`clear`, dann `caution`, dann `unknown`), dann danach, wie viele Beete die Gruppe in dieser Saison schon tragen (weniger zuerst), dann nach Bedarfspräferenz (`met`, dann `unknown` oder `not evaluated`, dann `unmet`), dann bekannte Familien vor unbekannten, dann nach dem Gruppenschlüssel als Text
- **DARF NICHT [MUST NOT]** Durchläufe, Flächen oder Abstände platzieren; eine Platzierung nennt eine Familiengruppe und ihre Kulturen, und die Beetaufteilung platziert sie
- **MUSS [MUST]** jeder Platzierung eine Begründung mitgeben, die die Werte der Rangfolge angibt und jede nicht gewählte Gruppe mit ihrem Urteil nennt
- **MUSS [MUST]** jede Kandidatenkultur, die nie platziert wurde, unter `NOT PLACED` aufführen, mit dem Grund je Beet und Saison: ihrem Urteil, `excluded`, `occupied`, `pinned slot`, wenn eine Festlegung einer anderen Kultur die Stelle hält, oder der Gruppe, die sie überholt hat
- **MUSS [MUST]** jede Kultur als `species_key/cultivar_key` schlüsseln, mit `none` für keine Sorte, was das Präfix einer Durchlaufkennung der [Pflanzplanung](../plant-planning-and-planting-calendar/de.md) ist, sodass ein Plan und ein Pflanzplan darüber zusammengeführt werden

Das Plandokument hat sechs Blöcke, in dieser Reihenfolge und unter diesen Namen: `ROTATION HEADER` (der Garten, vorgegeben oder ermittelt, die Eingaben, der Abstand und die Bedarfsreihenfolge oder `not supplied`, die nicht ausgewerteten Einträge), `BED HISTORY`, `ROTATION PLAN`, `CONFLICTS` (jede platzierte Kultur, die eine Regel bricht, und jeder Widerspruch, den eine Festlegung verursacht; da die Auswahl nie ein `conflict` oder ein `repeat — interval unknown` platziert, erzeugt nur eine Festlegung einen Eintrag, und eine Kultur, die für ein Beet in einer Saison betrachtet und dort nicht platziert wurde, behält ihr Urteil bei diesem Beet und unter `NOT PLACED`), `NOT PLACED` und `APPLY CONTRACT`. Die Stufe jedes Urteils folgt Abschnitt D.

| Verbraucher | Liest |
|-------------|-------|
| [Beetaufteilung und Folgesaaten](../bed-layout-and-succession-planning/de.md) (nolte/kamerplanter-goose#46) | je Beet und Saison: das Beet, die Saison, die gewählte Familiengruppe oder `open` oder `occupied`, die Kulturen als `species_key/cultivar_key` mit ihren Urteilen, die Konflikte |
| Eine Person, die einen Plan der [Pflanzplanung](../plant-planning-and-planting-calendar/de.md) prüft | je Kultur: die Beete und Saisons, in denen sie platziert ist, über das Präfix `species_key/cultivar_key` mit den Pflanzdurchläufen zusammengeführt |

- **MUSS [MUST]** die sechs Blöcke in dieser Reihenfolge mit diesen Namen zurückgeben und **DARF NICHT [MUST NOT]** ein Feld zurückgeben, das nicht gelesen wurde, sondern ein ungelesenes Feld mit seinem Grund als fehlend auflisten

### F. Determinismus

- **MUSS [MUST]** den Plan zu einer Funktion der gelieferten Eingabeblöcke und der Regeln machen, sodass zwei Läufe über dieselben Blöcke dieselben Plan-Fakten ergeben: die Platzierungen, die Urteile, die Konflikte, die Gründe für „nicht platziert“ und die Belegstufen
- **DARF NICHT [MUST NOT]** die Reihenfolge der Eingabe oder das aktuelle Datum über einen Plan-Fakt entscheiden lassen; Abrufzeitpunkte werden neben den Fakten berichtet und nicht verglichen
- **MUSS [MUST]** angeben, dass bytegleicher Text außerhalb der Plan-Fakten nicht beansprucht wird und dass die Eigenschaft an einer festen Vorlage aus Eingabeblöcken geprüft wird und nicht an einem laufenden Garten

### G. Trennung und Anwendungsvertrag

- **MUSS [MUST]** die Fruchtfolgeplanung rein lesend halten: Die Planungs-Skills und -Rezepte rufen kein Werkzeug auf, das Zustand ändert
- **MUSS [MUST]** in jeden Plan einen Block `APPLY CONTRACT` aufnehmen, der je Platzierung angibt, was ein späteres `-apply`-Rezept festhalten müsste (das Beet, die Saison, die Familiengruppe und ihre Kulturen), und **MUSS [MUST]** angeben, dass der gemessene Katalog kein Werkzeug hat, das eine Beetzuordnung, eine Fruchtfolge, einen Pflanzdurchlauf oder einen Plan festhält: Die Schreibwerkzeuge, die er verzeichnet, sind `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` und `create_inspection`, dazu das Einrichtungswerkzeug `create_site`, und keines davon tut es; `set_plant_location` verschiebt eine Pflanze, die existiert, und eine Fruchtfolge plant Kulturen, die noch keine Pflanzen sind
- **MUSS [MUST]** nolte/kamerplanter-goose#68 als den Ort nennen, an dem das `-apply`-Rezept geführt wird, und **DARF NICHT [MUST NOT]** ein Rezept mit der Endung `-apply` ausliefern, das nicht schreibt, was seine Beschreibung sagt
- **MUSS [MUST]** das Festhalten eines Plans einem eigenen Rezept überlassen, das einen freigegebenen Plan entgegennimmt, nachdem eine Person ihn geprüft hat

## Akzeptanzkriterien

- [ ] Jedes Urteil nennt seine Regel, seine Felder mit ihren Quellen und Stufen und die fehlenden Daten; ein Urteil, das auf einem Fakt des Aufrufers ruht, sagt das
- [ ] Eine Kultur ohne festgehaltenes `family_key` ist überall `unknown`, und keine Familie stammt aus Erinnerung oder Recherche
- [ ] Ohne `rotation_years` ist eine Wiederholung derselben Familie `repeat — interval unknown`, nie `conflict` und nie `clear`
- [ ] Ein Beet, dessen Vorgeschichte nicht belegt ist, ergibt `unknown`, wo das Vergleichsfenster vor den Plan reicht, nie `clear`
- [ ] Eine Katalogpflanze wird einem Beet nur bei genauer Gleichheit von `location_key` zugeordnet, und ein unvollständiges oder gescheitertes Lesen der Vorgeschichte wird gemeldet, nicht als keine Vorgeschichte gelesen
- [ ] Eine festgehaltene Inspektion ergibt `caution`, nie `conflict`
- [ ] Die Bedarfsreihenfolge ist eine Präferenz und ergibt nie einen Konflikt; keine Bedarfskonvention ist eingebaut
- [ ] Eine Festlegung wird immer platziert, und eine Festlegung, die eine Regel bricht, steht unter `CONFLICTS`
- [ ] Jede Platzierung hat eine Begründung, die die nicht gewählten Gruppen nennt, und jede nie platzierte Kultur wird mit ihren Gründen aufgeführt
- [ ] Jede Kultur ist als `species_key/cultivar_key` geschlüsselt
- [ ] Der Plan hat die sechs Blöcke in Reihenfolge, und der Anwendungsvertrag gibt an, dass der gemessene Katalog kein Werkzeug hat, das eine Fruchtfolge festhält
- [ ] Zwei Läufe über dieselben Eingabeblöcke ergeben an einer festen Vorlage dieselben Plan-Fakten, und der Plan sagt, was nicht beansprucht wird
- [ ] Die Fruchtfolge-Skills und -Rezepte rufen kein Werkzeug auf, das Zustand ändert
- [ ] Jede Aussage zur Werkzeugoberfläche zitiert eine Spezifikation in diesem Repository; eine nicht erneut gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Zahl an Anforderungspunkten und dieselbe Zahl an Akzeptanz-Checkboxen

## Quelle

- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Werkzeugkatalog ohne Werkzeug zum Lesen einer Familie, `get_plant_inspections` leer gemessen an einer nie inspizierten Pflanze, `get_pest` ohne Felder zum Wirtskreis gemessen, die Schreib- und Einrichtungswerkzeuge und die Mandantenfähigkeit
- [Der Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md) — `family_key`, `nutrient_demand_level`, `green_manure_suitable` und `compatible_companions[]` am 2026-08-07 an zwei Arten als vorhanden beobachtet, ein fehlender Schlüssel bedeutet nicht befüllt, und die Drei-Quellen-Regel
- [Der Prozess zur Erkennung von Nährstoff-Ungleichgewichten](../nutrient-imbalance-detection/de.md) — `heavy_feeder` und `medium_feeder` als die festgehaltenen Beispiele für `nutrient_demand_level`
- [Die Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) — Belegstufen, die Ausgabe einer Empfehlung und der Gartenkontext mit Beeten und Gefäßen als ohne Quelle
- [Die Spezifikation zur Pflanzplanung](../plant-planning-and-planting-calendar/de.md) — die Durchlaufkennung, über deren Präfix dieser Plan zusammengeführt wird, und der Hinweis zur Fruchtfolge, den sie unbekannt lässt
- `recipes/plant-master-data-check.yaml` — `list_plants` gemessen mit `matched: 9` gegenüber `total_in_tenant: 11`, der einzige Beleg dafür, dass archivierte Pflanzen existieren
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Issue nolte/kamerplanter-goose#47 — die Fruchtfolgefaktoren und die fünf Kriterien stammen aus seinem Text; nolte/kamerplanter-goose#68 — die blockierte Anwendungshälfte; nolte/kamerplanter-goose#46, #59 und #39 — der Verbraucher, der Präzedenzfall für eine blockierte Anwendungshälfte und das Audit

## Offene Fragen

- **Ob jede Art `family_key` trägt, und die Wertemenge von `nutrient_demand_level`.** Beide wurden an zwei Arten beobachtet, und welche der beiden welches Feld trug, ist nicht festgehalten. Ein Plan voller `unknown` ist das ehrliche Ergebnis, bis `get_species_info` an zehn oder mehr Gemüsearten etwas anderes sagt.
- **Was eine archivierte Pflanze trägt.** Ob `list_plants` mit `include_archived: true` `location_key` und `planted_on` behält und ob ein Enddatum existiert. Bis das gemessen ist, ist die Vorgeschichte des Aufrufers primär.
- **Kulturen, die länger als eine Saison stehen.** Die Katalogsaison ist das Jahr von `planted_on`, daher zählt eine mehrjährige Kultur oder eine, die zwei Jahre überspannt, nur in ihrem Pflanzjahr. Kein Feld `cycle_type` existiert, um das zu korrigieren.
- **Eingebaute Abstände je Familie.** Keine sind eingebaut. Recherchierte Abstände bräuchten je drei unabhängige Quellen, beim Verfassen und nicht in einem Lauf, und wären eine Änderung dieser Spezifikation.
- **Die Form von `list_planting_runs`.** Pflanzdurchläufe bleiben Kontext, bis ihre Form festgehalten ist.
- **Ob eine laufende Instanz ein Werkzeug hat, das eine Fruchtfolge oder eine Beetzuordnung festhält.** Der gemessene Katalog hat keines, die Server-Spezifikation sagt, jede Werkzeugzahl als Untergrenze zu behandeln, und niemand hat `tools/list` an einer erreichbaren Instanz ausgeführt. Das `-apply`-Rezept wartet darauf, geführt als nolte/kamerplanter-goose#68.
- **Wie Determinismus gemessen wird.** Diese Spezifikation legt die Plan-Fakten fest und verlangt, dass sie über dieselben Eingabeblöcke gleich sind. Geprüft wird das an einer festen, als Text ausgeschriebenen Vorlage, wiederholte Läufe verglichen; das zeigt die Eigenschaft für diese Vorlage und nicht für einen laufenden Garten, und die Zahl der Läufe, die nötig ist, um sie stabil zu nennen, wird hier nicht festgelegt.
- **Wo das Audit, nolte/kamerplanter-goose#39, die Fruchtfolge gegenüber Pflanzplanung und Beetaufteilung einordnet.** Ob Sammeln und Planen zwei Skills bleiben, entscheidet das Audit.
