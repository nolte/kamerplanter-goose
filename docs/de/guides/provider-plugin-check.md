---
title: Provider-Plugins prüfen
audience: [maintainer, recipe-author]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Provider-Plugins prüfen

Das Gegenstück [Provider-Werkzeuge prüfen](provider-surface-check.md) fragt, welche Werkzeuge existieren. Dieses hier stellt die engere Frage: Wenn ein Lauf `Skill` und `Agent` hält — ist die Registry dahinter überhaupt befüllt, und welche Auffindungsschicht antwortet, Gooses oder die des Providers? Die beiden sind sich uneinig darüber, wo eine Datei hingehört, und wer der falschen folgt, legt einen Skill oder einen Agent dorthin, wo der Lauf ihn nicht sieht — ohne dass ein Fehler das anzeigt.

Führ es nach einem Goose-Upgrade aus, nach einem Providerwechsel, oder nachdem du ein Plugin installiert hast, dessen Skills ein Rezept nutzen soll.

Der Lauf liest nur: Er schreibt keine Datei und ruft kein MCP-Werkzeug auf. Die zwei Agents, die er dispatcht, sind Sonden, die mit einem einzigen Wort antworten und nichts prüfen.

## Bevor du startest

**Starte den Lauf aus diesem Repository-Checkout.** Die Schritte 5 bis 7 dispatchen Sonden-Agents, die in diesem Baum unter `.claude/agents/` und `.agents/agents/` definiert sind. Anderswo gestartet meldet das Rezept beide als unerreichbar — das ist eine falsche Messung, kein fehlgeschlagener Lauf, und für eine der beiden sieht es genau wie das echte Ergebnis aus.

## Ausführen

```sh
goose run --recipe provider-plugin-check
```

Es nimmt keine Parameter.

## Was gemessen wird

| # | Sonde | Frage |
|---|-------|-------|
| 1 | Skill-Registry | welche Skill-Namen sind auflistbar, und trägt einer ein Plugin-Präfix |
| 2 | Plugin-Skill laden | lädt `Skill(frontend-design:frontend-design)` tatsächlich |
| 3 | Agent-Typ-Registry | welche Agent-Typen sind auflistbar |
| 4 | Plugin-Agent dispatchen | lässt sich `nolte-shared:project-structure-reviewer` dispatchen |
| 5 | Projekt-Agent-Registry | steht `probe-agent-reachable` aus `.claude/agents/` unter den Typen |
| 6 | Ihn dispatchen | antwortet dieser projektlokale Agent |
| 7 | Seinen Zwilling dispatchen | antwortet der identische Agent in `.agents/agents/` |

Die Schritte 5 und 6 sind absichtlich getrennt: Eine Registry, die einen Typ nicht anzeigt, und eine, die ihn ablehnt, sind unterschiedliche Ergebnisse — Schritt 6 versucht den Aufruf deshalb auch dann, wenn Schritt 5 den Namen nicht gelistet hat.

## Das Ergebnis lesen

Eine Zeile je Sonde, mit einem Result von genau `AVAILABLE`, `UNAVAILABLE` oder `ERROR` und einer Zeile Beleg — die beobachteten Namen, der zurückgegebene Text oder die wörtliche Fehlermeldung. Dann vier Schlusszeilen:

```
PLUGIN SKILLS: <available or unavailable>
PLUGIN AGENTS: <available or unavailable>
PROJECT AGENTS (.claude/agents): <available or unavailable>
PROJECT AGENTS (.agents/agents): <available or unavailable>
```

## Was hier gemessen wurde

Gegen Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`, der zuletzt erfasste Lauf:

| Fähigkeit | Ergebnis | Beleg |
|-----------|----------|-------|
| Plugin-Skill laden | funktioniert | `Skill(frontend-design:frontend-design)` wurde aus dem Plugin-Cache geladen |
| Plugin-Agent dispatchen | schlägt fehl | `Agent type '…' not found.` gegen eine Liste der Provider-eigenen Built-ins |
| Agent aus `.claude/agents/` dispatchen | funktioniert | die Sonde antwortete `reachable` |
| Zwilling aus `.agents/agents/` dispatchen | schlägt fehl | `Agent type 'probe-agents-dir' not found.` im selben Lauf |

Drei Ergebnisse in einem Lauf klären, welche Schicht antwortet: Die Registry listet Claude Codes eigene Built-ins, der Dispatch läuft über das `Agent`-Werkzeug des Providers, und gelesen wird nur `.claude/`. **Das ist die Agent-Schicht des Providers, nicht die von Goose** — das genaue Gegenstück zu dem, was mit Skills passiert, wo der `.claude/skills/`-Leser des Providers überlebt und Gooses `load_skill` nicht.

Die Falle: Gooses eigene Dokumentation nennt `.agents/agents/` als Ort für neue Projekt-Agents — und genau dieses Verzeichnis sieht dieser Provider nicht. Reproduziert dein Lauf die Tabelle oben, hat sich nichts geändert. Tut er es nicht, sind die Aussagen in `spec/goose/recipe-project-pattern/` zu aktualisieren — genau dafür gibt es das Rezept.

## Quellen

- [`recipes/provider-plugin-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/provider-plugin-check.yaml) — die sieben Sonden und warum es zwei Sonden-Agents gibt
- [`spec/goose/recipe-project-pattern/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/de.md) — die Messungen mit ihren Daten und die Verzeichnistabelle, die sie ergaben
