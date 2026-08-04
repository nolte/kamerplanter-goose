# Goose-Rezept-Projektmuster

Status: Entwurf
Portfolio-Scope: local

## Kontext

Ein Repository, das wiederverwendbare Goose-Rezepte ausliefert, stößt auf dieselben Hindernisse, unabhängig davon, was die Rezepte tun. Extension-Blöcke werden in jede Datei kopiert. Ein Zugangsdatum wird still nicht ersetzt, und der Lauf meldet einen Serverausfall. Eine Nebenbedingung im falschen Schlüssel wird bei einem Headless-Lauf ignoriert. Der Agent hält am Ende Werkzeuge, die niemand deklariert hat.

Nichts davon lässt sich durch Lesen eines Rezepts entdecken. Jede Regel unten wurde gegen **Goose 1.45.0** mit dem Provider `claude-code` gemessen — durch Mitschnitt der tatsächlich abgesetzten Requests und durch Abfragen der Werkzeugoberfläche des laufenden Agenten —, weil beobachtetes und dokumentiertes Verhalten an mehreren Stellen auseinandergehen.

Diese Spec ist die Mechanik-Ebene dieses Repositorys. Die Backend-Specs unter `spec/mcp/` beschreiben, *was ein Server anbietet*; diese hier beschreibt, *wie ein Goose-Projekt darum herum gebaut wird*, sodass dieselbe Regel nicht je Backend wiederholt wird.

Leserschaft: alle, die hier ein Rezept ergänzen, sowie alle, die ein vergleichbares Goose-Repository beginnen und die Fehlermodi vorab kennen wollen statt einzeln je Debugging-Sitzung.

## Ziele

- Ein MCP-Server wird einmal pro Repository deklariert, nicht einmal pro Rezept
- Ein falsch konfiguriertes Zugangsdatum erzeugt eine Meldung, die das Zugangsdatum benennt, keinen Fehlbericht über den Server
- Die Lese-/Schreibgrenze eines Rezepts ist am Dateinamen sichtbar und dort durchgesetzt, wo Goose tatsächlich durchsetzt
- Die Werkzeuge, die ein Agent wirklich hält, sind bekannt, bevor ihm ein Rezept anvertraut wird
- Ein neues Rezept kostet einen Prompt, kein Setup

## Nicht-Ziele

- Prompt-Gestaltung oder Ausgabeformat von Rezepten
- Welche MCP-Backends genutzt werden und was deren Tools bedeuten — das ist `spec/mcp/`
- Goose-Provider-Auswahl, Modellwahl oder Kostensteuerung
- Paketierung von Rezepten für Konsumenten außerhalb der Verteilung dieses Repositorys

## Gemessenes Verhalten

### Deklaration von Extensions und Vorrang

Extensions dürfen im `extensions:`-Block eines Rezepts oder in einer geteilten Datei stehen, die über `GOOSE_ADDITIONAL_CONFIG_FILES` geladen wird. **Beide werden nicht zusammengeführt.** Gemessen: Waren eine geteilte und eine rezeptlokale Extension gleichzeitig konfiguriert, verband sich nur die rezeptlokale; der geteilte Eintrag erzeugte überhaupt keinen Request.

Ein Rezept deklariert daher entweder jede Extension, die es braucht, oder gar keine und erbt den geteilten Satz. Ein „geteilt plus eine weitere" gibt es nicht.

Die beiden Orte nutzen unterschiedliche Formen für dieselben Daten:

| Ort | Form |
|-----|------|
| Geteilte Konfigurationsdatei | `extensions:` ist eine **Map**, nach Namen verschlüsselt, jeder Eintrag braucht `enabled: true` |
| Rezept | `extensions:` ist eine **Liste**, ohne `enabled`-Schlüssel |

### Ersetzung von Umgebungsvariablen

`${VAR}` innerhalb einer Extension wird **nur** ersetzt, wenn `VAR` in den `env_keys` dieser Extension steht. Gegen einen Mitschnitt-Server gemessen:

| Deklaration | Was Goose sendete |
|-------------|-------------------|
| `${SECRET}`, ohne `env_keys` | `${SECRET}` — die literale Zeichenkette |
| `${SECRET}` mit `env_keys: ["SECRET"]` | den Wert |
| `{{ param }}` als Rezeptparameter | den Wert |

Der Fehler ist still und irreführend: Das Rezept validiert, die Extension verbindet sich, und der Server antwortet `401`, als wären die Zugangsdaten falsch.

**Eine Extension, deren `env_keys`-Variable nicht gesetzt ist, wird vollständig übersprungen** — keine Warnung `Failed to start extension`, die Tools fehlen einfach. Beobachtet, als `pass` nicht entschlüsseln konnte: Zwei Extensions verschwanden, während eine dritte, deren Variable gesetzt war, normal lud. Der Agent diagnostizierte das als „keine MCP-Server konfiguriert", was falsch war.

`--render-recipe` klärt das nicht: Es druckt `${VAR}` in beiden Fällen unersetzt.

### Auffinden und Verteilung von Rezepten

- `GOOSE_RECIPE_PATH` akzeptiert mehrere Verzeichnisse, getrennt durch `:`
- Das Auffinden ist **flach** — `*.yaml` direkt unter jedem Verzeichnis; Unterordner werden nicht durchlaufen
- `GOOSE_RECIPE_GITHUB_REPO` nimmt `owner/repo` und holt Rezepte nach Namen
- Es holt **nur Rezepte**. Eine geteilte Extension-Datei ist nicht Teil dieser Übertragung, sodass ein so bezogenes Rezept ohne Server ankommt, sofern der Konsument die Konfiguration nicht separat bereitstellt

### Wo Nebenbedingungen durchgesetzt werden

Ein Rezept mit `instructions`, aber ohne `prompt`, lädt und validiert, scheitert dann bei einem Headless-Lauf mit `no text provided for prompt`. Nebenbedingungen, die nur in `instructions` stehen, wurden beobachtet ignoriert. Was gelten muss, gehört in `prompt`.

### Werkzeugoberfläche des Providers

Der Provider ist nicht zwingend ein nackter Modell-Endpunkt. Gemessen mit `GOOSE_PROVIDER=claude-code` meldete ein Rezept ohne jede Extension und ohne geladene geteilte Konfiguration dennoch **29 Nicht-MCP-Tools**, darunter `Bash`, `Read`, `Write`, `Edit`, `WebFetch`, `WebSearch`, `Agent`, `Workflow`, `Skill` sowie die Familien `Task*` und `Cron*`.

Ein „nur lesendes" Rezept hält unter einem solchen Provider Shell-Zugriff, Schreibzugriff auf Dateien und die Fähigkeit, Subagenten zu starten. Seine Nur-Lese-Eigenschaft ist **Prompt-Disziplin, keine technische Grenze**. MCP-Tools aus Goose-Extensions erscheinen als `mcp__<server>__<tool>`.

### Verfügbarkeit von Plugins

Unter dem Provider `claude-code` gemessen:

| Fähigkeit | Ergebnis | Beleg |
|-----------|----------|-------|
| Plugin-**Skill** laden | funktioniert | `Skill(frontend-design:frontend-design)` aus dem Plugin-Cache geladen |
| Plugin-**Agent** dispatchen | scheitert | `Agent type '…' not found. Available agents: claude, Explore, general-purpose, Plan, statusline-setup` |

Sichtbar sind nur Skills aus Plugins, die installiert und aktiviert sind; Skills, die in einer interaktiven Claude-Code-Sitzung über einen anderen Mechanismus erreichbar sind, nicht.

## Projektlayout

```
recipes/                       ein Rezept je Datei, flach — das ausgelieferte Artefakt
extensions.yaml                jeder MCP-Server, einmal deklariert
spec/                          diese Ebene plus eine Spec je Backend
.envrc                         Endpunkte, Zugangsdaten-Abrufe, Konfigurationspfad
```

## Anforderungen

- **MUSS [MUST]** jeden MCP-Server genau einmal für das Repository deklarieren — in `extensions.yaml` —, und Rezepte, die sich darauf stützen, **DÜRFEN NICHT [MUST NOT]** einen eigenen `extensions:`-Block tragen, da ein rezeptlokaler Block den geteilten Satz ersetzt, statt ihn zu erweitern
- **MUSS [MUST]** jede `${VAR}`, die eine Extension referenziert, in deren `env_keys` aufführen, wo immer die Extension deklariert ist
- **MUSS [MUST]** Zugangsdaten aus der Umgebung beziehen; ein literales Zugangsdatum **DARF NICHT [MUST NOT]** in einem Rezept, in `extensions.yaml` oder in einer versionierten Datei auftauchen
- **MUSS [MUST]** jede Nebenbedingung, die gelten muss, in den `prompt` des Rezepts setzen; `instructions` **KANN [MAY]** Rahmen und Ton tragen, **DARF** aber **NICHT [MUST NOT]** der einzige Ort eines Verbots sein
- **MUSS [MUST]** die konkreten Tools benennen, die ein nur lesendes Rezept nicht aufrufen darf, statt nur die Kategorie zu beschreiben, damit das Verbot nicht von der Einordnung des Modells abhängt
- **MUSS [MUST]** das Dateinamens-Suffix `-apply` tragen und die Wirkung in `description` benennen, wenn ein Rezept ein zustandsänderndes Tool aufruft
- **MUSS [MUST]** `recipes/` flach halten; Gruppierung **MUSS [MUST]** in Dateinamen kodiert werden, da das Auffinden keine Unterverzeichnisse durchläuft
- **MUSS [MUST]** im README des Repositorys angeben, dass der Bezug von Rezepten über `GOOSE_RECIPE_GITHUB_REPO` das separate Bereitstellen der Extension-Konfiguration erfordert
- **DARF NICHT [MUST NOT]** einen nur lesenden Prompt als Sicherheitsgrenze behandeln, wenn der Provider Ausführungswerkzeuge mitbringt; ein Rezept, das nicht vertrauenswürdige Eingaben verarbeitet, **MUSS [MUST]** unter einem Provider ohne solche Werkzeuge oder unter `--no-profile` laufen
- **SOLLTE [SHOULD]** ein Konnektivitätsrezept ausliefern, das jeden deklarierten Server nur lesend prüft und je Server PASS/FAIL meldet, und **SOLLTE [SHOULD]** es ausführen, bevor einem anderen Rezept in einer neuen Umgebung vertraut wird
- **SOLLTE [SHOULD]** ein Provider-Oberflächen-Rezept ausliefern, das die Werkzeuge des Agenten inventarisiert, damit die Ausführungsoberfläche eine Messung statt einer Annahme ist
- **SOLLTE [SHOULD]** ein fehlendes Tool als ausdrückliches Schrittergebnis melden, das das Tool benennt, nie als stille Ersetzung
- **SOLLTE [SHOULD]** beim Melden eines Fehlers ein nicht gesetztes Zugangsdatum von einem nicht erreichbaren Server unterscheiden, da eine Extension mit nicht gesetzter `env_keys`-Variable ohne Warnung verschwindet
- **KANN [MAY]** Extensions innerhalb eines einzelnen Rezepts deklarieren, wenn es eigenständig konsumiert werden soll, wobei es dann auf den geteilten Satz vollständig verzichtet

## Akzeptanzkriterien

- [ ] Jeder MCP-Server erscheint genau einmal im gesamten Repository
- [ ] Kein Rezept, das sich auf `extensions.yaml` stützt, deklariert einen `extensions:`-Block
- [ ] Jede in einer Extension verwendete `${VAR}` steht in deren `env_keys`
- [ ] Keine versionierte Datei enthält ein literales Zugangsdatum
- [ ] Jedes Verbot, auf das sich ein Rezept stützt, steht in seinem `prompt`
- [ ] Jedes Rezept, das ein zustandsänderndes Tool aufruft, trägt einen `-apply`-Dateinamen
- [ ] `recipes/` enthält keine Unterverzeichnisse
- [ ] Das README benennt die Anforderung an die Extension-Konfiguration für über GitHub bezogene Rezepte
- [ ] Ein Konnektivitätsrezept existiert und läuft gegen die aktuelle Umgebung durch
- [ ] Ein Provider-Oberflächen-Rezept existiert und sein letztes Ergebnis ist festgehalten
- [ ] `goose recipe validate` läuft für jede Datei in `recipes/` durch

## Offene Fragen

- Ob sich die Werkzeugoberfläche des Providers je Rezept statt je Lauf einschränken lässt; `--no-profile` ist als „lässt Standard-Extensions weg" dokumentiert, seine Wirkung auf providerseitige Werkzeuge wurde nicht gemessen.
- Wie mehrere Dateien in `GOOSE_ADDITIONAL_CONFIG_FILES` getrennt werden und ob sich `~/.config/goose/config.yaml` identisch zu einer zusätzlichen Datei verhält. Ungetestet — die globale Konfiguration des Nutzers wurde bewusst nicht angefasst.
- Ob MCP-Server, die in den Einstellungen des Providers konfiguriert sind, dem Goose-Agenten zugänglich gemacht werden. Die Prüfung ergab keine, aber die Server des Providers waren zu diesem Zeitpunkt fehlerhaft, sodass „nicht weitergereicht" und „weitergereicht, aber defekt" am Ergebnis nicht unterscheidbar sind.
- Ob ein als Plugin installierter Skill für Goose sofort sichtbar wird oder erst nach einem Sitzungsneustart.

## Quelle

- Gemessen gegen Goose 1.45.0 mit `GOOSE_PROVIDER=claude-code`, 2026-08-04: Vorrang von Extensions und `env_keys`-Ersetzung mitgeschnitten mit einem lokalen HTTP-Server, der eingehende Header protokolliert; Auffinden von Rezepten geprüft mit `goose recipe list`; Werkzeugoberfläche und Plugin-Verfügbarkeit geprüft mit `recipes/provider-surface-check.yaml` und `recipes/provider-plugin-check.yaml`
- `goose run --help`, `goose recipe --help` (Goose 1.45.0) für Auffind- und Extension-Optionen
- Backend-Verträge: `spec/mcp/kamerplanter-mcp-server/de.md`, `spec/mcp/home-assistant-mcp-server/de.md`
