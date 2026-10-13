# Standortanalyse und Kulturwahl

Status: Entwurf
Portfolio-Scope: local

## Kontext

Die Wahl dessen, was angebaut wird, steht vor jeder Pflegefrage, die dieses Repository beantwortet, und sie ist die Wahl, die am ehesten aus einem plausibel klingenden Standardwert getroffen wird. Eine Kultur ist für einen Standort nur anhand von Fakten über den Standort „geeignet“, und die meisten Fakten, nach denen man zuerst greift — wie viel Licht das Beet bekommt, wie viel Platz da ist, ob Wasser bereitsteht —, hält der Kamerplanter-Katalog nicht. Ein Verfahren, das sie aus Allgemeinwissen füllt, liefert eine selbstsichere Kandidatenliste, die auf nichts ruht, was der Garten ihm gesagt hat.

Diese Spezifikation legt zwei Schritte fest. Die Standortanalyse macht aus dem, was über einen Standort bekannt ist, ein Profil, das Parameter für Parameter sagt, was bekannt ist, was unbekannt ist und woher jeder Wert stammt. Die Kulturwahl beurteilt Kandidaten aus Arten und Sorten gegen dieses Profil und gegen die Ziele der Anbauenden und liefert je Kandidat ein Urteil mit Gründen und den verfehlten Bedingungen. Beide führen Unbekanntes als unbekannt. Ein Parameter, den niemand geliefert hat, gilt nie als erfüllt und nie als verfehlt: Er lässt die Bedingung, die er speist, unentschieden.

Alles zur Werkzeugoberfläche unten ist zitiert aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) und aus dem [Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md), deren Messungen am 2026-08-07 an der Referenzinstanz gemacht wurden. **Nichts davon wurde beim Schreiben dieser Spezifikation erneut gemessen**: Der `kamerplanter`-MCP-Server war in der Sitzung, die sie entworfen hat, nicht erreichbar (`INVALID_CONFIG`). Werkzeug- und Feldnamen sind aus jenen Spezifikationen übernommen; ob sie noch existieren und was eine Antwort darüber hinaus trägt, bleibt unbelegt, bis ein `tools/list` und ein lesender Aufruf an einer erreichbaren Instanz es sagen.

Grenzen: Die [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) besitzen, wie Belege geordnet werden, welche Regeln eine Empfehlung nicht brechen darf und was sie offenlegen muss; diese Spezifikation wendet sie an und wiederholt sie nicht. Der Gartenkontext derselben Spezifikation besitzt die Feldnamen für das, was ein Garten enthält, und `plant-context-collect` besitzt den Kontext einer Pflanze. Die Fruchtfolgeplanung ist eine eigene Arbeit und wird als nolte/kamerplanter-goose#47 geführt, und der Pflanzplan, der das Ergebnis dieser Spezifikation verbraucht, als nolte/kamerplanter-goose#42; beide werden hier nicht festgelegt. Das Audit, das entscheidet, welches Artefakt was besitzt, wird als nolte/kamerplanter-goose#39 geführt, und nichts hier greift ihm vor. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt die Rezeptmechanik, und [die Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md) besitzt Transport, Authentifizierung und Mandantenfähigkeit.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Autorin des Pflanzplans, der die Kandidatenliste verbraucht, und alle, die eine Kulturempfehlung prüfen, bevor sie danach handeln.

## Ziele

- Ein Standortprofil nennt für jeden Parameter, ob er bekannt oder unbekannt ist, seinen Wert und seine Quelle
- Ein unbekannter Parameter bleibt unbekannt: Er gilt nie als erfüllt und nie als verfehlt
- Jeder Kandidat trägt ein Urteil, die Gründe dafür und die verfehlten harten Bedingungen, jeweils mit Quelle und Belegstufe
- Harte Bedingungen und Präferenzen werden getrennt gehalten, sodass eine Präferenz nie eine Kultur ausschließen und eine verfehlte harte Bedingung nie verrechnet werden kann
- Sortendaten werden verwendet, wenn sie vorliegen, sonst Artdaten, und der Datensatz sagt, welche
- Das Ergebnis kann vom Pflanzplan verbraucht werden, ohne dass etwas neu abgeleitet wird

## Nicht-Ziele

- Planen, wann und wo gepflanzt wird, Beetaufteilung, Folgesaaten oder Fruchtfolge — nolte/kamerplanter-goose#42 und #47
- Gesundheit, Ernährung oder Schädlinge einer einzelnen Pflanze beurteilen — das tun die Prozesse, denen sie gehören
- Einen Datensatz schreiben, einen Standort anlegen oder einen Plan zuweisen
- Standortfakten liefern, die der Katalog nicht enthält. Wo es keine Quelle gibt, liefert der Aufrufer den Wert, oder er bleibt unbekannt
- Licht, Fläche oder Wasser aus dem Namen oder Typ eines Standorts ableiten
- Das Urteil der Anbauenden über ihren eigenen Standort ersetzen

## Anforderungen

### A. Das Standortprofil

Das Profil hat sieben Parameter. Jeder wird als `known` oder `unknown` gemeldet; ein `known`-Parameter trägt seinen Wert, seine Quelle (ein Werkzeug oder `caller`), seinen Abrufzeitpunkt und seine Belegstufe gemäß den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md).

| Parameter | Quelle im gemessenen Katalog | Nicht belegt |
|-----------|------------------------------|--------------|
| Licht und Exposition | **Keine Quelle gemessen.** Eine Suche in der Server-Spezifikation nach Licht, Sonne, Schatten und Exposition findet kein Feld | Alles; der Aufrufer kann es liefern |
| Verfügbare Fläche und Gefäßvolumen | **Keine Quelle gemessen.** Kein Flächen- oder Volumenfeld ist genannt | Alles; der Aufrufer kann es liefern |
| Boden und Substrat | `list_substrates`, mit `ph_base`, `ec_base_ms`, `buffer_capacity` und `cec_meq_per_100g` gemäß dem [Nährstoffprozess](../nutrient-imbalance-detection/de.md); der `substrate_key` einer Pflanze aus `list_plants` | Welches Substrat ein Beet oder Gefäß enthält: Nur eine Pflanze trägt den Schlüssel |
| Klima und lokale Saison | `get_sowing_calendar` mit einer `query` lieferte Frostdaten, gemäß dem [Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md); `list_hardiness_zones` listet Zonen | In welcher Zone der Garten liegt: Kein Feld sagt es. Die darüber hinausgehenden Antwortfelder beider Werkzeuge sind nicht festgehalten |
| Wasserverfügbarkeit | **Keine Quelle gemessen.** Kein Bewässerungs- oder Wasserfeld ist genannt | Alles; der Aufrufer kann es liefern |
| Umweltbedingte Einschränkungen | **Keine Quelle gemessen** als Feld; vom Aufrufer als Freitext geliefert | Alles |
| Vorhandene Beobachtungen und Messungen | Die Felder des Gartenkontexts für aktuelle Messungen und historische Beobachtungen, je Pflanze gesammelt | Nicht auf Gartenebene gesammelt |

- **MUSS [MUST]** in jedem Profil alle sieben Parameter in dieser Reihenfolge als `known` oder `unknown` melden und **DARF NICHT [MUST NOT]** einen unbekannten Parameter weglassen
- **MUSS [MUST]** Licht und Exposition, Fläche oder Gefäßvolumen, Wasserverfügbarkeit und umweltbedingte Einschränkungen vom Aufrufer annehmen und **MUSS [MUST]** deren Quelle als `caller` kennzeichnen, nicht als Werkzeug
- **DARF NICHT [MUST NOT]** Licht, Fläche, Volumen oder Wasserverfügbarkeit aus dem Namen eines Standorts, dem Namen eines Orts oder dem Typ eines Standorts ableiten
- **MUSS [MUST]** die Winterhärtezone des Gartens als unbekannt melden, es sei denn, der Aufrufer liefert sie, da kein Werkzeug genannt ist, das sagt, in welcher Zone der Garten liegt
- **MUSS [MUST]** `get_sowing_calendar` nur mit einer einschränkenden `query` aufrufen, weil der Server einen uneingeschränkten Aufruf verweigert, und **MUSS [MUST]** eine Verweigerung oder ein leeres Ergebnis als Grund melden, warum ein Klimawert unbekannt ist
- **SOLLTE [SHOULD]** für vorhandene Beobachtungen und Messungen auf den Gartenkontext verweisen und **DARF NICHT [MUST NOT]** sie wiederholen

### B. Der Kandidatenpool

- **MUSS [MUST]** den Pool vom Aufrufer nehmen, wenn dieser Arten oder Sorten benennt
- **KANN [MAY]**, wenn der Aufrufer keine benennt, eine begrenzte Seite von `list_species` lesen, das am 2026-08-07 mit 210 Arten gemessen wurde und dessen Parameter nicht festgehalten sind, und **MUSS [MUST]** den Pool dann als Stichprobe mit seiner Größe melden und sagen, dass der Rest nicht betrachtet wurde
- **DARF NICHT [MUST NOT]** einen so gelesenen Pool als den Katalog oder als die vollständige Auswahl melden

### C. Harte Bedingungen und Präferenzen

Bedingungen gehören zu zwei Klassen, und ein Kandidat wird gegen jede Klasse getrennt beurteilt.

| Bedingung | Klasse | Felder | Was sie nicht abdeckt |
|-----------|--------|--------|-----------------------|
| Frostempfindlichkeit gegen die Frostdaten des Gartens | Hart, wo beides bekannt ist | `frost_sensitivity` an der Art; Frostdaten aus `get_sowing_calendar` | Der Wertevorrat von `frost_sensitivity` ist nicht festgehalten, die Bedingung wird also nur gebildet, wo ein Wert eindeutig lesbar ist; sonst ist sie unentschieden |
| Winterhärtezone gegen die Zone des Gartens | Hart, wo beides bekannt ist | `hardiness_zones[]` an der Art; die vom Aufrufer gelieferte Zone | Die Zone des Gartens hat keine Katalogquelle |
| Saat- und Erntezeitpunkt gegen das Erntefenster der Anbauenden | Präferenz | `direct_sow_months[]`, `harvest_months[]`, `bloom_months[]`, `sowing_indoor_weeks_before_last_frost` und der passende Eintrag von `growing_periods[]` | Die Monate auf oberster Ebene sind die Vereinigung über die Perioden, daher muss zuerst eine Periode gewählt werden |
| Tage bis zur Reife gegen die frostfreie Spanne | Präferenz | `days_to_maturity` der Sorte; Frostdaten | Ab wann `days_to_maturity` zählt, Aussaat oder Pflanzung, ist nicht festgehalten |
| Passung der Nachbarn | Präferenz | `compatible_companions[]` mit seinem `score` | Das Feld listet verträgliche Nachbarn: Sein Fehlen für ein Paar ist keine Unverträglichkeit |
| Die Ziele der Anbauenden | Präferenz | Eingabe des Aufrufers | — |
| Licht, Schatten, Staunässe und Boden-pH | **Keine Bedingung bildbar** | `shade_tolerance`, `waterlogging_tolerance` und `soil_ph_preference` wurden am 2026-08-07 bei beiden geprüften Arten als fehlend gemessen | Ob andere Arten sie tragen, ist nicht belegt; zwei von 210 wurden geprüft |

- **MUSS [MUST]** harte Bedingungen und Präferenzen in jedem Kandidatendatensatz als zwei getrennte Listen führen
- **MUSS [MUST]** einen Kandidaten bei einer verfehlten harten Bedingung ablehnen, **MUSS [MUST]** diese Bedingung mit Quelle und Belegstufe auflisten und **DARF NICHT [MUST NOT]** sie gegen eine Präferenz abwägen
- **DARF NICHT [MUST NOT]** einen Kandidaten wegen einer Präferenz ablehnen; eine Präferenz ordnet und wird als erfüllt, nicht erfüllt oder unbekannt gemeldet
- **DARF NICHT [MUST NOT]** eine harte Bedingung aus einem Feld bilden, das nicht als vorhanden beobachtet wurde, und **MUSS [MUST]** eine Bedingung, deren Art- oder Standortseite fehlt, als unentschieden melden
- **DARF NICHT [MUST NOT]** das Fehlen eines Nachbareintrags oder irgendeiner Liste als Beleg für Unverträglichkeit oder Verträglichkeit werten
- **MUSS [MUST]** vor dem Vergleich des Zeitpunkts den zutreffenden Eintrag von `growing_periods[]` wählen und **MUSS [MUST]** sagen, welcher verwendet wurde

### D. Eignung und Urteil

- **MUSS [MUST]** jeder Bedingung eines von `met`, `failed` oder `undetermined` geben; ein unbekannter Standortparameter oder ein fehlendes Artfeld macht die Bedingung zu `undetermined`, nie zu `met` und nie zu `failed`
- **MUSS [MUST]** jedem Kandidaten genau ein Urteil geben: `rejected`, wenn mindestens eine harte Bedingung verfehlt wurde, `eligible`, wenn jede bildbare harte Bedingung erfüllt ist und keine unentschieden bleibt, und sonst `undetermined`
- **DARF NICHT [MUST NOT]** `eligible` für einen Kandidaten mit einer unentschiedenen harten Bedingung zurückgeben
- **MUSS [MUST]** die Gründe für das Urteil in Worten zurückgeben, die Anbauende prüfen können, jeweils an ein Feld und seinen Wert gebunden

### E. Der Kandidatendatensatz

- **MUSS [MUST]** je Kandidat zurückgeben: den Artschlüssel, den Sortenschlüssel oder keinen, das Urteil, die Gründe, die verfehlten harten Bedingungen mit Quelle und Belegstufe, die unentschiedenen Bedingungen mit dem, was fehlt, und jede Präferenz als erfüllt, nicht erfüllt oder unbekannt mit ihrer Quelle
- **MUSS [MUST]** den Wert der Sorte verwenden, wenn die Sorte das Attribut trägt, sonst den Wert der Art, und **MUSS [MUST]** je verwendetem Attribut festhalten, welcher von beiden es war
- **MUSS [MUST]** eine Konfidenz, abgeleitet aus der höchsten Belegstufe, die das Urteil stützt, eine Unsicherheitsaussage und eine Liste fehlender Daten zurückgeben, gemäß den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md)
- **DARF NICHT [MUST NOT]** eine Konfidenz für ein Urteil angeben, das auf einem vom Aufrufer gelieferten Standortfakt ruht, ohne das zu sagen

### F. Die Ausgabe für den Pflanzplan

Das Ergebnis hat drei Blöcke: das Standortprofil (Abschnitt A, sieben Parameter), den Pool (seine Herkunft, `caller` oder `sample`, und seine Größe) und die Kandidatendatensätze (Abschnitt E). Der Pflanzplan liest je Kandidat `species_key`, `cultivar_key`, `verdict`, `failed_hard_constraints`, die Präferenzen, die Herkunft der Attribute und die Konfidenz.

- **MUSS [MUST]** die drei Blöcke in dieser Reihenfolge und mit diesen Namen zurückgeben, damit ein Verbraucher nichts neu ableitet
- **DARF NICHT [MUST NOT]** ein Feld zurückgeben, das der Skill nicht gelesen hat, und **MUSS [MUST]** ein ungelesenes Feld mit seinem Grund als fehlend auflisten

## Akzeptanzkriterien

- [ ] Ein Standortprofil listet alle sieben Parameter; jeder ist bekannt oder unbekannt, bei bekannten mit Wert, Quelle und Abrufzeitpunkt
- [ ] Licht und Exposition, Fläche oder Volumen, Wasserverfügbarkeit und umweltbedingte Einschränkungen sind nur bekannt, wenn der Aufrufer sie geliefert hat, und sind mit `caller` gekennzeichnet
- [ ] Die Winterhärtezone des Gartens ist unbekannt, es sei denn, der Aufrufer hat sie geliefert
- [ ] Kein Kandidat wird wegen einer Präferenz abgelehnt, und kein Kandidat mit einer unentschiedenen harten Bedingung ist geeignet
- [ ] Jeder abgelehnte Kandidat listet die verfehlte harte Bedingung mit Quelle und Belegstufe
- [ ] Jeder Kandidatendatensatz nennt je verwendetem Attribut, ob Sorte oder Art es geliefert hat
- [ ] Ein aus `list_species` gelesener Pool wird als Stichprobe mit seiner Größe gemeldet
- [ ] Aus Licht, Schatten, Staunässe oder Boden-pH wird keine harte Bedingung gebildet
- [ ] Die drei Ausgabeblöcke erscheinen in Reihenfolge mit den genannten Namen
- [ ] Jede Aussage über die Werkzeugoberfläche zitiert eine Spezifikation in diesem Repository; eine nicht erneut gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Zahl an Anforderungs-Aufzählungspunkten und dieselbe Zahl an Akzeptanz-Kontrollkästchen

## Quelle

- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Werkzeugkatalog, die Verweigerung eines uneingeschränkten `get_sowing_calendar` und die Mandantenfähigkeit
- [Der Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md) — die als vorhanden und als fehlend beobachteten Artfelder, `list_species` (210 Arten) und `get_sowing_calendar` mit `query`, das Frostdaten lieferte, alles am 2026-08-07 an der Referenzinstanz gemessen
- [Der Nährstoffprozess](../nutrient-imbalance-detection/de.md) — die Substratfelder
- [Die Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) — Belegstufen, die Ausgabe einer Empfehlung und der Gartenkontext
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Issue nolte/kamerplanter-goose#41 — die Scope-Listen und die fünf Kriterien stammen aus seinem Text; nolte/kamerplanter-goose#42, #47 und #39 — der Verbraucher, die Fruchtfolgearbeit und das Audit

## Offene Fragen

- **Was jeder Wert von `frost_sensitivity` bedeutet.** Das Feld ist als vorhanden festgehalten, sein Wertevorrat nicht. Eine darauf gebaute harte Bedingung kann nicht genauer sein, als der Wert lesbar ist. Offen, weil niemand die Werte aufgelistet hat; sie zu klären, braucht das Lesen mehrerer Arten an einer erreichbaren Instanz.
- **In welcher Zone der Garten liegt.** `list_hardiness_zones` listet Zonen, und kein festgehaltenes Feld sagt, welche zum Garten gehört. Bis ein Werkzeug oder Feld es sagt, kommt die Zone vom Aufrufer.
- **Ob andere Arten Licht-, Schatten-, Staunässe- oder Boden-pH-Felder tragen.** Zwei Arten wurden am 2026-08-07 geprüft, und keine trug sie. Offen, weil 208 von 210 nicht gelesen wurden; tragen einige sie, werden Bedingungen für diese Arten bildbar, und die Tabelle in Abschnitt C ändert sich.
- **Ab wann `days_to_maturity` zählt.** Aussaat und Pflanzung ergeben verschiedene Spannen gegen die Frostdaten. Offen, weil keine Spezifikation den Startpunkt festhält.
- **Die Antwortfelder von `list_hardiness_zones` und `get_sowing_calendar`.** Festgehalten ist nur, dass die Antwort des Saatkalenders Frostdaten enthält. Die genauen Felder sind nicht gemessen, weil der Server beim Schreiben dieser Spezifikation nicht erreichbar war.
- **Die Parameter von `list_species`.** Ob es eingeschränkt, geblättert oder gefiltert werden kann, ist nicht festgehalten; deshalb ist das Lesen des Pools eine begrenzte Seite und eine Stichprobe.
- **Wie Fruchtfolgebedingungen eingespeist werden, sobald nolte/kamerplanter-goose#47 existiert.** Bis dahin ist die Fruchtfolge unbekannt, und `compatible_companions` wird nur als Präferenz gelesen.
- **Wo das Audit, nolte/kamerplanter-goose#39, die Standortanalyse im Verhältnis zum Gartenkontext einordnet.** Beide beschreiben, was ein Garten enthält; diese Spezifikation fügt die Auslegung hinzu, und der Gartenkontext sammelt nur. Ob es zwei Artefakte bleiben, entscheidet das Audit.
