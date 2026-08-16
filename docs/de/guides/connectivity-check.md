---
title: Verbindungsprüfung
audience: [self-hoster, plant-owner]
content_mode: how-to
track: developer-docs
last_updated: 2026-08-16
---

# Verbindungsprüfung

Bevor eine Antwort über eine Pflanze etwas wert ist, müssen beide MCP-Server erreichbar sein, sich authentifizieren lassen und tatsächlich Tool-Aufrufe beantworten. `connectivity-check` weist das in vier nur lesenden Schritten nach und druckt eine Zeile je Schritt — so wird eine vertippte Adresse oder ein abgelaufener Key genau als das benannt, statt später als Rezept aufzutauchen, das deine Pflanzen für gesund zu halten scheint.

Führe es in jeder neuen Umgebung zuerst aus, und erneut, nachdem du eine URL geändert, einen Key rotiert oder einen der Server aktualisiert hast.

Dieser Lauf **liest nur**. Er ruft kein Werkzeug auf, das Zustand ändert, und druckt nie einen Key oder ein Token, auch nicht teilweise.

## Bevor du startest

- **Die Umgebung muss Endpunkte und Zugangsdaten liefern**: `KAMERPLANTER_URL`, `KAMERPLANTER_API_KEY`, `HA_URL`, `HA_MCP_TOKEN` und `GOOSE_ADDITIONAL_CONFIG_FILES`, das auf eine `extensions.yaml` zeigt. Schreib dafür deine eigene `.envrc` — die hier eingecheckte enthält die Adressen und Passwortmanager-Pfade des Maintainers, und auf deiner Maschine schlagen diese Lookups stillschweigend fehl.
- **Dieses Rezept lädt keinen Projekt-Skill** und läuft daher aus jedem Arbeitsverzeichnis — auch über `GOOSE_RECIPE_GITHUB_REPO` ohne Clone. Es braucht trotzdem `extensions.yaml`: Ein Rezept ohne angebundene Server hat nichts zu prüfen.

## Ausführen

```sh
goose run --recipe connectivity-check --params tenant=my-garden
```

| Parameter | Pflicht | Wirkung, wenn weggelassen |
|-----------|:-------:|---------------------------|
| `tenant` | nein | die Prüfung ermittelt den Garten-Slug über `list_tenants` und nimmt den ersten |

## Was geprüft wird

| # | Schritt | Server | Aufruf |
|---|---------|--------|--------|
| 1 | Erreichbarkeit | Kamerplanter | `list_tenants` — hält fest, welche Garten-Slugs und Rollen der Key trägt |
| 2 | Nutzlast | Kamerplanter | `get_due_care_tasks` für den ermittelten Garten, gezählt je Dringlichkeitsgruppe |
| 3 | Erreichbarkeit | Home Assistant | listet die Werkzeuge, die deine Instanz anbietet, namentlich auf |
| 4 | Nutzlast | Home Assistant | ein nur lesendes Werkzeug — `GetLiveContext`, sonst `GetDateTime` oder `todo_get_items` |

Der Werkzeugkatalog von Home Assistant wird je Instanz zusammengestellt. Schritt 3 berichtet deshalb, was deine Instanz tatsächlich anbietet, statt gegen eine feste Liste zu prüfen. Schritt 4 wählt dann nur aus diesen drei als lesend klassifizierten Werkzeugen; ein Werkzeug, das bloß harmlos aussieht, wird nicht aufgerufen. Zwei sind aus genau diesem Grund namentlich verboten: `TimeTillErnte` und `time_till` sagen in ihrer Beschreibung nicht, ob sie handeln — ein nur lesender Lauf lässt sie deshalb in Ruhe.

Ein fehlgeschlagener Schritt beendet den Lauf nicht. Jeder wird festgehalten, und der nächste läuft trotzdem — ein einziger Bericht sagt dir also, ob ein Server ausgefallen ist oder beide.

## Das Ergebnis lesen

Der Lauf druckt eine Zeile je Schritt mit einem Result von genau `PASS`, `FAIL` oder `SKIP` und einer Detail-Zeile, die entweder die beobachtete Antwort oder die wörtliche Fehlermeldung trägt. Er schließt mit einer einzelnen Verdikt-Zeile.

| Schlusszeile | Bedeutung |
|--------------|-----------|
| `VERDICT: PASS` | alle vier Schritte bestanden |
| `VERDICT: FAIL` | mindestens einer nicht, gefolgt von einem Satz, der den schuldigen Server und die wahrscheinlichste Ursache benennt |

`SKIP` ist kein Bestehen. Es heißt, dass ein Schritt nichts hatte, womit er arbeiten konnte: kein Garten aus Schritt 1, oder keines der drei lesenden Werkzeuge in Schritt 3.

## Was ein Fehlschlag dir sagt

| Beobachtung | Ursache |
|-------------|---------|
| `404` von Kamerplanter | sein MCP-Server ist nicht aktiviert — `MCP_SERVER_ENABLED=true` |
| `401` von Kamerplanter | der API-Key ist ungültig oder widerrufen |
| `401` von Home Assistant | das Long-Lived Access Token stimmt nicht |
| ein Server fehlt im Lauf vollständig | die Variable unter den `env_keys` dieser Extension ist nicht gesetzt, und Goose entfernt die Extension ohne Warnung |
| `401`, obwohl die Zugangsdaten stimmen | die Variable steht nicht unter den `env_keys` dieser Extension, also ging das wörtliche `${KAMERPLANTER_API_KEY}` über die Leitung und der Server wies es als falschen Key ab |

Die letzten beiden sind die teuren, weil keiner von beiden nach einem Konfigurationsproblem aussieht. Beide sind Eigenschaften der `extensions.yaml`, nicht deines Servers.

## Quellen

- [`recipes/connectivity-check.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/recipes/connectivity-check.yaml) — die vier Schritte, die verbotenen Werkzeuge und das Berichtsformat
- [`extensions.yaml`](https://github.com/nolte/kamerplanter-goose/blob/develop/extensions.yaml) — die Endpunkte und `env_keys`, die sich alle Rezepte hier teilen
- [`spec/goose/recipe-project-pattern/de.md`](https://github.com/nolte/kamerplanter-goose/blob/develop/spec/goose/recipe-project-pattern/de.md) — warum eine nicht gesetzte `env_keys`-Variable eine Extension stillschweigend entfernt
