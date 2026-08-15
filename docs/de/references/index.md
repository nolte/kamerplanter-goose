---
title: Referenzen
audience: [recipe-author, self-hoster, maintainer]
content_mode: meta
track: developer-docs
last_updated: 2026-08-07
---

# Referenzen

Nachschlagematerial: die mitgelieferten Rezepte mit ihren Parametern, die gemeinsamen MCP-Extension-Definitionen, die Projekt-Skills und die Umgebungsvariablen, die jeder Lauf konsumiert.

## Rezepte

Jedes Rezept außer den drei Diagnosen lädt Projekt-Skills und muss deshalb mit diesem Repository-Checkout als Arbeitsverzeichnis gestartet werden.

| Rezept | Schreibt | Zweck |
|--------|:--------:|-------|
| `connectivity-check` | nein | Prüft beide MCP-Server nur lesend und druckt PASS/FAIL je Schritt |
| `provider-surface-check` | nein | Inventarisiert die Werkzeuge, die der Agent unter dem aktuellen Provider tatsächlich hält |
| `provider-plugin-check` | nein | Ob Plugin-Skills, Plugin-Agents und Projekt-Agents aus einem Lauf erreichbar sind |
| `nutrient-imbalance-check` | nein | Unter-, Überversorgung oder Nichtverfügbarkeit bei ausreichender Versorgung, für eine Pflanze |
| `pest-pressure-check` | nein | Ob ein Schädlings- oder Krankheitsverdacht biologisch tragfähig ist |
| `species-baseline-check` | nein | Ob ein Artdatensatz plausibel ist und wie sein Lebenszyklus aussieht |
| `plant-master-data-check` | nein | Welchen Pflanzen die Stammdaten fehlen, die eine spätere Analyse braucht |
| `domain-review` | nur nach `.audits/` | Prüft ein Rezept oder eine Spezifikation aus Sicht einer Anbau-Persona |
| `diary-photo-analysis-apply` | **ja** | Analysiert einen wartenden Tagebucheintrag und übermittelt das Ergebnis |
| `diary-analysis-queue-apply` | **ja** | Arbeitet die Analyse-Warteschlange Eintrag für Eintrag ab |

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

**Prüfperspektiven** — lesen dieses Checkout, nie einen Garten. Eine je Lauf; sie sollen sich uneinig sein:

| Skill | Prüft als |
|-------|-----------|
| `agronomy-review` | Pflanzenwissenschaftlerin, auf biologische Korrektheit |
| `indoor-grower-review` | Zeltbetreiber, auf Alltagstauglichkeit |
| `casual-owner-review` | Jemand mit drei Zimmerpflanzen und wenig Geduld |
| `outdoor-gardener-review` | Beetgärtnerin, über Jahreszeiten und 120 Pflanzen hinweg |

## Agents

`.claude/agents/` enthält ausschließlich Messsonden, keine Arbeitsartefakte. Ein Projekt-Agent ist aus genau diesem Verzeichnis dispatchbar und aus keinem anderen — nicht aus `.agents/agents/`, das Gooses eigene Dokumentation empfiehlt, und nicht aus einem Plugin. Siehe die [Spezifikation des Rezeptprojekt-Musters](https://github.com/nolte/kamerplanter-goose/blob/main/spec/goose/recipe-project-pattern/de.md).
