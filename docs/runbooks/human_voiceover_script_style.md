# Human Voiceover Script Style

## Zweck

Dieses Runbook definiert, wie gesprochene Skripte im Video-Generate-Flow klingen
sollen. Der technische 10-Minuten-MVP funktioniert bereits mit YouTube-Transcript,
Longform-Script, OpenAI Images, ElevenLabs Voice, YouTube Packaging und finalem
`final_video.mp4`. Der naechste Qualitaetsschritt ist ein Voiceover-Text, der
weniger nach interner Kapitelstruktur und mehr nach menschlicher YouTube-
Erzaehlung klingt.

## Struktur vs. gesprochener Text

`script.json` ist die strukturierte Arbeitsform. Sie darf Kapitel, Hook, interne
Logik, Szenen, Quellenhinweise und technische Felder enthalten. Diese Struktur
hilft Planung, Visualisierung, Timeline, Review und Debugging.

`voiceover_text.txt` ist die gesprochene Fassung. Sie soll wie ein natuerlicher
Fliesstext klingen: ruhig, nachvollziehbar, mit weichen Uebergaengen und ohne
sichtbare interne Strukturbegriffe.

## Verbote im Voiceover

- Kein `Kapitel 1`.
- Kein `Kapitel 2`.
- Kein `In diesem Kapitel`.
- Keine JSON-, Manifest-, Feld- oder Strukturbegriffe.
- Keine Stichpunkt-Sprache.
- Kein mechanisches Vorlesen von Kapitelueberschriften.
- Kein 1:1-Vorlesen des Transkripts.
- Keine internen Labels wie `Hook`, `CTA`, `Outro`, `Abschnitt`, `Scene` oder `Beat`.

## Gewuenschter Stil

- Menschlich und ruhig.
- Erzaehlerisch statt tabellarisch.
- YouTube-Doku- oder Kommentar-Stil.
- Klare, natuerliche Uebergaenge.
- Einfache, gesprochene Saetze.
- Sachlich, aber nicht trocken.
- Kontext erklaeren, ohne neue Fakten zu erfinden.
- Beobachtung, Einordnung und Bewertung sprachlich sauber trennen.

## Aufbau

Der gesprochene Text soll typischerweise so wirken:

1. Hook: ein kurzer Einstieg, der die zentrale Frage oder Spannung setzt.
2. Intro: knappe Orientierung, worum es geht und warum es relevant ist.
3. Hauptteil: mehrere Gedanken oder Szenen mit fluessigen Uebergaengen.
4. Einordnung: was die Aussagen, Ereignisse oder Reaktionen bedeuten koennten.
5. Fazit: ruhige Zusammenfassung ohne kuenstliches Drama.
6. Dezenter CTA: kurz, passend zum Thema und nicht zu werblich.

## Beispiele

Schlecht:

```text
Kapitel 1: Die Ausgangslage. In diesem Kapitel geht es um die erste Reaktion.
Kapitel 2: Die politische Einordnung.
```

Gut:

```text
Am Anfang steht eine Reaktion, die viele Zuschauer sofort einordnen wollen:
Was ist hier eigentlich passiert, und warum sorgt gerade diese Aussage fuer so
viel Widerspruch? Von dort aus lohnt sich ein ruhiger Blick auf den Kontext.
```

Schlecht:

```text
CTA: Abonniere den Kanal und aktiviere die Glocke.
```

Gut:

```text
Wenn du solche ruhigen Einordnungen hilfreich findest, abonniere den Kanal gern.
```

## CTA und Outro

- Kurz halten.
- Nicht zu werblich formulieren.
- Kein lauter Sales-Ton.
- Zum Thema passend und ruhig.
- Nicht mehrfach wiederholen.
- Am Ende darf ein kurzer Dank stehen, aber kein langer Werbeblock.

## Fakten und Transcript-Nutzung

Das Transcript ist Quellenmaterial, nicht der fertige Sprechertext. Der
Voiceover-Text soll die vorhandenen Aussagen eigenstaendig erzaehlen,
paraphrasieren und einordnen. Dabei gilt:

- Keine erfundenen Fakten.
- Keine unbelegten Details hinzufuegen.
- Keine wörtliche Abschrift, sofern nicht ausdruecklich als Zitat markiert und
  kurz gehalten.
- Bei Unsicherheit lieber allgemein und vorsichtig formulieren.
- Der gesprochene Text darf glatter und menschlicher sein als das Transkript,
  aber nicht inhaltlich freier.

## Agent-Regel

Wenn ein Agent einen Voiceover-Text erzeugt oder glättet, soll er zuerst alle
sichtbaren Strukturmarker entfernen, dann Uebergaenge ergaenzen und zuletzt
pruefen, ob der Text laut gesprochen natuerlich klingt. `script.json` darf
strukturiert bleiben; `voiceover_text.txt` muss fuer Menschen geschrieben sein.
