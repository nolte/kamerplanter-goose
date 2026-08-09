# Persona-Review aus Anbausicht

Status: Entwurf
Portfolio-Scope: local

## Kontext

Ein Rezept in diesem Repository sagt jemandem, was er mit einer lebenden Pflanze tun soll. Der Bericht, den es druckt, ist das Produkt — nicht die Tool-Aufrufe dahinter, nicht das YAML. Zweierlei kann an diesem Produkt falsch sein, und nichts im Repository fängt derzeit eines davon ab:

- **Der Rat ist fachlich falsch.** `tests/validate_recipes.py` prüft das Hausmuster, `goose recipe validate` das Schema, die Process-Specs die Argumentationsführung. Keines bemerkt, dass eine Empfehlung biologisch unsinnig ist, dass ein EC-Zielwert für die Kultur außerhalb des Bereichs liegt oder dass eine Behandlung innerhalb der Karenzzeit vorgeschlagen wird.
- **Der Rat ist fachlich einwandfrei und für seine Leserschaft nutzlos.** Ein Bericht, der mit „Belege der Stufe 2 weisen auf eine Leitfähigkeitsabweichung von 0,4 mS/cm gegenüber dem Phasenziel hin" beginnt, ist korrekt und wird von jemandem mit drei Zimmerpflanzen ungelesen geschlossen. Ein Bericht, der Runoff-EC nie erwähnt, nützt jemandem mit einem Zelt nichts. Derselbe Lauf kann nicht beides leisten, und so zu tun als ob, ist der Weg, am Ende keinem von beiden zu dienen.

Diese Spezifikation begründet ein Review, das ein Rezept, eine Process-Spec oder die tatsächliche Ausgabe eines Laufs **als eine bestimmte anbauende Person** liest und berichtet, was diese Person damit anfangen würde. Vier bewusst weit auseinanderliegende Personas, übernommen aus dem Reviewer-Cluster in `nolte/kamerplanter`, wo sie auf Anforderungsdokumente angewandt wurden. Hier gelten sie Rezepten und den Berichten, die Rezepte erzeugen.

**Das sind nicht die Audiences aus `AUDIENCES.md`.** Jene Datei beschreibt, wer *dieses Repository* konsumiert — `plant-owner`, `recipe-author`, `self-hoster` und die übrigen —, und ihre IDs werden von Dokumentations-Frontmatter und Issue-Vorlagen referenziert. Die Personas hier sind die Anbausituationen, in denen der Rat eines Rezepts landet. Ein einzelner `plant-owner` kann jede der vier sein, und die vier sind sich über denselben Bericht uneinig. Die beiden Achsen stehen quer zueinander; ein Review unter dieser Spezifikation darf `AUDIENCES.md`-IDs weder umnummerieren noch erweitern noch als Personas zitieren.

Leserschaft: Rezeptautorinnen und -autoren in diesem Repository sowie alle, die entscheiden, ob ein Rezept reif ist, gegen einen echten Garten zu laufen.

## Ziele

- Der Rat eines Rezepts wird von jemandem auf fachliche Stichhaltigkeit geprüft, der den Fehler sehen kann, und auf Brauchbarkeit von denen, die ihn tatsächlich erhalten
- Das Urteil jeder Persona bleibt getrennt, denn ein Bericht, der für eine hervorragend und für eine andere unbrauchbar ist, ist ein echtes Ergebnis und kein wegzumittelnder Widerspruch
- Ein Befund benennt die Folge für diese Persona — App gelöscht, Nützlingsfreilassung verschenkt, Pflanze tot — statt einer Stilvorliebe
- Keine fachliche Korrektur gelangt aufgrund der Erinnerung der prüfenden Instanz in ein Review
- Prüfgegenstand darf ein Rezept, eine Process-Spec oder die reale Ausgabe eines Laufs sein, denn ein Rezept kann gut spezifiziert sein und trotzdem Unbrauchbares drucken

## Nicht-Ziele

- Rezeptmechanik prüfen — Extension-Blöcke, `env_keys`, `-apply`-Suffixe, Arbeitsverzeichnis-Angaben. Das gehört `tests/validate_recipes.py` und dem [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md); es hier zu wiederholen, hieße eine Regel in zwei Ebenen zu führen
- Den Zustand einer einzelnen Pflanze beurteilen; die Personas prüfen das Verfahren, nicht einen Garten
- Den Schädlings-, Arten- oder Nährstoffkatalog korrigieren — Befunde zu Daten gehen an [Schädlingsdruck](../pest-pressure-assessment/de.md) und [Speziesbaseline](../species-baseline-verification/de.md), Korrekturen an `nolte/kamerplanter`
- Prosa um ihrer selbst willen redigieren; ein Lesbarkeitsbefund muss die Persona benennen, die er blockiert
- Das Audience-Artefakt in `AUDIENCES.md` oder die daraus abgeleiteten Dokumentationsspuren ersetzen
- Ein Konsensurteil über die Personas hinweg erzeugen

## Die Personas

Jede ist eine Prüfperspektive mit festem Profil, fester Vokabulargrenze und festem Abbruchgrund. Das Profil macht den Befund vorhersagbar statt stimmungsabhängig, und es wird aus dem Quell-Cluster zitiert statt neu erfunden.

### `agronomy` — die Pflanzenwissenschaftlerin

Zwanzig Jahre Praxis mit Schwerpunkt auf Indoor-Anbau, Zimmerpflanzen, Hydroponik und gesteuertem Anbau (CEA), mit Freiland-Phänologie als Vergleichsbasis. Liest auf **biologische Korrektheit**: Pflanzenphysiologie unter künstlichen Bedingungen, Licht (PPFD, DLI, Spektrum, Photoperiode), Klimasteuerung (VPD, CO₂, DIF, Luftzirkulation), integrierter Pflanzenschutz, Taxonomie und Nomenklatur.

Fragt: Stimmt diese Aussage, ist diese Empfehlung sicher, trägt diese Schlusskette, und wird hier ein artspezifischer Wert behauptet, den niemand verifiziert hat?

Diese Perspektive trägt die strengste Belegregel der Spezifikation und ist die einzige, die fachliche Korrekturen aussprechen darf.

### `indoor-grower` — der Zeltbetreiber

Zehn Jahre in einem 120×120×200-cm-Zelt, 480 W LED, Abluft mit Aktivkohlefilter, Coco-Perlit-Fertigation, photoperiodische und Autoflower-Genetik, Mutterpflanzen und Stecklinge. Trainiert mit Topping, LST, SCROG, Lollipopping. Führt ein Trichom-Mikroskop, protokolliert Temperatur und Luftfeuchte durch Trocknung und Cure und misst Erfolg in Gramm je Quadratmeter.

Fragt: Kann ich meinen kompletten Zyklus hier abbilden, hilft mir das zu mehr und besserem Ertrag, ist das praxistauglich oder nur theoretisch schön, und würde ich es täglich nutzen?

Findet die Lücke zwischen einem *abgedeckten* Arbeitsablauf und einem, der *um 23 Uhr mit nassen Händen* funktioniert.

### `casual-owner` — der widerwillige Zimmerpflanzenhalter

Zweiunddreißig, Büro, drei Zimmerpflanzen, eine davon unbestimmt. Botanisches Wissen nahe null. Zwei Pflanzen sind im letzten Jahr eingegangen. Motivation minimal, Geduld kürzer: Mehr als drei Klicks nerven, und jede Hürde ist ein Grund aufzuhören. Versteht kein Latein. **„EC", „VPD" und „PPFD" sind Fremdwörter, die aktiv abschrecken.** Will eine Push-Nachricht „Gieß deine Monstera" und sonst nichts.

Fragt: Was soll ich jetzt konkret tun, warum muss ich das ausfüllen, kann man das auf Deutsch sagen, und würde ich das nach zwei Tagen löschen?

Diese Perspektive liefert die Befunde, die sonst niemand liefern kann, weil alle anderen das Vokabular bereits kennen. Ihr Urteil ist ein Stellvertreter dafür, ob die Software den Erstkontakt mit einem gewöhnlichen Menschen überlebt.

### `outdoor-gardener` — die Beetplanerin

Fünfundvierzig, fünfzehn Jahre Praxis, 400 m² Hausgarten plus 80 m² Parzelle im Gemeinschaftsgarten, Mitteleuropa (USDA 7b–8a). Rund 120 Pflanzen gleichzeitig, davon 40 mehrjährig. Systematische Vierjahresrotation, Mischkultur, Voranzucht ab Februar auf der Fensterbank und im Folientunnel, eigener Kompost und Brennnesselsud, Regenwasser aus dem IBC. Überwintert Kübelpflanzen, gräbt Dahlien aus, deckt Beete ab. Mittlere Technikaffinität; hat drei Garten-Apps probiert, keine konnte alles.

Fragt: Was muss wann wohin, was wird wann geerntet, was muss vor dem ersten Frost herein, halte ich vier Jahre Fruchtfolge im Kopf, und wer gießt diese Woche die gemeinsame Parzelle?

Findet alles, was eine einzelne Pflanze im Topf in der Wohnung voraussetzt — und die saisonalen und mehrjährigen Horizonte, über die ein reines Indoor-Design nie nachdenken muss.

## Belegdisziplin

Unverändert aus dem Quell-Cluster übernommen, weil sie genau den Fehler verhindert, für den ein Persona-Review am anfälligsten ist: eine autoritativ klingende artspezifische Zahl, die niemand geprüft hat.

**Niemals eine Fachtatsache erfinden, schätzen oder aus dem Kontext ableiten.** Das bindet alle vier Perspektiven, nicht nur `agronomy`. Es gilt für artspezifische Werte (PPFD, Temperatur, pH, EC, VPD), Taxonomie, Toxizitäts- und Sicherheitsaussagen, Schädlings-Wirts-Zuordnungen, Nährstoffbedarfe und Dosierungen sowie Ertrags- und Wachstumsangaben.

Jede fachliche Aussage, die als Korrektur angeboten wird, muss aus **drei unabhängigen, überprüfbaren Quellen** ableitbar sein: begutachtete Fachliteratur; offizielle Institutionen (JKI, BfN, EPPO, FAO, USDA, RHS, ASPCA); anerkannte Fachbücher; standardisierte Datenbanken (GBIF, POWO, CABI, Tropicos); oder Herstellerdatenblätter für produktspezifische Werte. **Nicht akzeptiert:** Blogs, Foren, Social Media, Wikis ohne wissenschaftliche Referenz oder das eigene Expertenwissen ohne Beleg.

Eine nicht belegbare Aussage wird ein offener Recherchepunkt, keine abgeschwächte Behauptung. Jedes Review führt einen Abschnitt dazu — er darf leer sein, aber niemals fehlen:

| Nr. | Aussage | Verfügbare Quellen | Fehlend | Empfohlene Recherche |
|-----|---------|--------------------|---------|----------------------|

Für Persona-Reaktionen gilt die Regel nicht. „Ich wüsste nicht, was dieses Wort bedeutet" braucht keinen Beleg; es ist der Befund.

## Befunde und Schweregrade

Geordnet danach, was die Persona als Nächstes tut, nicht danach, wie falsch der Text ist:

| Rang | Bedeutung |
|------|-----------|
| **Blocker** | Diese Persona hört auf. Die Pflanze nimmt Schaden, der Rat ist unsicher, oder die App wird gelöscht |
| **Frustrierend** | Es funktioniert und kostet die Persona jedes Mal etwas |
| **Überfordernd** | Korrekt und über diese Persona hinweg formuliert; für Fachleute brauchbar, für sie eine Wand |
| **Gut gelöst** | Ausdrücklich benannt, damit eine spätere Änderung es nicht stillschweigend entfernt |
| **Wunsch** | Wäre hilfreich, das Fehlen ist kein Mangel |

Jeder Befund benennt Ziel und Fundstelle, die Folge für die Persona und — bei `agronomy` — seine Quellen oder seine Nummer im Recherche-Abschnitt. Ein Befund, der nur eine Vorliebe benennt, ist keiner.

## Ausgabe

Ein Bericht je Persona und Prüfgegenstand. Berichte werden unter `.audits/grower-persona-review/` abgelegt, nie in `spec/`: Ein Review ist eine Beobachtung zu einem Zeitpunkt, und `spec/` hält, was gelten soll.

Jeder Bericht schließt mit einer festen Tabelle und einer maschinenlesbaren Schlusszeile, wie es jedes Rezept hier tut:

```
REVIEW: pass
REVIEW: fail — <der schwerwiegendste einzelne Blocker>
```

`fail` heißt, dass diese Persona aufhören würde. Es ist eine Aussage über eine Perspektive, kein Urteil über das Rezept — drei Bestanden und ein Durchgefallen ist ein normales und aufschlussreiches Ergebnis, und es zu einer Punktzahl zu mitteln, zerstört das Einzige, was das Review hervorbringt.

## Anforderungen

- **MUSS [MUST]** je Lauf als genau eine Persona prüfen und **DARF NICHT** Personas vermischen oder ihre Urteile mitteln
- **DARF NICHT [MUST NOT]** einen artspezifischen Wert, eine taxonomische Zuordnung, eine Toxizitätsaussage, eine Schädlings-Wirts-Zuordnung, eine Dosierung oder eine Ertragszahl ohne drei unabhängige, zitierbare Quellen behaupten
- **MUSS [MUST]** in jedem Bericht einen Abschnitt für offene Recherchepunkte führen, leer wenn nichts aussteht, und **DARF** ihn **NICHT** weglassen
- **MUSS [MUST]** zu jedem Befund eine Folge für die Persona angeben und **DARF NICHT** eine bloße Stilvorliebe als Befund melden
- **MUSS [MUST]** Berichte unter `.audits/grower-persona-review/` schreiben und **DARF NICHT** nach `spec/`, `recipes/` oder `.claude/` schreiben
- **MUSS [MUST]** mit der festen Tabelle und genau einer `REVIEW:`-Zeile schließen
- **DARF NICHT [MUST NOT]** ein Kamerplanter- oder Home-Assistant-Tool aufrufen; das Review liest Dateien dieses Checkouts
- **DARF NICHT [MUST NOT]** Regeln der Rezeptmechanik wiederholen, die dem [Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md) gehören, und **SOLLTE** einen Mechanikfehler stattdessen als vorgeschlagene Prüfung an `tests/validate_recipes.py` weiterreichen
- **DARF NICHT [MUST NOT]** `AUDIENCES.md`-IDs als Personas behandeln und **SOLLTE** die Beziehung ausdrücklich benennen, wenn ein Befund beide Achsen berührt
- **SOLLTE [SHOULD]** die reale Ausgabe eines Laufs als Prüfgegenstand annehmen, denn ein Rezept kann gut spezifiziert sein und trotzdem Unlesbares drucken
- **SOLLTE [SHOULD]** benennen, was gut gelöst ist, damit eine spätere Änderung es nicht stillschweigend entfernt
- **SOLLTE [SHOULD]** einen Datenqualitätsbefund an [Schädlingsdruck](../pest-pressure-assessment/de.md) oder [Speziesbaseline](../species-baseline-verification/de.md) weiterreichen, statt ihn hier aufzulösen
- **KANN [MAY]** die Stimme der Persona zitieren, wo das einen Befund greifbar macht, sofern der Befund auch ohne das Zitat trägt

## Akzeptanzkriterien

- [ ] Jeder Bericht weist genau eine Persona aus
- [ ] Jeder Bericht enthält einen Abschnitt für offene Recherchepunkte
- [ ] Keine fachliche Korrektur erscheint ohne drei Quellen oder eine Recherchepunkt-Nummer
- [ ] Jeder Befund benennt eine Folge für die Persona
- [ ] Jeder Bericht endet mit genau einer `REVIEW:`-Zeile
- [ ] Kein Bericht wird außerhalb von `.audits/` geschrieben
- [ ] Kein Review-Lauf ruft ein MCP-Tool auf
- [ ] Kein Befund wiederholt eine Regel, die dem Rezeptprojekt-Muster gehört
- [ ] Kein Bericht zitiert eine `AUDIENCES.md`-ID als Persona
- [ ] Befunde erscheinen unter den hier definierten Schweregraden, in dieser Reihenfolge

## Offene Fragen

- Ob vier Personas der richtige Schnitt sind. Das Quell-Cluster trug mehr — darunter eine Smart-Home- und eine Frontend-Design-Perspektive —, und beide hätten hier plausible Ziele. Sie hinzuzufügen ist billig; festzustellen, dass sie fehlen, ist es, was diese Frage verfolgt.
- Ob die Ausgabe eines Laufs nach jeder Rezeptänderung automatisch geprüft werden soll oder auf Anforderung. Automatisch verlangt eine hinterlegte Referenzausgabe je Rezept, die das Repository nicht hat.
- Wie ein Persona-Review mit den aus `AUDIENCES.md` abgeleiteten Dokumentationsspuren zusammenspielt. Ein `casual-owner`-Blocker an einem Bericht ist vermutlich auch ein `user-docs`-Befund, und es gibt keine Konvention, das einmal zu sagen.
- Ob die `agronomy`-Perspektive die MCP-Kataloge lesen dürfen soll — das erlaubte, eine Empfehlung gegen die tatsächlichen Schädlings- und Artdatensätze zu prüfen statt nur gegen den Rezepttext. Es machte das Review aber von einer laufenden Umgebung abhängig, was die übrigen nicht sind.
- Ob ein `fail` einer Persona etwas blockieren soll oder rein informativ bleibt. Heute konsumiert nichts die Schlusszeile.

## Quelle

- Persona-Profile, Belegregel und Schweregradstruktur übernommen aus `nolte/kamerplanter`, `.claude/agents/`: `agrobiology-requirements-reviewer.md` (Drei-Quellen-Regel, akzeptierte und abgelehnte Quellentypen, Abschnitt für offene Recherchepunkte, CEA- und Physiologie-Hintergrund), `cannabis-indoor-grower-reviewer.md`, `casual-houseplant-user-reviewer.md` und `outdoor-garden-planner-reviewer.md` (Profile, Denkmuster und Go/No-Go-Aussage). Jene Agents prüfen die Anforderungsdokumente jenes Repositories und schreiben in dessen `spec/analysis/`; diese Spezifikation regelt dieselben Perspektiven, angewandt auf die Rezepte und Berichte dieses Repositories, mit Ablage unter `.audits/`.
- Abgrenzung der Audiences: `AUDIENCES.md` in diesem Repository sowie `spec/project/audience-identification/` in `nolte/nolte-shared` dazu, wozu jenes Artefakt dient
- Rezeptmechanik: [Das Goose-Rezeptprojekt-Muster](../../goose/recipe-project-pattern/de.md)
- Fachverfahren, an die ein Review Befunde weiterreichen kann: [Schädlingsdruck](../pest-pressure-assessment/de.md), [Speziesbaseline](../species-baseline-verification/de.md), [Nährstoff-Ungleichgewichte](../nutrient-imbalance-detection/de.md), [Pflanzengesundheits-Bildanalyse](../plant-health-image-analysis/de.md)
