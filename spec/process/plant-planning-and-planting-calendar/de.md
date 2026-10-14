# Pflanzplanung und Pflanzkalender

Status: Entwurf
Portfolio-Scope: local

## Kontext

Eine Kulturwahl ist noch kein Plan. Ein Plan sagt, wann jede gewählte Kultur gesät wird, wann sie umgepflanzt wird, wann die Ernte erwartet wird und wohin sie kommt, und jede dieser Antworten ist ein Datum. Bei Daten richtet ein Verfahren, das aus Allgemeinwissen arbeitet, den größten Schaden an und klingt dabei am sichersten: „Tomaten im März säen“ stimmt für die meisten Gärten nicht und liest sich wie richtig. Der Kamerplanter-Katalog enthält einiges von dem, was ein Datum braucht — einen Saatkalender mit den Frostdaten des Gartens und Artfelder für Saatmonate, Erntemonate und Wachstumsperioden —, und den Rest nicht: Er nennt kein Feld für Beete oder Gefäße, für ein Ziel-Erntefenster oder für die Fruchtfolge.

Diese Spezifikation legt zwei Schritte fest. Der Pflanzkalender macht aus jeder gewählten Kultur die Fenster, in denen sie an diesem Garten gesät, umgepflanzt und geerntet werden kann, und sagt für jedes Fenster, welche Regel und welches Feld es ergeben haben. Der Plan macht aus dem Kalender Vorschläge für Pflanzdurchläufe, die eine Person prüfen kann: mit einer stabilen Identität je Durchlauf, einer Begründung und einer Konfidenz je Datum und einer Liste dessen, was nicht geplant wurde und warum. Beide sind rein lesend. Ein Plan ist ein Dokument; ihn anzuwenden ist ein eigener Schritt, und der gemessene Katalog hat kein Werkzeug, das das könnte (Abschnitt F).

Alles zur Werkzeugoberfläche unten ist zitiert aus der [Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) und aus dem [Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md), deren Messungen am 2026-08-07 an der Referenzinstanz gemacht wurden. **Nichts davon wurde beim Schreiben dieser Spezifikation erneut gemessen**: Der `kamerplanter`-MCP-Server war in der Sitzung, die sie entworfen hat, nicht erreichbar (`INVALID_CONFIG`). Werkzeug- und Feldnamen sind aus jenen Spezifikationen übernommen; ob sie noch existieren und was eine Antwort darüber hinaus trägt, bleibt unbelegt, bis ein `tools/list` und ein lesender Aufruf an einer erreichbaren Instanz es sagen.

Grenzen: Die [Spezifikation zu Standortanalyse und Kulturwahl](../site-analysis-and-crop-selection/de.md) besitzt den Kandidatendatensatz und das Standortprofil, die diese Spezifikation liest; die [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) besitzen das Gewicht einer Aussage, die Form einer Empfehlung und den Gartenkontext. Diese Spezifikation wendet sie an und wiederholt sie nicht. Die Beetaufteilung ist nolte/kamerplanter-goose#46, die Pflegeplanung nolte/kamerplanter-goose#43 und die Fruchtfolge nolte/kamerplanter-goose#47; die ersten beiden lesen die Ausgabe dieser Spezifikation, die dritte ist nicht gebaut. Die `-apply`-Rezepte für Garten- und Saisonpläne sind nolte/kamerplanter-goose#59. Das Audit, das entscheidet, welches Artefakt was besitzt, ist nolte/kamerplanter-goose#39, und nichts hier greift ihm vor. [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) besitzt die Rezeptmechanik, und [die Server-Spezifikation](../../mcp/kamerplanter-mcp-server/de.md) besitzt Transport, Authentifizierung und Mandantenfähigkeit.

Leserinnen und Leser: Autorinnen und Autoren von Garten-Skills und -Rezepten in diesem Repository, die Autorinnen von Beetaufteilung und Pflegeplanung, die den Plan verbrauchen, und alle, die einen Plan prüfen, bevor sie danach handeln.

## Ziele

- Jedes Datum in einem Plan nennt die Regel, die es ergeben hat, die Felder, aus denen es stammt, und die Belegstufe, auf der es ruht
- Ein Datum, das sich aus festgehaltenen Feldern nicht berechnen lässt, wird als unbekannt mit der fehlenden Eingabe gemeldet, nie geschätzt
- Ein Pflanzdurchlauf hat eine Identität, die davon abhängt, was er ist, nicht davon, in welcher Reihenfolge er aufgelistet wurde, sodass sich ein Plan mit dem nächsten vergleichen lässt
- Lesendes Planen und Anwenden sind getrennt, und ein Plan kann geprüft werden, bevor irgendetwas angewendet wird
- Der Plan kann von der Pflegeplanung und von der Beetaufteilung gelesen werden, ohne dass etwas neu abgeleitet wird

## Nicht-Ziele

- Einen Plan anwenden: Pflanzdurchläufe, Aufgaben oder Pflanzen anlegen. Der gemessene Katalog hat dafür kein Werkzeug (Abschnitt F)
- Kulturen wählen: das ist die [Kulturwahl](../site-analysis-and-crop-selection/de.md)
- Pflanzen Beeten zuordnen, Beete aufteilen oder die Fruchtfolge planen — nolte/kamerplanter-goose#46 und #47
- Pflegepläne für die gepflanzte Kultur — nolte/kamerplanter-goose#43
- Fakten liefern, die der Katalog nicht enthält. Wo es keine Quelle gibt, liefert der Aufrufer den Wert, oder er bleibt unbekannt
- Typische Saatzeiten, Dauern oder Versätze aus Allgemeinwissen. Ein Datum stammt aus einem festgehaltenen Feld oder ist unbekannt

## Anforderungen

### A. Eingaben

| Eingabe | Quelle | Nicht belegt |
|---------|--------|--------------|
| Kandidatendatensätze | [Kulturwahl](../site-analysis-and-crop-selection/de.md), Abschnitte E und F | — |
| Standortprofil, einschließlich der Frostdaten des Gartens | [Standortanalyse](../site-analysis-and-crop-selection/de.md), Abschnitt A | Das Format der Frostdaten: Festgehalten ist nur, dass `get_sowing_calendar` mit einer `query` sie lieferte |
| Die bestehenden Pflanzdurchläufe des Gartens | `list_planting_runs` | Seine Parameter und seine Paginierung sind nicht festgehalten |
| Beete und Gefäße | Nur der Aufrufer: Einträge `name:area_or_volume`, durch Kommas getrennt | Keine Quelle im gemessenen Katalog |
| Ziel-Erntefenster | Nur der Aufrufer, in den Worten des Aufrufers | Keine Quelle |
| Bevorzugte Anbauweise | Nur der Aufrufer: `direct_sow` oder `indoor_then_transplant` | Keine Quelle |

- **MUSS [MUST]** die Kandidatendatensätze so übernehmen, wie sie sind, und **DARF NICHT [MUST NOT]** ein Urteil neu berechnen oder übersteuern
- **MUSS [MUST]** Beete und Gefäße, das Erntefenster und die bevorzugte Anbauweise mit der Quelle `caller` kennzeichnen und jedes als unbekannt melden, wenn der Aufrufer es nicht geliefert hat
- **MUSS [MUST]** die Beet-Zeichenkette an den Kommas und am ersten Doppelpunkt jedes Eintrags auftrennen und **DARF NICHT [MUST NOT]** den zusammenhängenden Text als Namen weitergeben
- **DARF NICHT [MUST NOT]** einen Durchlauf einem Beet zuordnen, das der Aufrufer nicht genannt hat
- **SOLLTE [SHOULD]** die bestehenden Pflanzdurchläufe des Gartens als Kontext auflisten und **DARF NICHT [MUST NOT]** ein unvollständiges oder fehlgeschlagenes Lesen als Beleg werten, dass es keine gibt

### B. Der Pflanzkalender

Ein Fenster ist ein Anfang und ein Ende für einen Schritt einer Anbauweise einer Wachstumsperiode eines Kandidaten. Ein Kandidat mit mehreren `growing_periods[]` hat mehrere Mengen von Fenstern.

| Fenster | Anbauweise | Felder, die es speisen | Was sie nicht abdecken |
|---------|------------|------------------------|------------------------|
| Aussaat | Direktsaat | `direct_sow_months[]` der gewählten Wachstumsperiode; die Frostdaten des Gartens bei einer frostempfindlichen Kultur | Was die Werte von `frost_sensitivity` bedeuten und das Format der Frostdaten sind nicht festgehalten, die Frostgrenze wird also nur angewendet, wo beides eindeutig lesbar ist |
| Vorkultur | Vorkultur, dann Umpflanzen | `sowing_indoor_weeks_before_last_frost`; das Datum des letzten Frosts im Garten | Das Format der Frostdaten |
| Umpflanzen | Vorkultur, dann Umpflanzen | Die Frostdaten des Gartens bei einer frostempfindlichen Kultur | Dasselbe, und wie lange ein Sämling vor dem Umpflanzen braucht: kein Feld sagt es |
| Ernte | Beide | `harvest_months[]` der gewählten Wachstumsperiode | Die Monate auf oberster Ebene sind die Vereinigung über die Perioden, daher muss zuerst eine Periode gewählt werden |
| Ernte, aus der Reife | Beide | `days_to_maturity` der Sorte | Ab wann es zählt, Aussaat oder Umpflanzen, ist nicht festgehalten |

- **MUSS [MUST]** den zutreffenden Eintrag von `growing_periods[]` wählen, **MUSS [MUST]** sagen, welchen, und **DARF NICHT [MUST NOT]** die Monate auf oberster Ebene verwenden, wenn Perioden existieren
- **MUSS [MUST]** ein Fenster nur aus Feldern berechnen, deren Bedeutung festgehalten ist, und **MUSS [MUST]** ein Fenster, dessen Feld fehlt, nicht lesbar ist oder in der Bedeutung nicht festgehalten ist, als `unknown` mit der fehlenden Eingabe melden
- **DARF NICHT [MUST NOT]** ein typisches Datum, eine typische Dauer oder einen Versatz aus Allgemeinwissen nutzen, um ein Fenster zu füllen oder zu begrenzen
- **DARF NICHT [MUST NOT]** ein Erntedatum aus `days_to_maturity` berechnen, solange sein Ausgangspunkt nicht festgehalten ist, und **MUSS [MUST]** für das Erntefenster `harvest_months[]` verwenden und den Reifevergleich als `unknown` melden
- **MUSS [MUST]** den Wert der Sorte verwenden, wenn die Sorte das Attribut trägt, sonst den Wert der Art, und **MUSS [MUST]** je verwendetem Attribut festhalten, welcher von beiden es war
- **MUSS [MUST]** jedem Fenster die angewendete Regel, ihre Felder, seine Quelle (ein Werkzeug oder `caller`), seinen Abrufzeitpunkt und seine Belegstufe gemäß den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) mitgeben
- **MUSS [MUST]** ein Fenster mit dem Ziel-Erntefenster des Aufrufers als Präferenz vergleichen, erfüllt, nicht erfüllt oder unbekannt, und **DARF NICHT [MUST NOT]** einen Kandidaten deswegen ausscheiden

### C. Der Plan

- **MUSS [MUST]** einen Pflanzdurchlauf nur für einen Kandidaten erzeugen, dessen Urteil `eligible` ist und dessen Aussaatfenster bekannt ist
- **MUSS [MUST]** jeden anderen Kandidaten unter „nicht geplant“ mit genau einem Grund auflisten: `rejected` und die verfehlte harte Bedingung, `undetermined` und die fehlende Eingabe, oder `window unknown` und die fehlende Eingabe
- **MUSS [MUST]** jedem Durchlauf eine Kennung aus Artschlüssel, Sortenschlüssel oder keinem, Anbauweise und Wachstumsperiode geben, wobei die Periode über die Monate bestimmt wird, die sie trägt, und nicht über ihre Position, und **DARF NICHT [MUST NOT]** sie aus der Reihenfolge der Eingabe oder aus der Zeit bilden
- **MUSS [MUST]** jedem Durchlauf seine Anbauweise, seine Fenster mit ihren Regeln, einen Ort, der ein vom Aufrufer genanntes Beet oder `unassigned` ist, einen Hinweis zur Folgesaat, einen Hinweis zur Fruchtfolge und je Datum eine Begründung, eine aus der höchsten stützenden Belegstufe abgeleitete Konfidenz, eine Unsicherheitsaussage und eine Liste fehlender Daten mitgeben, gemäß den [Entscheidungsregeln für den Garten](../garden-decision-policy/de.md)
- **MUSS [MUST]** die Fruchtfolge als unbekannt melden und **DARF NICHT [MUST NOT]** `compatible_companions[]` als Fruchtfolgebedingung lesen
- **MUSS [MUST]** eine Folgesaat nur nennen, wo die eigenen Daten des Kalenders zwei Fenster aufeinander folgen lassen, und **DARF NICHT [MUST NOT]** eine erfinden
- **DARF NICHT [MUST NOT]** eine Konfidenz für ein Datum angeben, das auf einem vom Aufrufer gelieferten Fakt ruht, ohne das zu sagen

Das Plandokument hat vier Blöcke, in dieser Reihenfolge und unter diesen Namen: `PLAN HEADER` (der Garten, vorgegeben oder ermittelt, und die Eingabeblöcke, aus denen er entstand), `PLANTING RUNS`, `NOT PLANNED` und `APPLY CONTRACT`.

| Verbraucher | Liest je Durchlauf |
|-------------|--------------------|
| Pflegeplanung (nolte/kamerplanter-goose#43) | die Durchlaufkennung, den Artschlüssel, den Sortenschlüssel, die Anbauweise, das Aussaat-, Umpflanz- und Erntefenster, die Konfidenz |
| Beetaufteilung (nolte/kamerplanter-goose#46) | die Durchlaufkennung, den Ort, die Fläche oder das Volumen, wie der Aufrufer es lieferte, den Hinweis zur Folgesaat, den Hinweis zur Fruchtfolge |

- **MUSS [MUST]** die vier Blöcke in dieser Reihenfolge mit diesen Namen zurückgeben und **DARF NICHT [MUST NOT]** ein Feld zurückgeben, das nicht gelesen wurde, sondern **MUSS [MUST]** ein ungelesenes Feld mit seinem Grund als fehlend auflisten

### D. Die Saisonsicht

- **MUSS [MUST]** die Saisonsicht ausschließlich aus den Durchläufen des Plans bilden, gruppiert nach den Monaten ihrer Fenster, und **DARF NICHT [MUST NOT]** ein Datum hinzufügen, das nicht im Plan steht
- **MUSS [MUST]** die Folgesaaten auflisten, die der Plan nennt, und keine anderen, und **MUSS [MUST]** angeben, dass eine Saisonsicht über einen Plan mit unbekannten Fenstern unvollständig ist, und sie benennen

### E. Determinismus

- **MUSS [MUST]** den Plan zu einer Funktion der gelieferten Eingabeblöcke und der Regeln machen, sodass zwei Läufe über dieselben Blöcke dieselben Plan-Fakten ergeben: die Durchlaufkennungen, die Anbauweisen, die Fenster, die Orte, die Gründe für „nicht geplant“ und die Konfidenzstufen
- **MUSS [MUST]** die Durchläufe nach Inhalt ordnen (Artschlüssel, Sortenschlüssel, Anbauweise, Periode) und **DARF NICHT [MUST NOT]** sie nach der Reihenfolge der Eingabe ordnen
- **DARF NICHT [MUST NOT]** das aktuelle Datum innerhalb der Plan-Fakten lesen; Abrufzeitpunkte werden neben den Fakten gemeldet und nicht verglichen
- **MUSS [MUST]** angeben, dass byte-identischer Fließtext außerhalb der Plan-Fakten nicht behauptet wird und dass die Eigenschaft an einem festen Beispiel aus Eingabeblöcken geprüft wird und nicht an einem laufenden Garten

### F. Trennung und Anwendungsvertrag

- **MUSS [MUST]** das Planen rein lesend halten: Die Planungs-Skills und -Rezepte rufen kein zustandsänderndes Werkzeug auf
- **MUSS [MUST]** in jeden Plan einen Block `APPLY CONTRACT` aufnehmen, der je Durchlauf angibt, was ein späteres `-apply`-Rezept anlegen müsste (einen Pflanzdurchlauf mit Art, Sorte, Anbauweise, Fenstern und Ort), und **MUSS [MUST]** angeben, dass der gemessene Katalog kein Werkzeug hat, das einen Pflanzdurchlauf, eine Aussaat- oder Pflanzaufgabe oder einen Plan anlegt: Die dort festgehaltenen Schreibwerkzeuge sind `add_plant_diary_entry`, `confirm_care_task`, `archive_plant`, `set_plant_location`, `claim_diary_analysis`, `submit_diary_analysis`, `transition_plant_phase`, `assign_species_phase_sequence`, `assign_nutrient_plan`, `record_feeding_event` und `create_inspection` sowie das Einrichtungswerkzeug `create_site`, und keines davon tut das
- **MUSS [MUST]** nolte/kamerplanter-goose#59 als den Ort benennen, an dem die `-apply`-Rezepte geführt werden, und **DARF NICHT [MUST NOT]** ein Rezept mit dem Suffix `-apply` ausliefern, das nicht schreibt, was seine Beschreibung sagt
- **MUSS [MUST]** das Anwenden eines Plans einem eigenen Rezept überlassen, das einen genehmigten Plan nimmt, nachdem eine Person ihn geprüft hat

## Akzeptanzkriterien

- [ ] Jedes Fenster in einem Plan nennt seine Regel, seine Felder, seine Quelle, seinen Abrufzeitpunkt und seine Belegstufe, und ein Fenster, das sich nicht berechnen lässt, ist unbekannt mit der fehlenden Eingabe
- [ ] Kein Fenster entsteht aus einem typischen Datum, einer typischen Dauer oder einem Versatz, und kein Erntedatum aus `days_to_maturity`
- [ ] Die verwendete Wachstumsperiode ist für jeden Kandidaten mit Perioden benannt
- [ ] Nur `eligible`-Kandidaten mit bekanntem Aussaatfenster haben einen Durchlauf; jeder andere Kandidat ist mit einem Grund aufgelistet
- [ ] Eine Durchlaufkennung ändert sich nicht, wenn sich die Reihenfolge der Eingabe ändert
- [ ] Ein Durchlauf wird einem Beet nur zugeordnet, wenn der Aufrufer es genannt hat; sonst ist er `unassigned`
- [ ] Die Fruchtfolge ist in jedem Durchlauf unbekannt, und `compatible_companions[]` wird nicht als Fruchtfolgebedingung verwendet
- [ ] Eine Folgesaat wird nur genannt, wo zwei Fenster nach den Daten des Kalenders aufeinander folgen
- [ ] Der Plan hat die vier Blöcke in Reihenfolge, und der Anwendungsvertrag sagt, dass der gemessene Katalog kein Werkzeug hat, das einen Pflanzdurchlauf anlegt
- [ ] Zwei Läufe über dieselben Eingabeblöcke ergeben an einem festen Beispiel dieselben Plan-Fakten, und der Plan sagt, was nicht behauptet wird
- [ ] Die Planungs-Skills und -Rezepte rufen kein zustandsänderndes Werkzeug auf
- [ ] Jede Aussage über die Werkzeugoberfläche zitiert eine Spezifikation in diesem Repository; eine nicht erneut gemessene Aussage sagt das
- [ ] Die deutsche und die englische Datei haben dieselben Überschriften in derselben Reihenfolge, dieselbe Zahl an Anforderungs-Aufzählungspunkten und dieselbe Zahl an Akzeptanz-Kontrollkästchen

## Quelle

- [Die Spezifikation des Kamerplanter-MCP-Servers](../../mcp/kamerplanter-mcp-server/de.md) — der Werkzeugkatalog, die Schreibwerkzeuge, die Verweigerung eines uneingeschränkten `get_sowing_calendar` und die Mandantenfähigkeit
- [Der Prozess zur Artdaten-Prüfung](../species-baseline-verification/de.md) — die als vorhanden beobachteten Art- und Sortenfelder (`direct_sow_months[]`, `harvest_months[]`, `sowing_indoor_weeks_before_last_frost`, `growing_periods[]`, `frost_sensitivity`, `compatible_companions[]`, `days_to_maturity`) und `get_sowing_calendar` mit `query`, das Frostdaten lieferte, am 2026-08-07 an der Referenzinstanz gemessen
- [Die Anleitung zur Artdaten-Prüfung](../../../docs/de/guides/species-baseline-check.md) — sagt, dass die Frostdaten des Saatkalenders je Garten gelten und nennt den letzten Frost, die Eisheiligen und den ersten Frost als Anker; das Format steht dort nicht
- [Die Spezifikation zu Standortanalyse und Kulturwahl](../site-analysis-and-crop-selection/de.md) — der Kandidatendatensatz, das Standortprofil und die Ausgabe, die diese Spezifikation liest
- [Die Entscheidungsregeln für den Garten](../garden-decision-policy/de.md) — Belegstufen, die Ausgabe einer Empfehlung und der Gartenkontext
- [Das Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Issue nolte/kamerplanter-goose#42 — die Planungsfaktoren und die fünf Kriterien stammen aus seinem Text; nolte/kamerplanter-goose#43, #46, #47, #59 und #39 — die Verbraucher, die Fruchtfolge, die Anwendungshälfte und das Audit

## Offene Fragen

- **Das Format der Frostdaten des Saatkalenders.** Festgehalten ist nur, dass Frostdaten zurückkommen, und eine Anleitung in diesem Repository spricht vom letzten Frost, den Eisheiligen und dem ersten Frost als Ankern. Ob es einzelne Daten, Spannen oder Wochennummern sind, ist nicht festgehalten. Bis dahin wird ein davon begrenztes Fenster nur berechnet, wo die Antwort eindeutig lesbar ist.
- **Ab wann `days_to_maturity` zählt.** Aussaat und Umpflanzen ergeben verschiedene Erntedaten. Offen, weil keine Spezifikation den Ausgangspunkt festhält; bis dahin stammt die Ernte aus `harvest_months[]`.
- **Der Wertevorrat von `frost_sensitivity`.** Das Feld ist als vorhanden festgehalten, seine Werte nicht. Eine Frostgrenze für ein Fenster muss wissen, welche Werte „empfindlich“ bedeuten.
- **Wie eine Wachstumsperiode bestimmt wird.** Die Einträge von `growing_periods[]` tragen festgehaltenermaßen eigene Monate; ob sie einen Namen oder Schlüssel tragen, ist nicht festgehalten. Diese Spezifikation bestimmt eine Periode über ihre Monate, damit eine Durchlaufkennung nicht von der Position abhängt, was eine Entscheidung ohne diese Tatsache ist.
- **Die Parameter von `list_planting_runs`.** Ob es gefiltert oder geblättert werden kann, ist nicht festgehalten, und auch nicht, wie ein zurückgegebener Durchlauf aufgebaut ist; der Plan listet bestehende Durchläufe nur als Kontext auf.
- **Ob eine laufende Instanz ein Werkzeug hat, das Pflanzdurchläufe anlegt.** Der gemessene Katalog hat keines, die Server-Spezifikation sagt, jede Werkzeugzahl als Untergrenze zu behandeln, und niemand hat `tools/list` an einer erreichbaren Instanz ausgeführt. Die `-apply`-Rezepte warten darauf, geführt als nolte/kamerplanter-goose#59.
- **Wie Fruchtfolgebedingungen ankommen.** Bis nolte/kamerplanter-goose#47 existiert, ist die Fruchtfolge in jedem Durchlauf unbekannt.
- **Wie der Determinismus gemessen wird.** Diese Spezifikation legt die Plan-Fakten fest und verlangt, dass sie über dieselben Eingabeblöcke gleich sind. Geprüft wird das an einem festen Beispiel aus als Text ausgeschriebenen Eingabeblöcken, mit Vergleich wiederholter Läufe; das zeigt die Eigenschaft für dieses Beispiel und nicht für einen laufenden Garten, und wie viele Läufe nötig sind, um sie stabil zu nennen, wird hier nicht entschieden.
- **Wo das Audit, nolte/kamerplanter-goose#39, die Planung im Verhältnis zu Gartenkontext und Standortanalyse einordnet.** Ob Kalender und Plan zwei Artefakte bleiben, entscheidet das Audit.
