---
title: Anleitungen
audience: [plant-owner, self-hoster, queue-operator, recipe-author]
content_mode: meta
track: user-docs
last_updated: 2026-08-16
---

# Anleitungen

Aufgabenorientierte Anleitungen: eine Seite je mitgeliefertem Rezept, mit dem Befehl, den es nimmt, dem, worauf seine Antwort steht, und der Bedeutung seiner Schlusszeile. Die Rezepte nebeneinander stehen in der [Referenz](../references/index.md).

## Vor einem echten Lauf

- [Verbindungsprüfung](connectivity-check.md) — nachweisen, dass beide MCP-Server erreichbar sind, sich authentifizieren und antworten — und lesen, was ein Fehlschlag bedeutet

## Fragen an einen Garten

- [Gartenkontext-Prüfung](garden-context-check.md) — was über einen Garten bekannt ist und was fehlt, Feld für Feld, mit Grund
- [Kulturwahl](crop-selection.md) — welche Kandidaten ein Standort trägt, welche er ausschließt und warum, und was nicht gut genug bekannt ist, um zu entscheiden
- [Pflanzkalender](planting-calendar.md) — wann jede gewählte Kultur an diesem Garten gesät, vorgezogen, umgepflanzt und geerntet werden kann, und welche Regel jedes Fenster ergab
- [Gartenplan](garden-plan.md) — Vorschläge für Pflanzdurchläufe zu gewählten Kulturen, zur Prüfung, bevor etwas angewendet wird
- [Saisonplan](season-plan.md) — der Plan auf zwölf Monate gelegt, mit den Folgesaaten, die er nennt
- [Pflanzenstammdaten-Prüfung](plant-master-data-check.md) — welchen Pflanzen die Stammdaten fehlen, die eine spätere Analyse braucht, und was jede Lücke verhindert
- [Nährstoffbilanz-Prüfung](nutrient-imbalance-check.md) — unter- oder überversorgt, oder unfähig aufzunehmen, was da ist, für eine Pflanze
- [Schädlingsdruck-Prüfung](pest-pressure-check.md) — ob ein Schädlings- oder Krankheitsverdacht dem Datenbestand standhält
- [Artdaten-Prüfung](species-baseline-check.md) — ob der Artdatensatz, auf dem eine Pflanze steht, plausibel ist, und wie sein Lebenszyklus aussieht
- [Tagebuch-Analyse-Queue](diary-analysis-queue.md) — einen wartenden Tagebucheintrag analysieren, die Warteschlange abarbeiten oder beides nach Zeitplan laufen lassen

## Arbeit an diesem Repository

- [Persona-Review](domain-review.md) — ein Rezept oder eine Spezifikation als eine Anbau-Persona lesen und berichten, was diese Person damit anfängt
- [Provider-Werkzeuge prüfen](provider-surface-check.md) — die Werkzeuge inventarisieren, die ein Lauf unter dem aktuellen Provider tatsächlich hält
- [Provider-Plugins prüfen](provider-plugin-check.md) — ob Plugin-Skills, Plugin-Agents und Projekt-Agents aus einem Lauf erreichbar sind
