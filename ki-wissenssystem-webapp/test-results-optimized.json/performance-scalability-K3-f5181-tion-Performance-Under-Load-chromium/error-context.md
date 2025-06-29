# Page snapshot

```yaml
- banner:
  - text: KI-Chat
  - button "Startseite"
  - button "KI-Chat"
  - button "Wissensgraph"
  - button "Dokumente"
  - button
- main:
  - heading "Chat-Verlauf" [level=6]
  - button "Neuer Chat"
  - list:
    - listitem:
      - button "Neuer Chat 29.06.2025":
        - text: Neuer Chat
        - paragraph: 29.06.2025
        - button
  - button
  - heading "Neuer Chat" [level=6]
  - text: 0 Nachrichten
  - list:
    - listitem:
      - paragraph: Hallo! Ich bin Ihr KI-Assistent. Wie kann ich Ihnen heute helfen?
      - text: 12:53
  - textbox "Nachricht eingeben..."
  - button [disabled]
- alert
- button "Open Next.js Dev Tools":
  - img
```