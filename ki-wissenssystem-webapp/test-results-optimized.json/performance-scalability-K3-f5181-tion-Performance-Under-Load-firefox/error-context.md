# Page snapshot

```yaml
- banner:
  - text: Dokumente
  - button "Startseite"
  - button "KI-Chat"
  - button "Wissensgraph"
  - button "Dokumente"
  - button
- main:
  - heading "📄 Dokumente hochladen" [level=1]
  - paragraph: Laden Sie Ihre Dokumente hoch für automatische Analyse und Knowledge Graph Integration.
  - heading "Dateien hier ablegen oder klicken zum Auswählen" [level=6]
  - paragraph: "Unterstützte Formate: PDF, Word, Excel, PowerPoint, Text"
  - heading "📋 Upload-Liste (1 Datei)" [level=2]
  - button "Alle hochladen (0)" [disabled]
  - button "Liste leeren"
  - list:
    - text: performance-test.pdf
    - paragraph: 0.00 MB
    - button
    - paragraph: Analysiere Dokument...
    - paragraph: 10%
    - progressbar
  - alert:
    - paragraph:
      - strong: "💡 Tipp:"
      - text: Das System erkennt automatisch Dokumenttypen wie BSI IT-Grundschutz, ISO 27001, NIST CSF und andere Compliance-Standards. Nach dem Upload können Sie die Ergebnisse direkt im Knowledge Graph visualisieren oder per Chat abfragen.
- alert
- button "Open Next.js Dev Tools":
  - img
```