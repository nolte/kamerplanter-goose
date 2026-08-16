---
title: Persona-Review
audience: [recipe-author, maintainer]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Persona-Review

Ein Rezept kann technisch korrekt und für die Person, für die es geschrieben ist, trotzdem unbrauchbar sein — zu viel Fachjargon für jemanden mit drei Zimmerpflanzen, zu wenig Strenge für eine Pflanzenwissenschaftlerin, blind dafür, was 120 Freilandpflanzen über eine Saison tatsächlich kosten. `domain-review` liest ein Rezept, eine Spezifikation oder eine festgehaltene Laufausgabe als genau eine Anbau-Persona und berichtet, was diese Person damit anfangen würde.

Eine Persona je Lauf, mit Absicht. Dreimal bestanden und einmal durchgefallen ist das nützliche Ergebnis; die vier zu einer Note zu mitteln zerstört es.

Dieser Lauf berührt keinen Garten und ruft kein Kamerplanter- oder Home-Assistant-Werkzeug auf. Er **schreibt** aber: Sein Bericht landet unter `.audits/grower-persona-review/` in deinem Checkout. Deshalb sagt das Rezept das in seiner `description` und trägt trotzdem kein `-apply`-Suffix — dieses Suffix bezieht sich auf einen Garten, nicht auf das Dateisystem.

## Bevor du startest

- **Starte den Lauf aus diesem Repository-Checkout.** Das Rezept lädt einen Persona-Skill aus `.claude/skills/` und liest das Prüfziel aus diesem Baum; beides wird relativ zum Arbeitsverzeichnis des Goose-Prozesses aufgelöst.
- `.audits/` ist gitignored. Der Bericht ist ein Arbeitsartefakt, nichts zum Einchecken.

## Ausführen

```sh
goose run --recipe domain-review \
  --params persona=casual-owner \
  --params target=recipes/nutrient-imbalance-check.yaml
```

| Parameter | Pflicht | Wert |
|-----------|:-------:|------|
| `persona` | ja | eines von `agronomy`, `indoor-grower`, `casual-owner`, `outdoor-gardener` |
| `target` | ja | ein repository-relativer Pfad — ein Rezept unter `recipes/`, eine Spezifikation unter `spec/` oder eine festgehaltene Laufausgabe |

Eine unbekannte Persona wird nicht auf die nächstliegende abgebildet. Der Lauf stoppt mit `REVIEW: fail — unknown persona "<Wert>"` und sonst nichts.

## Die vier Perspektiven

| Persona | Prüft als | Fragt |
|---------|-----------|-------|
| `agronomy` | Pflanzenwissenschaftlerin | Ist die Aussage biologisch korrekt und der Rat sicher |
| `indoor-grower` | Zeltbetreiber | Übersteht das den täglichen Gebrauch, Lauf für Lauf |
| `casual-owner` | Jemand mit drei Zimmerpflanzen und wenig Geduld | Weiß ich jetzt, was zu tun ist — und nutze ich das in zwei Tagen noch |
| `outdoor-gardener` | Beetgärtnerin | Trägt das über Jahreszeiten und 120 Pflanzen |

Sie sollen sich uneinig sein. Ein `fail` ist eine Aussage über eine Perspektive, kein Urteil über das Ziel.

## Das Ergebnis lesen

Jede Perspektive ordnet ihre Befunde nach Konsequenz ein, mit denselben fünf Rängen, und benennt diese Konsequenz. Ein Befund, der nur eine Vorliebe benennt, ist keiner.

| Rang | Bedeutung |
|------|-----------|
| **Blocker** | Die lesende Person verliert eine Pflanze oder gibt das Ziel auf |
| **Frustrating** | Es funktioniert und kostet jedes einzelne Mal etwas |
| **Overwhelming** | Korrekt und an seiner Leserschaft vorbei angesetzt |
| **Solved well** | Benannt, damit es niemand später entfernt |
| **Wish** | Wäre hilfreich; sein Fehlen ist kein Mangel |

Der geschriebene Bericht landet unter `.audits/grower-persona-review/<target>-<persona>.md`. Sein Abschnitt **open research points** ist verpflichtend und darf leer sein, aber nie fehlen: Jede Tatsachenaussage über eine Pflanze braucht drei unabhängige Quellen, und eine ohne diese Quellen landet dort statt in den Befunden. Die Reaktion der Persona selbst braucht keine Quelle — „ich wüsste nicht, was dieses Wort bedeutet“ *ist* der Beleg.

Der Lauf selbst druckt eine kurze Feldtabelle (Persona, Ziel, ob der Skill geladen wurde, der Berichtspfad, Zahl der Blocker, Zahl der offenen Rechercheposten), den schwerwiegendsten Blocker in einem Satz und eine Schlusszeile:

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `REVIEW: pass` | kein Blocker aus dieser Perspektive |
| `REVIEW: fail — <Blocker>` | eine Perspektive würde hier aufhören, und warum |
| `REVIEW: fail — target not found: <Pfad>` | der Pfad existiert nicht; nichts wurde geprüft |

Lädt der Persona-Skill nicht, stoppt der Lauf und sagt es, statt trotzdem zu prüfen. Ein Review, das allein aus dem Rezept-Prompt geschrieben wäre, läse sich plausibel und trüge nichts von der Persona — genau der eine Fehlschlag, der nicht wie einer aussähe.

## Quellen

- [`recipes/domain-review.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/domain-review.yaml) — die Parameter, die Persona-Zuordnung und die Schreibgrenze
- [`spec/process/grower-persona-review/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/process/grower-persona-review/de.md) — warum die Personas getrennt bleiben und was ein Review seiner Leserschaft schuldet
