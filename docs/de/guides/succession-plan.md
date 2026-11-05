---
title: Folgesaatplan
audience: [plant-owner, recipe-author]
content_mode: how-to
track: user-docs
last_updated: 2026-11-05
---

# Folgesaatplan

Eine Folgesaat nutzt ein Beet in einer Saison zweimal: Eine Kultur kommt heraus, die nächste hinein, oder eine Kultur wird gestaffelt gesät, damit die Ernte nicht auf einmal kommt. `succession-plan` nimmt die Kulturen, die Sie anbauen wollen, und eine Saison, berechnet ihre Pflanzdurchläufe und eine Fruchtfolge für diese Saison und schlägt vor, welche Durchläufe im selben Beet aufeinander folgen können und welche gestaffelt gesät werden können. Jede Folgesaat nennt beide Pflanzdurchläufe und die Fenster des Pflanzkalenders, auf denen sie ruht; jeder Durchlauf ohne Folgesaat wird mit dem Grund aufgeführt.

Der Plan ist ein **Dokument zur Prüfung**. Er hält nichts fest, und unter den Kamerplanter-Werkzeugen, die dieses Repository gemessen hat, ist keines, das eine Folgesaat, eine Beetzuordnung oder einen Pflanzdurchlauf festhält. Das Rezept, das eine Beetaufteilung festhalten würde, `bed-layout-plan-apply`, wird blockiert in einem aus [#46](https://github.com/nolte/kamerplanter-goose/issues/46) ausgelagerten Folge-Issue geführt und existiert noch nicht.

Dieser Lauf **liest nur**. Er ändert keinen Datensatz.

!!! note "Noch nicht an einer laufenden Instanz ausgeführt"
    Das Rezept und sein neuer Skill, `succession-planning`, wurden geschrieben, während der Kamerplanter-MCP-Server nicht erreichbar war. Werkzeugnamen und Artfelder stammen aus der [Server-Spezifikation](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/mcp/kamerplanter-mcp-server/de.md) und der [Spezifikation zur Artdaten-Prüfung](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/species-baseline-verification/de.md), am 2026-08-07 an zwei Arten gemessen. Behandeln Sie den ersten echten Lauf als die Messung.

## Bevor Sie anfangen

- **Starten Sie den Lauf aus diesem Repository-Checkout.** Das Rezept lädt neun Projekt-Skills aus `.claude/skills/` — `garden-context`, `site-analysis`, `crop-selection`, `decision-policy`, `planting-calendar`, `plant-planning`, `rotation-history-collect`, `crop-rotation-planning` und `succession-planning` —, und die Skill-Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses. Anderswo gestartet, gehen die Skills still verloren, und der Lauf liefert trotzdem eine plausible Antwort.
- **Wissen Sie, was der Katalog dem Lauf nicht sagen kann.** Die Fenster stammen über den Pflanzkalender aus den Artdatensätzen; die Familie je Beet stammt aus dem Fruchtfolgeschritt. Der Katalog hat keine Beete, keine Beetvorgeschichte, keinen Fruchtfolgeabstand und keinen Staffelabstand. Diese kommen von Ihnen, oder sie bleiben unbekannt.

## Ausführen

```sh
goose run --recipe succession-plan \
  --params tenant=my-garden \
  --params crops="lactuca-sativa,cichorium-endivia,phaseolus-vulgaris" \
  --params season=2027 \
  --params beds="bed-1:2m2,bed-2:3m2" \
  --params bed_history="bed-1:2026:none,bed-2:2026:none" \
  --params rotation_years=3 \
  --params stagger_weeks=2
```

Die Schlüssel oben sind Beispiele; verwenden Sie die Artschlüssel, die der Katalog Ihres Gartens trägt.

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `crops` | ja | — |
| `season` | ja | — |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug aus `list_tenants` |
| `beds` | nein | nur die in `bed_history` oder in einer Festlegung genannten Beete werden geplant |
| `bed_history` | nein | die Vorgeschichte eines Beets stammt nur aus dem Katalog; der Fruchtfolgeschritt meldet, was er nicht beurteilen kann, als `unknown` |
| `rotation_years` | nein | keine Kultur ist `clear`; der Fruchtfolgeschritt füllt die Felder trotzdem, bestenfalls mit Urteilen `unknown` |
| `demand_sequence` | nein | der Fruchtfolgeschritt wertet die Bedarfsreihenfolge nicht aus |
| `constraints` | nein | keine Festlegung und kein Ausschluss |
| `stagger_weeks` | nein | eine Staffelung wird als möglich gemeldet, ohne gelieferten Abstand |
| `planting_method` | nein | eine Kultur, die für eine Wachstumsperiode unter beiden Methoden angeboten wird, erhält keine Folgesaat, bis Sie wählen |
| `goals`, `harvest_window`, `light`, `area_or_volume`, `water`, `hardiness_zone` | nein | wie im [Gartenplan](garden-plan.md) |
| `site_constraints` | nein | keine Umweltbedingung des Standorts; das ist, was der Gartenplan als seinen Parameter `constraints` nimmt |

## Die Eingaben liefern

- **Die Saison** ist ein Jahr. Die Fenster sind Monate darin. Eine Kultur, deren Ernte ins nächste Jahr reicht, zum Beispiel eine Winterkultur, oder deren Fenster einen Saatmonat nach ihrem letzten Erntemonat nennt, hat in dieser Saison keine bekannte Belegung und erhält keine Folgesaat.
- **Beete, Beetvorgeschichte, `rotation_years` und `constraints`** gehen genau wie im [Fruchtfolgeplan](crop-rotation-plan.md) an den Fruchtfolgeschritt. Eine Folgesaat wird nur zwischen Kulturen vorgeschlagen, die der Fruchtfolgeplan im selben Beet und in derselben Saison zulässt; ein Beet, das die Fruchtfolge `open` lässt, nimmt keine Folgesaat auf.
- **`stagger_weeks`** ist die Zahl der Wochen zwischen gestaffelten Aussaaten, zum Beispiel `2`. Der Lauf teilt das Saatfenster in Blöcke aufeinanderfolgender Monate und führt je Block die Saattermine ab dem ersten Tag des ersten Blockmonats alle zwei Wochen auf, solange der Termin in diesem Block liegt. Ein Durchlauf, der über die Saisongrenze reicht, erhält keine gestaffelten Termine. Kein Abstand ist eingebaut.
- **`constraints` ist hier nicht der Parameter des Gartenplans.** Er trägt `pin=` und `exclude=` für den Fruchtfolgeschritt (und `avoid=` für den Beetplan). Die Umweltbedingungen des Standorts, die der Gartenplan als `constraints` nimmt, gehören in `site_constraints`.
- **Abstände, Mengen und unverträgliche Paare** werden hier nicht verwendet; der [Beetplan](bed-layout-plan.md) nimmt sie entgegen.

## Was die Ergebnisse bedeuten

| Ergebnis | Bedeutet |
|----------|----------|
| `SEQUENTIAL <bed>/<season> <run> -> <run>` | der letzte Erntemonat des früheren Durchlaufs liegt vor dem ersten Saat- oder Umpflanzmonat des späteren, und die Fruchtfolge lässt beide Kulturen in diesem Beet zu |
| `STAGGERED <run>` mit Terminen | Aussaaten eines Durchlaufs in Ihrem Abstand innerhalb seines Saatfensters |
| `staggering possible within <months> — interval not supplied` | das Fenster erlaubt eine Staffelung, und Sie haben keinen Abstand angegeben |
| `method not chosen — set planting_method` | dieselbe Kultur und Wachstumsperiode wird unter beiden Methoden angeboten; wählen Sie eine |
| `outside rotation plan` | die Fruchtfolge lässt diese Kultur in der Saison in keinem Beet zu |
| `spans the season boundary` | die Ernte reicht ins nächste Jahr |
| `no run follows or precedes it in <slot>` | das Beet trägt andere Durchläufe, und deren Monate passen nicht zusammen |

Jede Folgesaat hat die Stufe `caller`, weil die Saison, die Sie angegeben haben, eines der Dinge ist, auf denen sie ruht.

## Was der Plan nicht tut

- **Er hält nichts fest.** Es gibt kein Werkzeug, um ihn festzuhalten.
- **Er setzt keine Durchläufe in Beete.** Er sagt, welche Durchläufe in einem Beet aufeinander folgen könnten. Der [Beetplan](bed-layout-plan.md) platziert sie und prüft, ob sie passen.
- **Er erinnert sich nicht.** Kein Staffelabstand, kein Saattermin und keine Dauer stammt aus Allgemeinwissen, und keine Folgesaat überschreitet eine Fruchtfolge.
- **Er plant nicht über mehrere Saisons.** Ein Lauf plant eine Saison.

## Das Ergebnis lesen

Der Bericht zeigt, welche Skills geladen wurden, dann eine Tabelle der Folgesaaten, dann die Durchläufe ohne Folgesaat, den Kopf des Folgesaatplans und den Anwendungsvertrag.

| Schlusszeile | Bedeutet |
|--------------|----------|
| `SUCCESSION: <s> successions, <u> unknown — <slug>` | wie viele aufeinanderfolgende und datierte gestaffelte Folgesaaten der Plan enthält und wie vielen gestaffelten Einträgen ein Abstand fehlt oder wie viele Durchläufe eine unbekannte Belegung haben |
| `APPLY: no write tool measured (the blocked follow-up split out of nolte/kamerplanter-goose#46)` | der Plan lässt sich von hier aus nicht festhalten |

## Wie weit „deterministisch“ reicht

Die Plan-Fakten sind eine Funktion dessen, was Sie liefern: die Folgesaaten mit ihren Feldern und Durchlaufkennungen, die Saattermine, die Gründe für *keine Folgesaat* und die Belegstufen. Zwei Läufe über dieselben Eingaben sollten dieselben Plan-Fakten ergeben; der Text drumherum kann abweichen. Geprüft wurde das dreimal an einem erfundenen, als Text ausgeschriebenen Beispiel — fünf Beete mit einem festgelegten und einem offenen Feld, eine Kultur unter zwei Methoden, eine Kultur mit zwei Wachstumsperioden, eine Winterkultur, einmal mit und einmal ohne Staffelabstand —, nicht an einem laufenden Garten. Alle drei Läufe ergaben in beiden Varianten dieselben Plan-Fakten, und sie stimmten mit den von Hand ermittelten Fakten überein. Das Beispiel liegt nicht in diesem Repository.

## Quellen

- [`recipes/succession-plan.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/succession-plan.yaml) — die Parameter und das Berichtsformat
- [`.claude/skills/succession-planning/SKILL.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/.claude/skills/succession-planning/SKILL.md) — die Folgesaaten und der Anwendungsvertrag
- [`spec/process/bed-layout-and-succession-planning/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/bed-layout-and-succession-planning/de.md) — der Prozess, den dieses Rezept umsetzt
