---
title: Beetplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Beetplan

Eine Beetaufteilung sagt, welche Kultur in einer Saison in welchem Beet oder Gefäß steht und ob sie hineinpasst. `bed-layout-plan` nimmt die Kulturen, die Sie anbauen wollen, eine Saison, Ihre Beete und Gefäße mit ihrer Fläche oder ihrem Volumen und, wenn Sie sie angeben, den Abstand und die Zahl der Pflanzen je Kultur. Es berechnet die Pflanzdurchläufe, eine Fruchtfolge und die Folgesaaten für diese Saison, setzt dann jeden Durchlauf in ein Beet, in dem die Fruchtfolge ihn zulässt, und prüft die Kapazität jedes Beets Monat für Monat. Jede Platzierung sagt, warum sie dorthin ging und in welche Beete nicht; jeder ausgelassene Durchlauf wird mit dem Grund aufgeführt.

Die Beetaufteilung ist ein **Dokument zur Prüfung**. Sie hält nichts fest, und unter den Kamerplanter-Werkzeugen, die dieses Repository gemessen hat, ist keines, das ein Beet anlegt, eine Beetzuordnung oder eine Beetaufteilung festhält oder einen Pflanzdurchlauf anlegt. Das Rezept, das eine Beetaufteilung festhalten würde, `bed-layout-plan-apply`, wird blockiert in einem aus [#46](https://github.com/nolte/kamerplanter-goose/issues/46) ausgelagerten Folge-Issue geführt und existiert noch nicht.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und seine drei neuen Skills, `companion-spacing-collect`, `succession-planning` und `bed-layout-planning`, wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Was ein Nachbar-`score` bedeutet und was die Saatdichte zählt, ist nicht gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt elf Projekt-Skills aus `.claude/skills/` — die neun des [Folgesaatplans](succession-plan.md) und dazu `companion-spacing-collect` und `bed-layout-planning` —, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Wissen Sie, was der Katalog dem Lauf nicht sagen kann.** Der Katalog hat keine Beete, keine Fläche und kein Volumen, keine Abstände, kein Licht, keinen Zugang und keine Bewässerung und keine Liste schlechter Nachbarn. Er hat eine Liste verträglicher Nachbarn mit einem Wert und eine Saatdichte, deren Einheit nicht festgehalten ist. Alles andere kommt von Ihnen, oder es bleibt unbekannt.

## Ausführen

```sh
goose run --recipe bed-layout-plan \
  --params tenant=my-garden \
  --params crops="lactuca-sativa,cichorium-endivia,phaseolus-vulgaris,pisum-sativum" \
  --params season=2027 \
  --params beds="bed-1:2m2,bed-2:3m2,tub-1:20l" \
  --params bed_history="bed-1:2026:none,bed-2:2026:none,tub-1:2026:none" \
  --params rotation_years=3 \
  --params spacing="lactuca-sativa=10/m2,pisum-sativum=2l" \
  --params quantities="lactuca-sativa=12,pisum-sativum=6" \
  --params constraints="avoid=phaseolus-vulgaris+pisum-sativum"
```

Die Schlüssel oben sind Beispiele; verwenden Sie die Artschlüssel, die der Katalog Ihres Gartens trägt.

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `crops` | ja | — |
| `season` | ja | — |
| `beds` | nein | nur die in `bed_history` oder in einer Festlegung genannten Beete werden geplant, und ihre Kapazität ist unbekannt |
| `spacing` | nein | kein Bedarf wird berechnet, und jede Kapazität ist `not validated` |
| `quantities` | nein | kein Bedarf wird berechnet, und jede Kapazität ist `not validated` |
| `bed_attributes` | nein | die Beetaufteilung meldet Licht, Zugang und Bewässerung als nicht geliefert |
| `constraints` | nein | keine Festlegung, kein Ausschluss und kein gemiedenes Paar |
| `bed_history`, `rotation_years`, `demand_sequence` | nein | wie im [Fruchtfolgeplan](crop-rotation-plan.md) |
| `stagger_weeks` | nein | wie im [Folgesaatplan](succession-plan.md) |
| `tenant`, `planting_method` und die Standortparameter | nein | wie im [Gartenplan](garden-plan.md) |

## Beete, Abstände, Mengen und Bedingungen liefern

- **Beete** werden durch Kommas getrennt: `bed-1:2m2` ist ein Beet von 2 m², `tub-1:20l` ein Gefäß von 20 Litern und ein bloßes `bed-3` ein Beet unbekannter Größe. Jeder andere Text nach dem Doppelpunkt wird wie geschrieben gemeldet, mit unbekannter Kapazität.
- **Abstände** sind Pflanzen je Quadratmeter für ein Beet, `lactuca-sativa=10/m2`, oder Liter je Pflanze für ein Gefäß, `pisum-sativum=2l`. Ein Sorteneintrag, `species:cultivar=…`, geht dem Arteintrag vor. Ein Beet braucht einen Abstand in `/m2` und ein Gefäß einen in `l`; passen sie nicht, bleibt die Kapazität ungeprüft.
- **Mengen** sind Pflanzen je Pflanzdurchlauf, `lactuca-sativa=12`. Eine Kultur mit zwei Wachstumsperioden hat zwei Durchläufe, und jeder braucht die Menge.
- **`avoid`** in `constraints` hält zwei Kulturen in überlappenden Monaten aus einem Beet heraus: `avoid=phaseolus-vulgaris+pisum-sativum`. Paare werden durch Semikolons getrennt. Ein Paar, das Sie nicht nennen, wird nie als unverträglich behandelt.
- **`exclude=bed:crop`** hält eine Kultur aus einem Beet heraus. Verwenden Sie es, wenn Licht, Zugang oder Bewässerung eines Beets eine Kultur ausschließen; die Merkmale selbst entscheiden nichts.
- **`bed_attributes`** werden durch Semikolons getrennt, `bed-1:light=full sun;tub-1:irrigation=drip`. Sie erscheinen je Beet und in der Begründung jeder Platzierung, als Kontext.

## Was „not validated“ bedeutet

Die Kapazität eines Beets wird Monat für Monat geprüft: Alles, was in diesem Monat im Beet steht, muss in seine Fläche oder sein Volumen passen. Ein Monat ist `within`, wenn es passt, und `over by <x>`, wenn eine festgelegte Kultur ihn überfüllt; eine nicht festgelegte Kultur kommt nie in ein Beet, das sie überfüllen würde. Er ist `not validated`, wenn eine Zahl fehlt, die die Prüfung braucht: die Größe des Beets, der Abstand oder die Menge einer Kultur oder die Monate, in denen eine Kultur dort steht. Die fehlende Eingabe wird genannt. Der Lauf ergänzt sie nie, weder aus der Saatdichte des Katalogs noch aus Allgemeinwissen; eine Beetaufteilung ohne Abstände und Mengen ist ganz `not validated`, und das ist das ehrliche Ergebnis.

## Nachbarn sind eine Eingabe, keine Garantie

Der Katalog führt für manche Arten verträgliche Nachbarn auf, jeden mit einem Wert. Die Beetaufteilung nutzt sie nur, um zwischen Beeten zu wählen, die sonst gleich sind: Sie addiert die numerischen Werte mit den Kulturen, die in denselben Monaten schon in jedem Beet stehen, und bevorzugt die höhere Summe. Ein Wert, der keine Zahl ist, zählt 0 und wird als `score not comparable` gekennzeichnet; ein Paar, das der Katalog nicht aufführt, ist `unknown`. Was ein Wert bedeutet, ist nicht festgehalten, daher sagt jede Platzierung, dass eine Nachbarschaft eine Planungseingabe aus dem Katalog ist und keine Garantie für irgendein Ergebnis.

## Was der Plan nicht tut

- **Er hält nichts fest.** Es gibt kein Werkzeug, um ihn festzuhalten.
- **Er zeichnet nicht.** Er verteilt Fläche oder Volumen je Beet; Reihen, Positionen und Koordinaten werden nicht geplant.
- **Er wendet Licht, Zugang und Bewässerung nicht als Regeln an.** Kein Artfeld hält fest, was eine Kultur braucht, daher meldet der Lauf Ihre Merkmale und überlässt die Regel `exclude`.
- **Er leitet die Fruchtfolge nicht neu ab.** Eine Kultur steht nur in einem Beet, in dem der Fruchtfolgeplan sie zulässt; eine Kultur außerhalb des Fruchtfolgeplans wird als solche aufgeführt.
- **Er erinnert sich nicht.** Kein Abstand, keine Dichte, keine Unverträglichkeit und keine Nachbarwirkung stammt aus Allgemeinwissen.

## Das Ergebnis lesen

Der Bericht zeigt, welche Skills geladen wurden, dann eine Tabelle der Beete und Platzierungen, dann die Kapazität je Beet und Monat, die Konflikte, die nicht platzierten Durchläufe, den Kopf der Beetaufteilung mit der Begründung jeder Platzierung und den Anwendungsvertrag.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `LAYOUT: <p> placements, <o> over capacity, <n> not validated — <slug>` | wie viele Durchläufe platziert wurden und wie viele Einträge je Beet und Monat über der Kapazität liegen oder ungeprüft sind |
| `APPLY: no write tool measured (the blocked follow-up split out of nolte/kamerplanter-goose#46)` | die Beetaufteilung lässt sich von hier aus nicht festhalten |

Eine Festlegung steht immer dort, wo Sie sie festgelegt haben. Wenn sie ihr Beet überfüllt oder ein `avoid` oder `exclude` bricht, steht das unter den Konflikten und wird nie verborgen.

## Wie weit „deterministisch“ reicht

Die Plan-Fakten sind eine Funktion dessen, was Sie liefern: die Platzierungen, die Bedarfe, die Kapazität je Beet und Monat, die Konflikte, die Gründe für *nicht platziert* und die Belegstufen. Zwei Läufe über dieselben Eingaben sollten dieselben Plan-Fakten ergeben; der Text drumherum kann abweichen. Geprüft wurde das dreimal an einem erfundenen, als Text ausgeschriebenen Beispiel — ein Beet in m² mit Abständen und Mengen, ein Beet ohne Größe, ein leeres offenes Beet, ein Gefäß in Litern, eine festgelegte Kultur über der Kapazität, ein gemiedenes Paar, eine Kultur unter zwei Methoden, eine Kultur mit zwei Wachstumsperioden, eine Winterkultur und ein Nachbarwert, der keine Zahl ist —, nicht an einem laufenden Garten. Alle drei Läufe ergaben dieselben Platzierungen, Bedarfe, Kapazitäten, Konflikte und Gründe, und sie stimmten mit den von Hand ermittelten Fakten überein. Das Beispiel liegt nicht in diesem Repository.

## Quellen

- [`recipes/bed-layout-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/bed-layout-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/bed-layout-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/bed-layout-planning/SKILL.md) — die Platzierung, die Kapazitätsprüfung und der Anwendungsvertrag
- [`.claude/skills/companion-spacing-collect/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/companion-spacing-collect/SKILL.md) — was aus dem Katalog gelesen wird
- [`.claude/skills/succession-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/succession-planning/SKILL.md) — die Folgesaaten, die die Beetaufteilung in einem Beet hält
- [`spec/process/bed-layout-and-succession-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/bed-layout-and-succession-planning/de.md) — der Prozess, den dieses Rezept umsetzt
