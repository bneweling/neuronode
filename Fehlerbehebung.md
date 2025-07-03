Exzellente Beobachtung und absolut kritisches Feedback. Sie haben zwei fundamentale Probleme aufgedeckt, die die User Experience und die Kernfunktionalität direkt beeinträchtigen. Ein flackernder Graph und nicht-persistente Chats sind klassische Symptome, die den Unterschied zwischen einem Prototyp und einem produktionsreifen System ausmachen.

Ihre Analyse ist zu 100% korrekt. Diese Probleme müssen mit höchster Priorität und ohne Abkürzungen behoben werden, bevor wir auch nur an Live-Tests denken.

Hier ist die finale, konsolidierte Arbeitsanweisung, die eine detaillierte Analyse der Ursachen und einen präzisen, qualitativ hochwertigen Lösungsplan für beide Probleme enthält.

---

## Finale Arbeitsanweisung: K9 - "UX Hardening & State Persistence"

**Mission:** Beseitigung der letzten verbleibenden User-Experience-Blocker durch die Implementierung eines robusten State-Managements für die Graphen-Visualisierung und die Herstellung vollständiger Persistenz für alle Nutzer-Chats.

**Dauer:** 2-3 Tage
**Qualitätsmaxime:** Das System muss sich für den Nutzer "solide" und "zuverlässig" anfühlen. Datenverlust ist inakzeptabel. Die UI muss jederzeit einen konsistenten und nachvollziehbaren Zustand anzeigen.

---

### **Problem 1: Graph-Visualisierungs-Instabilität (Das "Flicker"-Problem)**

**Kritische Analyse:**
Das im Video gezeigte Verhalten (Laden → kurzer Graph → wieder Laden) ist ein klassischer Bug im State-Management einer React-Komponente. Die Ursache ist höchstwahrscheinlich ein falsch konfigurierter `useEffect`-Hook, der die Datenabfrage wiederholt und unkontrolliert auslöst.

*   **Hypothese:** Ein `useEffect`, der die Graph-Daten lädt, hat eine Abhängigkeit (im Dependency Array `[...]`), die sich bei jedem Render ändert. Dies führt zu einer Endlosschleife:
    1.  Komponente mounted.
    2.  `useEffect` lädt Daten.
    3.  `setData()` wird aufgerufen.
    4.  Die Komponente rendert neu, weil sich der Daten-State geändert hat.
    5.  Durch den Re-Render ändert sich eine Abhängigkeit im `useEffect`-Array.
    6.  `useEffect` wird *erneut* ausgelöst, setzt den Ladezustand zurück und startet eine neue Datenabfrage. → **Das führt zum "Flickern".**

**Lösungsplan (Keine Abkürzungen):**

**Task 1.1: Refactoring der `GraphVisualization.tsx` Komponente**
*   **Aktion:** Führen Sie ein präzises Refactoring des State-Managements durch.
*   **Implementierungs-Details:**
    1.  **Stabiler Lade-Zustand:** Implementieren Sie einen robusten State für die drei möglichen Zustände der Komponente.
        ```typescript
        // in GraphVisualization.tsx
        const [graphState, setGraphState] = useState<{
          status: 'loading' | 'success' | 'error';
          data: GraphData | null;
          error: BackendError | null;
        }>({ status: 'loading', data: null, error: null });
        ```
    2.  **Korrekter `useEffect`-Hook:** Der Hook, der die Daten lädt, darf **nur einmal** beim Mounten der Komponente oder bei einer expliziten, vom Nutzer ausgelösten Änderung (z.B. eine neue Suche) ausgeführt werden.
        ```typescript
        // in GraphVisualization.tsx
        useEffect(() => {
          const fetchGraphData = async () => {
            setGraphState({ status: 'loading', data: null, error: null });
            try {
              // Nutzen Sie den existierenden API-Hook
              const data = await api.getGraphData(); // Annahme
              setGraphState({ status: 'success', data: data, error: null });
            } catch (err) {
              const parsedError = parseApiError(err); // K3.1.3 Foundation nutzen!
              setGraphState({ status: 'error', data: null, error: parsedError });
            }
          };

          fetchGraphData();
        }, []); // WICHTIG: Leeres Dependency-Array, damit es nur einmal läuft!
        ```
    3.  **Bedingtes Rendering (Conditional Rendering):** Die UI muss den Zustand exakt widerspiegeln.
        ```typescript
        // im JSX-Teil
        if (graphState.status === 'loading') {
          return <GraphLoadingIndicator />; // Zeigt "Graph wird geladen..."
        }
        if (graphState.status === 'error') {
          // K3.1.3 Foundation nutzen!
          return <InlineErrorDisplay error={graphState.error} />; 
        }
        if (graphState.status === 'success' && graphState.data) {
          // NUR DANN den Graphen rendern!
          return <CytoscapeComponent data={graphState.data} />;
        }
        return null; // Fallback
        ```

**Definition of Done für Task 1:**
*   `[ ]` Das "Flickern" ist zu 100% beseitigt.
*   `[ ]` Die Komponente zeigt zuverlässig einen der drei Zustände (Laden, Erfolg, Fehler) an.
*   `[ ]` API-Calls für die Graph-Daten werden nur einmal beim initialen Laden ausgelöst.

---

### **Problem 2: Fehlende Chat-Persistenz**

**Kritische Analyse:**
Wie von Ihnen korrekt beobachtet, wird der Chat-Zustand aktuell nur im lokalen React-State (`useState`) gehalten. Dieser Zustand ist flüchtig (ephemeral) und wird bei jedem Verlassen der Seite oder Neuladen des Browsers zurückgesetzt. Das ist für eine Enterprise-Anwendung inakzeptabel.

**Lösungsplan (Enterprise-Grade State Management):**

**Task 2.1: Implementierung einer globalen State-Management-Lösung**
*   **Strategische Entscheidung:** Wir verwenden **Zustand** als State-Management-Bibliothek. Sie ist leichtgewichtiger als Redux, aber mächtiger und zentraler als der React Context allein.
*   **Aktion:** Fügen Sie die Abhängigkeit hinzu: `npm install zustand`.

**Task 2.2: Erstellung eines persistenten "Chat Stores"**
*   **Aktion:** Erstellen Sie eine neue Datei `src/stores/chatStore.ts`.
*   **Implementierung:** Wir nutzen die `persist`-Middleware von Zustand, um den gesamten Chat-Verlauf automatisch im `localStorage` des Browsers zu speichern.
    ```typescript
    // src/stores/chatStore.ts
    import { create } from 'zustand';
    import { persist } from 'zustand/middleware';

    interface Message { /* ... Ihre Message-Definition ... */ }
    interface ChatSession {
      id: string;
      title: string;
      messages: Message[];
      createdAt: Date;
    }

    interface ChatState {
      sessions: Record<string, ChatSession>;
      currentChatId: string | null;
      actions: {
        addMessage: (chatId: string, message: Message) => void;
        createNewChat: () => string; // Gibt die ID des neuen Chats zurück
        switchChat: (chatId: string) => void;
        getChatHistory: (chatId: string) => Message[];
        getAllChats: () => ChatSession[];
      }
    }

    export const useChatStore = create<ChatState>()(
      persist(
        (set, get) => ({
          sessions: {},
          currentChatId: null,
          actions: {
            addMessage: (chatId, message) => set((state) => ({
              sessions: {
                ...state.sessions,
                [chatId]: {
                  ...state.sessions[chatId],
                  messages: [...state.sessions[chatId].messages, message],
                },
              },
            })),
            createNewChat: () => {
              const newId = `chat_${Date.now()}`;
              const newChat: ChatSession = {
                id: newId,
                title: `Neuer Chat ${Object.keys(get().sessions).length + 1}`,
                messages: [],
                createdAt: new Date(),
              };
              set((state) => ({
                sessions: { ...state.sessions, [newId]: newChat },
                currentChatId: newId,
              }));
              return newId;
            },
            switchChat: (chatId) => set({ currentChatId: chatId }),
            getChatHistory: (chatId) => get().sessions[chatId]?.messages || [],
            getAllChats: () => Object.values(get().sessions).sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime()),
          }
        }),
        {
          name: 'ki-wissenssystem-chat-storage', // Name des Eintrags im localStorage
          partialize: (state) => ({ sessions: state.sessions, currentChatId: state.currentChatId }), // Nur diese Teile persistieren
        }
      )
    );
    ```

**Task 2.3: Refactoring der Chat-Komponenten**
*   **Aktion:** Bauen Sie die `ChatInterface.tsx` und alle zugehörigen Komponenten (z.B. eine `ChatHistorySidebar.tsx`) komplett auf den neuen `useChatStore` um.
    *   **Lokale `useState`-Aufrufe für die Chat-Nachrichten werden vollständig entfernt.**
    *   **Beispiel-Verwendung:**
        ```typescript
        // in ChatInterface.tsx
        import { useChatStore } from '@/stores/chatStore';

        function ChatInterface() {
          const currentChatId = useChatStore((state) => state.currentChatId);
          const actions = useChatStore((state) => state.actions);
          const messages = useChatStore((state) => state.sessions[currentChatId]?.messages || []);

          const handleSendMessage = (text: string) => {
            const userMessage = { ... };
            actions.addMessage(currentChatId, userMessage);
            // ... API-Call ...
            const assistantMessage = { ... };
            actions.addMessage(currentChatId, assistantMessage);
          };

          // ... JSX ...
        }
        ```

**Definition of Done für Task 2:**
*   `[ ]` Alle Chat-Nachrichten bleiben nach einem Browser-Neustart oder Seitenwechsel erhalten.
*   `[ ]` Ein Nutzer kann einen neuen Chat erstellen, ohne dass der alte verloren geht.
*   `[ ]` Eine Chat-Historien-Anzeige (z.B. in einer Seitenleiste) zeigt alle gespeicherten Chats an und ermöglicht das Wechseln zwischen ihnen.

---

**Finale Anweisung an das Team:**
"Team, wir haben zwei kritische UX-Blocker identifiziert, die unsere Enterprise-Qualität untergraben. Wir starten sofort den 'UX-Hardening'-Sprint.

**Fokus 1: Graph-Stabilität.** Refactort die `GraphVisualization`-Komponente. Implementiert ein sauberes, dreistufiges State-Management (`loading`, `success`, `error`) und stellt sicher, dass der Datenabruf-Hook nur einmal ausgeführt wird. Das Flickern muss zu 100% eliminiert werden.

**Fokus 2: Chat-Persistenz.** Implementiert den globalen `useChatStore` mit Zustand und `persist`-Middleware. Reißt das lokale State-Management aus den Chat-Komponenten heraus und bindet sie vollständig an den neuen, persistenten Store an.

Wenn dieser Sprint abgeschlossen ist, ist das System nicht nur funktional robust, sondern fühlt sich auch so an. Das ist der letzte Schritt, bevor wir in die Live-Tests gehen."