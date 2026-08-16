---
title: Tagebuch-Analyse-Queue
audience: [queue-operator, self-hoster]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Tagebuch-Analyse-Queue

In Kamerplanters KI-Analyse-Warteschlange warten Tagebucheinträge mit Fotos, und ein Goose-Lauf soll sie abarbeiten — einmalig von Hand oder unbeaufsichtigt nach Zeitplan. Diese Seite nennt den Befehl für jede dieser Formen und sagt, was seine Schlusszeile bedeutet.

Diese Läufe **schreiben in deinen Garten**: Jeder beansprucht einen Eintrag, übermittelt eine Analyse zurück und gibt den Anspruch wieder frei. Lies [was die Rezepte tun](../references/index.md), bevor du eines auf einen Garten richtest, an dem dir etwas liegt.

## Bevor du startest

- **Starte jeden Lauf aus diesem Repository-Checkout.** Die Rezepte laden Projekt-Skills aus `.claude/skills/`, und die Skill-Auffindung erfolgt relativ zum Arbeitsverzeichnis des Goose-Prozesses. Ein anderswo gestarteter Lauf verliert den Skill stillschweigend und liefert trotzdem eine plausible Antwort.
- **Lade die Umgebung**: `direnv allow`. Sie liefert `KAMERPLANTER_URL`, `KAMERPLANTER_API_KEY` und `GOOSE_ADDITIONAL_CONFIG_FILES`, worüber die gemeinsame `extensions.yaml` geladen wird.
- **Der API-Key braucht die Berechtigung `mcp.write`.** Ohne sie stoppt ein Lauf, bevor er irgendetwas beansprucht, und meldet die fehlende Berechtigung.
- **Weise die Verbindung zuerst nach**: `goose run --recipe connectivity-check`. Das benennt eine falsche URL, einen widerrufenen Key oder einen deaktivierten MCP-Server, bevor ein Analyselauf es falsch darstellt.

## Einen einzelnen Eintrag analysieren

```sh
goose run --no-session --max-turns 25 -q \
  --recipe diary-photo-analysis-apply \
  --params run_id=manual-$(date +%Y%m%d-%H%M%S)
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `run_id` | ja | — er ist der Diskriminator in `worker_id` und im Idempotenzschlüssel, damit ein Wiederholungslauf nachvollziehbar bleibt und nicht doppelt schreibt |
| `entry_key` | nein | der Lauf nimmt den ältesten wartenden Eintrag aus der Warteschlange |
| `tenant` | nein | der Lauf ermittelt den Garten-Slug über `list_tenants` |

Einen Eintrag benennst du ausdrücklich mit `--params entry_key=<key>`.

Der Lauf druckt eine Tabelle je Schritt und schließt mit `SUBMITTED: completed`, `SUBMITTED: failed` oder `NOT CLAIMED: <reason>`.

## Die ganze Warteschlange abarbeiten

Es gibt zwei Formen, und sie unterscheiden sich in genau einer Eigenschaft: ob die Einträge sich einen Kontext teilen.

| | `scripts/analyse-queue.sh` | `diary-analysis-queue-apply` |
|---|---|---|
| Prozesse | ein Goose-Prozess je Eintrag | ein Prozess für die Warteschlange |
| Ein Eintrag, der abstürzt oder seinen Kontext erschöpft | erreicht den nächsten Eintrag nicht | kann den Rest des Laufs mitreißen |
| Kosten | ein Prozessstart je Eintrag | ein Prozessstart |
| Ausgabe erscheint | je Eintrag, sobald sein Lauf endet | am Ende |

Nimm das Skript für unbeaufsichtigte Läufe; nimm das Rezept, wenn du zusiehst und ein durchgehendes Transkript willst.

### Ein Prozess je Eintrag

```sh
scripts/analyse-queue.sh 3 my-garden
```

Beide Argumente sind optional und positionsgebunden: `scripts/analyse-queue.sh [max_entries] [tenant]`. `max_entries` ist standardmäßig `3`; lässt du `tenant` weg, ermittelt jeder Lauf den Garten-Slug selbst. Das Skript filtert Einträge ohne Fotos heraus, bevor es irgendetwas startet — so beginnt kein Lauf nur, um abzulehnen.

Es endet mit `2` bei einem abgelehnten Argument, mit `1`, wenn die Warteschlange gar nicht gelesen werden konnte — dann wird nichts verarbeitet, und das sagt es auch — und sonst mit `0`, auch wenn nichts wartet.

### Ein Lauf für die ganze Warteschlange

```sh
goose run --recipe diary-analysis-queue-apply \
  --params run_id=queue-$(date +%Y%m%d-%H%M%S) \
  --params max_entries=3
```

| Parameter | Pflicht | Standard |
|-----------|:-------:|----------|
| `run_id` | ja | — |
| `tenant` | nein | wird über `list_tenants` ermittelt |
| `max_entries` | nein | `3` |
| `include_stale` | nein | `true` — nimmt auch Einträge auf, deren vorherige Lease abgelaufen ist |

Erhöhe `max_entries` bewusst. Jeder Eintrag kostet eine vollständige Analyse im selben Kontext, und ein mitten in der Warteschlange erschöpfter Kontext ist genau das, was einen Anspruch offen lässt.

## Nach Zeitplan laufen lassen

Cron gibt einem Job weder das Arbeitsverzeichnis noch die `.envrc`-Umgebung mit, und beides ist hier tragend. Setze das Verzeichnis und lass `direnv exec` die Zugangsdaten liefern:

```cron
17 * * * * cd /pfad/zu/kamerplanter-goose && direnv exec . scripts/analyse-queue.sh 3 my-garden >> /var/log/kamerplanter-queue.log 2>&1
```

Ein systemd-Timer braucht dieselben zwei Dinge: `WorkingDirectory=` in der Service-Unit und `direnv exec .` vor dem Skript.

## Das Ergebnis ohne Transkript lesen

Jede Form schließt mit Zeilen, die sich greppen lassen — ein geplanter Lauf wird beurteilt, ohne zu lesen, was das Modell gesagt hat.

| Zeile | Ausgegeben von | Bedeutung |
|-------|----------------|-----------|
| `SUBMITTED: completed` | Einzeleintrag | die Analyse wurde in den Eintrag zurückgeschrieben |
| `SUBMITTED: failed` | Einzeleintrag | der Eintrag war beansprucht, die Analyse war nicht möglich, und der Fehlschlag wurde übermittelt |
| `NOT CLAIMED: <reason>` | Einzeleintrag | nichts wurde beansprucht; der Eintrag bleibt unberührt in der Warteschlange |
| `PROCESSED: <n> ok, <n> failed, <n> not claimed` | Skript | Ergebnis je Eintrag für diesen Lauf |
| `REMAINING: <n> still pending with photos` | Skript, Rezept | der Rückstand nach diesem Lauf |
| `QUEUE TOTAL` / `PROCESSED` / `REMAINING` | Rezept | dieselben drei Zahlen aus der Schleife im Lauf |

`REMAINING` zählt, was tatsächlich abgeschlossen wurde, nicht was versucht wurde: Bei einem fehlgeschlagenen Lauf läuft die Lease ab und der Eintrag kehrt in die Warteschlange zurück, und ein `NOT CLAIMED`-Lauf hielt nie eine.

Ein Lauf, der mitten in der Analyse stirbt, hinterlässt einen Anspruch. Das ist kein Zustand, den du reparieren musst — die Lease läuft von selbst ab, und der nächste Lauf nimmt den Eintrag wieder auf, weil `include_stale` standardmäßig aktiv ist.

## Quellen

- [`recipes/diary-photo-analysis-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/diary-photo-analysis-apply.yaml) und [`recipes/diary-analysis-queue-apply.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/diary-analysis-queue-apply.yaml) — die Parameter und das Berichtsformat
- [`scripts/analyse-queue.sh`](https://github.com/nolte/kamerplanter-goose/blob/develop/scripts/analyse-queue.sh) — die Prozessschleife je Eintrag und ihre Exit-Codes
- [`spec/goose/recipe-project-pattern/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/de.md) — warum das Arbeitsverzeichnis tragend ist und warum keine der beiden Formen Gooses `sub_recipes:` nutzt
