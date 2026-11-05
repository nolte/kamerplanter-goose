---
title: Referenzen
audience: [recipe-author, self-hoster, maintainer]
content_mode: meta
track: developer-docs
last_updated: 2026-11-05
---

# Referenzen

Nachschlagematerial: die mitgelieferten Rezepte mit ihren Parametern, die gemeinsamen MCP-Extension-Definitionen, die Projekt-Skills und die Umgebungsvariablen, die jeder Lauf konsumiert.

## Rezepte

Ein Rezept, das Projekt-Skills lädt, muss mit diesem Repository-Checkout als Arbeitsverzeichnis gestartet werden, weil die Skill-Auffindung relativ zum Arbeitsverzeichnis des Goose-Prozesses erfolgt. `connectivity-check`, `provider-surface-check` und `plant-master-data-check` laden keines und laufen von überall — genau das macht sie über `GOOSE_RECIPE_GITHUB_REPO` nutzbar.

`provider-plugin-check` lädt ebenfalls keinen Skill und braucht dieses Checkout trotzdem: Seine letzten drei Sonden dispatchen Agents, die in diesem Baum definiert sind. Anderswo gestartet meldet es sie als unerreichbar — eine falsche Messung, kein fehlgeschlagener Lauf, und für eines der beiden verglichenen Verzeichnisse nicht vom echten Ergebnis zu unterscheiden.

Zu jedem Rezept gibt es eine eigene Anleitung, verlinkt über seinen Namen.

| Rezept | Schreibt | Zweck |
|--------|:--------:|-------|
| [`connectivity-check`](../guides/connectivity-check.md) | nein | Prüft beide MCP-Server nur lesend und druckt PASS/FAIL je Schritt |
| [`provider-surface-check`](../guides/provider-surface-check.md) | nein | Inventarisiert die Werkzeuge, die der Agent unter dem aktuellen Provider tatsächlich hält |
| [`provider-plugin-check`](../guides/provider-plugin-check.md) | nein | Ob Plugin-Skills, Plugin-Agents und Projekt-Agents aus einem Lauf erreichbar sind |
| [`nutrient-imbalance-check`](../guides/nutrient-imbalance-check.md) | nein | Unter-, Überversorgung oder Nichtverfügbarkeit bei ausreichender Versorgung, für eine Pflanze |
| [`pest-pressure-check`](../guides/pest-pressure-check.md) | nein | Ob ein Schädlings- oder Krankheitsverdacht biologisch tragfähig ist |
| [`daily-garden-check`](../guides/daily-garden-check.md) | nein | Was in einem Garten heute Aufmerksamkeit verdient, nach Dringlichkeit geordnet; wendet nichts an |
| [`watering-decision`](../guides/watering-decision.md) | nein | Jetzt gießen, warten oder zu wenig Beleg, für eine Pflanze; gießt nichts |
| [`watering-decision-apply`](../guides/watering-decision.md) | **ja** | Bestätigt eine Pflegeerinnerung, nach der eine Person gehandelt hat |
| [`fertilization-decision`](../guides/fertilization-decision.md) | nein | Düngen, nicht düngen oder zu wenig Beleg, für eine Pflanze; düngt nichts |
| [`fertilization-decision-apply`](../guides/fertilization-decision.md) | **ja** | Hält eine Düngung fest, die eine Person ausgeführt hat |
| [`growth-stage-check`](../guides/growth-stage-check.md) | nein | Erfasstes Stadium passend, fraglich (voraus, hinterher, unklar) oder zu wenig Beleg, für eine Pflanze; ändert keine Phase |
| [`weather-impact-check`](../guides/weather-impact-check.md) | nein | Je Wetterfaktor eine Exposition, keine oder keine Quelle, für bis zu fünf Pflanzen; steuert nichts an |
| [`plant-health-assessment`](../guides/plant-health-assessment.md) | nein | Eine Differenzialbetrachtung für eine Pflanze: führende oder konkurrierende Erklärungen, nur Vermutung, nichts Auffälliges oder zu wenig Beleg; nie eine Diagnose |
| [`pest-ipm-plan`](../guides/pest-ipm-plan.md) | nein | Vier IPM-Stufen für einen Schädlings- oder Krankheitsverdacht, eine Behandlung nur an der Schwelle und mit ihrem Sicherheitsblock; behandelt und hält nichts fest |
| [`harvest-readiness-check`](../guides/harvest-readiness-check.md) | nein | Reif, nahe der Reife, nicht reif, nicht erntbar oder zu wenig Beleg, für eine Pflanze, mit ihrer Sperre durch die Wartezeit; erntet nichts |
| [`harvest-plan`](../guides/harvest-plan.md) | nein | Die Ernten von bis zu fünf Pflanzen in einer Reihenfolge, mit Fenstern und Arbeitszählungen; plant nichts ein |
| [`garden-review`](../guides/garden-review.md) | nein | Die bisherige Geschichte eines Gartens, Pflanze für Pflanze, mit Lehren und einem Block für den nächsten Zyklus; schreibt nichts |
| [`season-review`](../guides/season-review.md) | nein | Die Geschichte einer Saison, archivierte Pflanzen eingeschlossen, übergeben an den nächsten Plan; schreibt nichts |
| [`species-baseline-check`](../guides/species-baseline-check.md) | nein | Ob ein Artdatensatz plausibel ist und wie sein Lebenszyklus aussieht |
| [`garden-context-check`](../guides/garden-context-check.md) | nein | Welche Teile des Kontexts eines Gartens bekannt sind und welche fehlen |
| [`crop-selection`](../guides/crop-selection.md) | nein | Welche Kandidaten ein Standort trägt und welche Bedingungen er verfehlt |
| [`planting-calendar`](../guides/planting-calendar.md) | nein | Wann jede gewählte Kultur an einem Garten gesät, umgepflanzt und geerntet werden kann |
| [`garden-plan`](../guides/garden-plan.md) | nein | Vorschläge für Pflanzdurchläufe zu gewählten Kulturen, zur Prüfung; wendet nichts an |
| [`season-plan`](../guides/season-plan.md) | nein | Der Plan auf zwölf Monate gelegt, mit seinen Folgesaaten |
| [`crop-rotation-plan`](../guides/crop-rotation-plan.md) | nein | Eine Pflanzenfamilie je Beet und Saison, mit Urteilen und Konflikten; hält nichts fest |
| [`succession-plan`](../guides/succession-plan.md) | nein | Aufeinanderfolgende und gestaffelte Folgesaaten je Beet für eine Saison; hält nichts fest |
| [`bed-layout-plan`](../guides/bed-layout-plan.md) | nein | Durchläufe je Beet mit Kapazität je Monat, Konflikten und nicht platzierten Durchläufen; hält nichts fest |
| [`plant-master-data-check`](../guides/plant-master-data-check.md) | nein | Welchen Pflanzen die Stammdaten fehlen, die eine spätere Analyse braucht |
| [`domain-review`](../guides/domain-review.md) | nur nach `.audits/` | Prüft ein Rezept oder eine Spezifikation aus Sicht einer Anbau-Persona |
| [`diary-photo-analysis-apply`](../guides/diary-analysis-queue.md) | **ja** | Analysiert einen wartenden Tagebucheintrag und übermittelt das Ergebnis |
| [`diary-analysis-queue-apply`](../guides/diary-analysis-queue.md) | **ja** | Arbeitet die Analyse-Warteschlange Eintrag für Eintrag ab |

## Projekt-Skills

Werden namentlich aus `.claude/skills/` geladen. Die Auffindung ist relativ zum Arbeitsverzeichnis des Goose-Prozesses.

**Gartenverfahren** — lesen den Kamerplanter-MCP-Server:

| Skill | Beantwortet |
|-------|-------------|
| `plant-context-collect` | Was für genau diese Pflanze normal ist |
| `plant-photo-read` | Was ein Tagebuchfoto zeigt, gemessen an diesem Kontext |
| `nutrient-imbalance-assess` | In welche Richtung ein Nährstoffproblem läuft |
| `pest-pressure-assess` | Ob ein Schädlingsverdacht seine Falsifikationstests übersteht |
| `species-baseline-verify` | Ob dem Artdatensatz zu trauen ist |
| `plant-lifecycle-resolve` | Einjährig, zweijährig oder mehrjährig — und die daraus folgenden Fenster |
| `diary-analysis-claim` | Das Claim-and-Submit-Protokoll der Analyse-Warteschlange |
| `garden-context` | Was über einen Garten bekannt ist und was fehlt |
| `decision-policy` | Wie weit einer Empfehlung zu trauen ist; liest keinen Garten, arbeitet auf den übergebenen Belegen |
| `site-analysis` | Was über einen Standort bekannt ist, Parameter für Parameter, und was nicht |
| `crop-selection` | Welche Kandidaten ein Standort trägt, mit Gründen und verfehlten Bedingungen |
| `planting-calendar` | Die Fenster für Aussaat, Umpflanzen und Ernte je Kultur und Wachstumsperiode, mit der Regel dahinter |
| `plant-planning` | Vorschläge für Pflanzdurchläufe mit Kennungen, Begründung und Konfidenz; ruft kein Werkzeug auf |
| `rotation-history-collect` | Familie, Bedarfsklasse und Gründüngungseignung jeder Kultur sowie Pflanzen und Inspektionen je Standort, archivierte eingeschlossen |
| `crop-rotation-planning` | Eine Familie je Beet und Saison, mit einem Urteil und seiner Regel für jede betrachtete Kultur und jedem Konflikt benannt; ruft kein Werkzeug auf |
| `companion-spacing-collect` | Die Nachbarn jeder Kultur im Katalog mit ihren Werten und ihre Saatdichte nur als Kontext |
| `succession-planning` | Welche Durchläufe in einem Beet aufeinander folgen können, und gestaffelte Aussaaten im Abstand des Aufrufers; ruft kein Werkzeug auf |
| `bed-layout-planning` | Welcher Durchlauf in welchem Beet steht, sein Bedarf und die Kapazität je Beet und Monat; ruft kein Werkzeug auf |
| `diary-measurements-read` | Die erfassten Messwerte aus dem Tagebuch einer Pflanze, mit einem Bericht, wie viel gelesen wurde |
| `care-planning` | Die Domänenergebnisse in einer nach Dringlichkeit geordneten Liste, mit dem, was keine Handlung ergibt; ruft kein Werkzeug auf |
| `watering-decision` | Jetzt gießen, warten oder unzureichender Beleg, aus dem gegenwärtigen Zustand der Pflanze; ruft kein Werkzeug auf |
| `fertilization-decision` | Düngen, nicht düngen oder unzureichender Beleg, aus der Nährstoffprüfung; ruft kein Werkzeug auf |
| `growth-stage-assessment` | Erfasstes Stadium passend, fraglich oder unzureichender Beleg, aus Beobachtungen gegen zeitliche Erwartungen; liest Phasenstatus und Phasenverlauf |
| `weather-impact-analysis` | Wetterexpositionen je Faktor, getrennt von Symptomen; liest eine Home-Assistant-Wetter-Entität nur, wo erlaubt |
| `plant-health-assessment` | Kandidaten-Erklärungen je Klasse, jede gestützt, Vermutung, widerlegt oder nicht beurteilbar, und ein Gesamtergebnis; ruft kein Werkzeug auf |
| `pest-ipm-planning` | Bestätigung, Umweltkorrektur, kulturelle Maßnahmen und gezielte Behandlung in Reihenfolge, mit Voraussetzungen und Sicherheitsauflagen je Behandlung; liest die Katalogdatensätze des Kandidaten |
| `harvest-planning` | Reif, nahe der Reife, nicht reif, nicht erntbar oder unzureichender Beleg aus einem beobachteten Reifemerkmal, eine Sperre durch die Wartezeit und eine Erntereihenfolge für bis zu fünf Pflanzen; liest die Erntereife- und Behandlungsdaten |
| `garden-review` | Verlaufsdatensätze, Leistung der Sorten, Lehren und ein Block für den nächsten Zyklus für einen Garten oder eine Saison; ruft kein Tool auf |

**Prüfperspektiven** — lesen dieses Checkout, nie einen Garten. Eine je Lauf; sie sollen sich uneinig sein:

| Skill | Prüft als |
|-------|-----------|
| `agronomy-review` | Pflanzenwissenschaftlerin, auf biologische Korrektheit |
| `indoor-grower-review` | Zeltbetreiber, auf Alltagstauglichkeit |
| `casual-owner-review` | Jemand mit drei Zimmerpflanzen und wenig Geduld |
| `outdoor-gardener-review` | Beetgärtnerin, über Jahreszeiten und 120 Pflanzen hinweg |

## Agents

`.claude/agents/` enthält ausschließlich Messsonden, keine Arbeitsartefakte. Ein Projekt-Agent ist aus genau diesem Verzeichnis dispatchbar und aus keinem anderen — nicht aus `.agents/agents/`, das Gooses eigene Dokumentation empfiehlt, und nicht aus einem Plugin. Siehe die [Spezifikation des Rezeptprojekt-Musters](https://github.com/nolte/kamerplanter-goose/blob/main/spec/goose/recipe-project-pattern/de.md).
