import { MarkdownRenderer, Component } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { Message, ChatSession, ChatStorage, ChatHistoryEntry } from '../types';

export class ChatInterface extends Component {
  private container: HTMLElement;
  private plugin: KIWissenssystemPlugin;
  private messages: Message[] = [];
  private onSendMessage: (message: string) => void;
  private onContextClick: (nodeId: string) => void;
  private inputField: HTMLTextAreaElement;
  private messagesContainer: HTMLElement;
  private suggestionsContainer: HTMLElement;
  
  // Neue Chat-Speicherung Features
  private currentSession: ChatSession | null = null;
  private chatStorage: ChatStorage;
  private historyContainer: HTMLElement;
  private isHistoryVisible: boolean = false;

  constructor(
    container: HTMLElement,
    plugin: KIWissenssystemPlugin,
    onSendMessage: (message: string) => void,
    onContextClick: (nodeId: string) => void
  ) {
    super();
    this.container = container;
    this.plugin = plugin;
    this.onSendMessage = onSendMessage;
    this.onContextClick = onContextClick;
    
    // Chat-Speicherung initialisieren
    this.initializeChatStorage();
    this.initialize();
  }

  private async initializeChatStorage() {
    // Lade existierende Chat-Historie aus Obsidian's Daten
    const data = await this.plugin.loadData();
    
    this.chatStorage = data?.chatStorage || {
      sessions: [],
      currentSessionId: null,
      settings: {
        maxSessions: 50,
        autoSave: true,
        autoTitle: true
      }
    };

    // Lade aktuelle Sitzung oder erstelle neue
    if (this.chatStorage.currentSessionId) {
      this.currentSession = this.chatStorage.sessions.find(
        s => s.id === this.chatStorage.currentSessionId
      ) || null;
    }

    if (!this.currentSession) {
      this.createNewSession();
    } else {
      // Lade Nachrichten der aktuellen Sitzung
      this.messages = this.currentSession.messages;
    }
  }

  private initialize() {
    // Header mit erweiterten Funktionen
    const header = this.container.createDiv('ki-chat-header');
    
    const headerLeft = header.createDiv('ki-chat-header-left');
    headerLeft.createEl('h3', { text: 'KI-Assistent' });
    
    // Session-Info
    const sessionInfo = headerLeft.createDiv('ki-chat-session-info');
    this.updateSessionInfo(sessionInfo);
    
    const headerActions = header.createDiv('ki-chat-header-actions');
    
    // Chat-Historie Button
    const historyBtn = headerActions.createEl('button', {
      text: '📚 Historie',
      cls: 'ki-chat-history-btn'
    });
    historyBtn.addEventListener('click', () => this.toggleHistory());

    // Neue Sitzung Button
    const newSessionBtn = headerActions.createEl('button', {
      text: '➕ Neu',
      cls: 'ki-chat-new-session-btn'
    });
    newSessionBtn.addEventListener('click', () => this.createNewSession());
    
    // Clear chat button
    const clearBtn = headerActions.createEl('button', {
      text: 'Leeren',
      cls: 'ki-chat-clear-btn'
    });
    clearBtn.addEventListener('click', () => this.clearCurrentSession());

    // Chat-Historie Container (zunächst versteckt)
    this.historyContainer = this.container.createDiv('ki-chat-history');
    this.historyContainer.style.display = 'none';
    this.renderChatHistory();

    // Messages container
    this.messagesContainer = this.container.createDiv('ki-chat-messages');
    
    // Lade existierende Nachrichten
    this.renderExistingMessages();
    
    // Welcome message (nur wenn noch keine Nachrichten)
    if (this.messages.length === 0) {
      this.addWelcomeMessage();
    }

    // Suggestions container
    this.suggestionsContainer = this.container.createDiv('ki-chat-suggestions');
    this.showDefaultSuggestions();

    // Input area
    const inputContainer = this.container.createDiv('ki-chat-input-container');
    
    this.inputField = inputContainer.createEl('textarea', {
      placeholder: 'Stellen Sie Ihre Frage...',
      cls: 'ki-chat-input'
    });
    
    this.inputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    const sendBtn = inputContainer.createEl('button', {
      text: 'Senden',
      cls: 'ki-chat-send-btn'
    });
    sendBtn.addEventListener('click', () => this.sendMessage());

    // Apply styles
    this.applyStyles();
  }

  private createNewSession() {
    // Speichere aktuelle Sitzung falls vorhanden
    if (this.currentSession) {
      this.saveCurrentSession();
    }

    // Erstelle neue Sitzung
    this.currentSession = {
      id: this.generateSessionId(),
      title: 'Neue Sitzung',
      created: new Date(),
      lastUpdated: new Date(),
      messages: [],
      tags: []
    };

    // Lösche aktuellen Chat
    this.messages = [];
    this.messagesContainer.empty();
    
    // Begrüßungsnachricht
    this.addWelcomeMessage();
    
    // Speichere neue Sitzung
    this.chatStorage.currentSessionId = this.currentSession.id;
    this.chatStorage.sessions.push(this.currentSession);
    this.saveChatStorage();
    
    // UI aktualisieren
    this.updateSessionInfo();
    this.renderChatHistory();
  }

  private async saveCurrentSession() {
    if (!this.currentSession) return;

    // Update session data
    this.currentSession.messages = [...this.messages];
    this.currentSession.lastUpdated = new Date();
    
    // Auto-generate title if needed
    if (this.chatStorage.settings.autoTitle && 
        this.currentSession.title === 'Neue Sitzung' && 
        this.messages.length > 1) {
      this.currentSession.title = this.generateSessionTitle();
    }

    // Find and update session in storage
    const sessionIndex = this.chatStorage.sessions.findIndex(
      s => s.id === this.currentSession!.id
    );
    
    if (sessionIndex >= 0) {
      this.chatStorage.sessions[sessionIndex] = this.currentSession;
    }

    await this.saveChatStorage();
  }

  private async saveChatStorage() {
    // Begrenze Anzahl der gespeicherten Sitzungen
    if (this.chatStorage.sessions.length > this.chatStorage.settings.maxSessions) {
      // Sortiere nach lastUpdated und behalte nur die neuesten
      this.chatStorage.sessions.sort((a, b) => 
        new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime()
      );
      this.chatStorage.sessions = this.chatStorage.sessions.slice(0, this.chatStorage.settings.maxSessions);
    }

    // Speichere in Obsidian's Plugin-Daten
    const data = await this.plugin.loadData() || {};
    data.chatStorage = this.chatStorage;
    await this.plugin.saveData(data);
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateSessionTitle(): string {
    const firstUserMessage = this.messages.find(m => m.role === 'user');
    if (firstUserMessage) {
      const words = firstUserMessage.content.trim().split(' ').slice(0, 5);
      return words.join(' ') + (firstUserMessage.content.split(' ').length > 5 ? '...' : '');
    }
    return `Chat ${new Date().toLocaleDateString()}`;
  }

  private renderExistingMessages() {
    this.messages.forEach(message => {
      this.renderMessage(message);
    });
  }

  private renderMessage(message: Message) {
    const messageEl = this.messagesContainer.createDiv({
      cls: `ki-chat-message ki-chat-message-${message.role}`
    });

    // Avatar
    const avatar = messageEl.createDiv('ki-chat-avatar');
    avatar.setText(message.role === 'user' ? 'U' : 'KI');

    // Content
    const content = messageEl.createDiv('ki-chat-content');
    
    // Render markdown content
    const contentEl = content.createDiv('ki-chat-text');
    MarkdownRenderer.renderMarkdown(
      message.content,
      contentEl,
      '',
      this.plugin
    );

    // Add click handlers for links to nodes
    contentEl.querySelectorAll('a[data-node-id]').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const nodeId = link.getAttribute('data-node-id');
        if (nodeId) this.onContextClick(nodeId);
      });
    });

    // Sources
    if (message.sources && message.sources.length > 0) {
      const sourcesEl = content.createDiv('ki-chat-sources');
      sourcesEl.createEl('div', { 
        text: 'Quellen:',
        cls: 'ki-chat-sources-title'
      });
      
      message.sources.forEach(source => {
        const sourceEl = sourcesEl.createDiv('ki-chat-source');
        
        if (source.control_id) {
          const link = sourceEl.createEl('a', {
            text: `${source.control_id}: ${source.title || 'Unknown'}`,
            cls: 'ki-chat-source-link'
          });
          link.setAttribute('data-node-id', source.control_id);
          link.addEventListener('click', (e) => {
            e.preventDefault();
            if (source.control_id) {
              this.onContextClick(source.control_id);
            }
          });
        } else {
          sourceEl.setText(`${source.source} (${source.type})`);
        }
      });
    }

    // Confidence indicator
    if (message.confidence !== undefined && message.role === 'assistant') {
      const confidenceEl = content.createDiv('ki-chat-confidence');
      const percentage = Math.round(message.confidence * 100);
      confidenceEl.setText(`Konfidenz: ${percentage}%`);
      
      // Color based on confidence
      if (percentage >= 80) {
        confidenceEl.addClass('high-confidence');
      } else if (percentage >= 60) {
        confidenceEl.addClass('medium-confidence');
      } else {
        confidenceEl.addClass('low-confidence');
      }
    }

    // Timestamp
    const timestamp = content.createDiv('ki-chat-timestamp');
    timestamp.setText(this.formatTimestamp(message.timestamp));

    // Scroll to bottom
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }

  private addWelcomeMessage() {
    const welcomeMessage: Message = {
      role: 'assistant',
      content: 'Hallo! Ich bin Ihr KI-Assistent für Compliance und Sicherheit. Wie kann ich Ihnen helfen?',
      timestamp: new Date()
    };
    this.addMessage(welcomeMessage);
  }

  private updateSessionInfo(container?: HTMLElement) {
    const sessionInfo = container || this.container.querySelector('.ki-chat-session-info') as HTMLElement;
    if (!sessionInfo || !this.currentSession) return;

    sessionInfo.empty();
    
    const titleEl = sessionInfo.createEl('span', {
      text: this.currentSession.title,
      cls: 'ki-chat-session-title'
    });
    
    const countEl = sessionInfo.createEl('span', {
      text: `(${this.messages.length} Nachrichten)`,
      cls: 'ki-chat-message-count'
    });
  }

  private toggleHistory() {
    this.isHistoryVisible = !this.isHistoryVisible;
    this.historyContainer.style.display = this.isHistoryVisible ? 'block' : 'none';
    
    if (this.isHistoryVisible) {
      this.renderChatHistory();
    }
  }

  private renderChatHistory() {
    this.historyContainer.empty();
    
    const historyHeader = this.historyContainer.createDiv('ki-chat-history-header');
    historyHeader.createEl('h4', { text: 'Chat-Historie' });
    
    const closeBtn = historyHeader.createEl('button', {
      text: '✕',
      cls: 'ki-chat-history-close'
    });
    closeBtn.addEventListener('click', () => this.toggleHistory());

    const historyList = this.historyContainer.createDiv('ki-chat-history-list');
    
    // Sortiere Sitzungen nach Datum (neueste zuerst)
    const sortedSessions = [...this.chatStorage.sessions].sort((a, b) => 
      new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime()
    );

    sortedSessions.forEach(session => {
      const historyEntry = historyList.createDiv('ki-chat-history-entry');
      
      if (session.id === this.currentSession?.id) {
        historyEntry.addClass('active');
      }
      
      const entryHeader = historyEntry.createDiv('ki-chat-history-entry-header');
      entryHeader.createEl('span', {
        text: session.title,
        cls: 'ki-chat-history-entry-title'
      });
      
      const entryMeta = historyEntry.createDiv('ki-chat-history-entry-meta');
      entryMeta.createEl('span', {
        text: `${session.messages.length} Nachrichten`,
        cls: 'ki-chat-history-entry-count'
      });
      entryMeta.createEl('span', {
        text: this.formatDate(session.lastUpdated),
        cls: 'ki-chat-history-entry-date'
      });
      
      // Preview der ersten User-Nachricht
      const firstUserMessage = session.messages.find(m => m.role === 'user');
      if (firstUserMessage) {
        const preview = historyEntry.createDiv('ki-chat-history-entry-preview');
        preview.setText(firstUserMessage.content.slice(0, 100) + 
          (firstUserMessage.content.length > 100 ? '...' : ''));
      }

      // Click-Handler
      historyEntry.addEventListener('click', () => this.loadSession(session.id));
      
      // Delete button
      const deleteBtn = historyEntry.createEl('button', {
        text: '🗑️',
        cls: 'ki-chat-history-delete-btn'
      });
      deleteBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteSession(session.id);
      });
    });
  }

  private async loadSession(sessionId: string) {
    // Speichere aktuelle Sitzung
    await this.saveCurrentSession();
    
    // Lade gewählte Sitzung
    const session = this.chatStorage.sessions.find(s => s.id === sessionId);
    if (!session) return;

    this.currentSession = session;
    this.chatStorage.currentSessionId = sessionId;
    
    // Aktualisiere UI
    this.messages = [...session.messages];
    this.messagesContainer.empty();
    this.renderExistingMessages();
    
    this.updateSessionInfo();
    this.toggleHistory(); // Historie schließen
    
    await this.saveChatStorage();
  }

  private async deleteSession(sessionId: string) {
    if (!confirm('Möchten Sie diese Chat-Sitzung wirklich löschen?')) return;
    
    // Entferne Sitzung
    this.chatStorage.sessions = this.chatStorage.sessions.filter(s => s.id !== sessionId);
    
    // Falls aktuelle Sitzung gelöscht wurde, erstelle neue
    if (this.currentSession?.id === sessionId) {
      this.createNewSession();
    }
    
    await this.saveChatStorage();
    this.renderChatHistory();
  }

  private clearCurrentSession() {
    if (!confirm('Möchten Sie den aktuellen Chat wirklich leeren?')) return;
    
    this.messages = [];
    this.messagesContainer.empty();
    this.addWelcomeMessage();
    
    if (this.currentSession) {
      this.currentSession.messages = [];
      this.currentSession.lastUpdated = new Date();
      this.saveCurrentSession();
    }
    
    this.updateSessionInfo();
  }

  private formatDate(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - new Date(date).getTime();
    const diffHours = diffMs / (1000 * 60 * 60);
    const diffDays = diffMs / (1000 * 60 * 60 * 24);

    if (diffHours < 1) {
      return 'Vor wenigen Minuten';
    } else if (diffHours < 24) {
      return `Vor ${Math.floor(diffHours)} Stunden`;
    } else if (diffDays < 7) {
      return `Vor ${Math.floor(diffDays)} Tagen`;
    } else {
      return new Date(date).toLocaleDateString();
    }
  }

  private sendMessage() {
    const message = this.inputField.value.trim();
    if (!message) return;

    // Add user message
    this.addMessage({
      role: 'user',
      content: message,
      timestamp: new Date()
    });

    // Clear input
    this.inputField.value = '';
    
    // Hide suggestions
    this.suggestionsContainer.style.display = 'none';

    // Send message
    this.onSendMessage(message);
  }

  addMessage(message: Message) {
    this.messages.push(message);
    
    // Render the message
    this.renderMessage(message);
    
    // Auto-save if enabled
    if (this.chatStorage.settings.autoSave) {
      this.saveCurrentSession();
    }
    
    // Update session info
    this.updateSessionInfo();
  }

  showProcessingIndicator() {
    const indicator = this.messagesContainer.createDiv('ki-chat-processing');
    indicator.createEl('div', { cls: 'ki-chat-processing-dots' });
    indicator.createEl('span', { text: 'KI denkt nach...' });
    
    // Auto-scroll
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    
    // Remove after response
    setTimeout(() => {
      indicator.remove();
    }, 30000); // Safety timeout
  }

  showError(error: string) {
    // Remove processing indicator
    this.messagesContainer.querySelector('.ki-chat-processing')?.remove();
    
    this.addMessage({
      role: 'assistant',
      content: `❌ Fehler: ${error}`,
      timestamp: new Date()
    });
  }

  showFollowUpQuestions(questions: string[]) {
    this.suggestionsContainer.empty();
    this.suggestionsContainer.style.display = 'block';
    
    const title = this.suggestionsContainer.createEl('div', {
      text: 'Mögliche Folgefragen:',
      cls: 'ki-suggestions-title'
    });

    questions.forEach(question => {
      const btn = this.suggestionsContainer.createEl('button', {
        text: question,
        cls: 'ki-suggestion-btn'
      });
      
      btn.addEventListener('click', () => {
        this.inputField.value = question;
        this.sendMessage();
      });
    });
  }

  showDefaultSuggestions() {
    const defaultQuestions = [
      'Was fordert BSI C5 zu Multi-Factor Authentication?',
      'Wie implementiere ich Verschlüsselung in Azure?',
      'Zeige mir alle Controls für Zugriffskontrolle',
      'Was ist der Unterschied zwischen BSI und ISO 27001?'
    ];
    
    this.showFollowUpQuestions(defaultQuestions);
  }

  updateSuggestions(suggestions: string[]) {
    // Update autocomplete suggestions
    // This could be implemented as a dropdown
  }

  clearChat() {
    this.messages = this.messages.filter(m => m.role === 'assistant' && this.messages.indexOf(m) === 0);
    
    const messages = this.messagesContainer.querySelectorAll('.ki-chat-message');
    messages.forEach((msg, index) => {
      if (index > 0) msg.remove();
    });
    
    this.showDefaultSuggestions();
  }

  getConversationHistory(): Array<{role: string, content: string}> {
    return this.messages.map(m => ({
      role: m.role,
      content: m.content
    }));
  }

  private formatTimestamp(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Gerade eben';
    if (diff < 3600000) return `Vor ${Math.floor(diff / 60000)} Minuten`;
    if (diff < 86400000) return `Vor ${Math.floor(diff / 3600000)} Stunden`;
    
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  private applyStyles() {
    const style = document.createElement('style');
    style.textContent = `
      .ki-chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
      }

      .ki-chat-header h3 {
        margin: 0;
        font-size: 1.1rem;
      }

      .ki-chat-clear-btn {
        font-size: 0.85rem;
        padding: 0.25rem 0.75rem;
      }

      .ki-chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
      }

      .ki-chat-message {
        display: flex;
        gap: 0.75rem;
        animation: fadeIn 0.3s ease-in;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .ki-chat-message-user {
        flex-direction: row-reverse;
      }

      .ki-chat-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
      }

      .ki-chat-message-user .ki-chat-avatar {
        background: var(--interactive-accent);
        color: white;
      }

      .ki-chat-message-assistant .ki-chat-avatar {
        background: var(--background-modifier-form-field);
        color: var(--text-normal);
      }

      .ki-chat-content {
        flex: 1;
        max-width: 80%;
      }

      .ki-chat-message-user .ki-chat-content {
        align-items: flex-end;
        display: flex;
        flex-direction: column;
      }

      .ki-chat-text {
        background: var(--background-primary-alt);
        padding: 0.75rem 1rem;
        border-radius: 12px;
        line-height: 1.5;
      }

      .ki-chat-message-user .ki-chat-text {
        background: var(--interactive-accent);
        color: white;
      }

      .ki-chat-sources {
        margin-top: 0.5rem;
        padding: 0.5rem;
        background: var(--background-modifier-form-field);
        border-radius: 8px;
        font-size: 0.85rem;
      }

      .ki-chat-sources-title {
        font-weight: 600;
        margin-bottom: 0.25rem;
      }

      .ki-chat-source {
        padding: 0.125rem 0;
      }

      .ki-chat-source-link {
        color: var(--link-color);
        text-decoration: none;
        cursor: pointer;
      }

      .ki-chat-source-link:hover {
        text-decoration: underline;
      }

      .ki-chat-confidence {
        margin-top: 0.5rem;
        font-size: 0.75rem;
        opacity: 0.8;
      }

      .high-confidence { color: var(--text-success); }
      .medium-confidence { color: var(--text-warning); }
      .low-confidence { color: var(--text-error); }

      .ki-chat-timestamp {
        font-size: 0.75rem;
        opacity: 0.6;
        margin-top: 0.25rem;
      }

      .ki-chat-processing {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
        color: var(--text-muted);
      }

      .ki-chat-processing-dots {
        display: flex;
        gap: 0.25rem;
      }

      .ki-chat-processing-dots::before,
      .ki-chat-processing-dots::after,
      .ki-chat-processing-dots {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
        animation: pulse 1.5s infinite;
      }

      .ki-chat-processing-dots::before {
        animation-delay: 0s;
      }

      .ki-chat-processing-dots {
        animation-delay: 0.5s;
      }

      .ki-chat-processing-dots::after {
        animation-delay: 1s;
      }

      @keyframes pulse {
        0%, 60%, 100% { opacity: 0.3; }
        30% { opacity: 1; }
      }

      .ki-chat-suggestions {
        padding: 1rem;
        border-top: 1px solid var(--background-modifier-border);
        display: none;
      }

      .ki-suggestions-title {
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--text-muted);
      }

      .ki-suggestion-btn {
        display: block;
        width: 100%;
        text-align: left;
        padding: 0.5rem 0.75rem;
        margin: 0.25rem 0;
        background: var(--background-modifier-form-field);
        border: 1px solid var(--background-modifier-border);
        border-radius: 6px;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ki-suggestion-btn:hover {
        background: var(--background-modifier-form-field-highlighted);
        transform: translateX(4px);
      }

      .ki-chat-input-container {
        display: flex;
        gap: 0.5rem;
        padding: 1rem;
        border-top: 1px solid var(--background-modifier-border);
      }

      .ki-chat-input {
        flex: 1;
        min-height: 60px;
        max-height: 200px;
        padding: 0.75rem;
        border: 1px solid var(--background-modifier-border);
        border-radius: 8px;
        resize: vertical;
        font-family: inherit;
        font-size: 0.95rem;
        line-height: 1.5;
      }

      .ki-chat-input:focus {
        outline: none;
        border-color: var(--interactive-accent);
      }

      .ki-chat-send-btn {
        padding: 0.75rem 1.5rem;
        background: var(--interactive-accent);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }

      .ki-chat-send-btn:hover {
        background: var(--interactive-accent-hover);
      }

      /* Chat-Historie Styles */
      .ki-chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
        background: var(--background-primary);
      }

      .ki-chat-header-left {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
      }

      .ki-chat-header-left h3 {
        margin: 0;
        font-size: 1.2rem;
      }

      .ki-chat-session-info {
        display: flex;
        gap: 0.5rem;
        font-size: 0.8rem;
        color: var(--text-muted);
      }

      .ki-chat-session-title {
        font-weight: 500;
        color: var(--text-normal);
      }

      .ki-chat-header-actions {
        display: flex;
        gap: 0.5rem;
      }

      .ki-chat-header-actions button {
        padding: 0.5rem 0.75rem;
        font-size: 0.8rem;
        border-radius: 6px;
        background: var(--background-modifier-form-field);
        border: 1px solid var(--background-modifier-border);
        cursor: pointer;
        transition: all 0.2s;
      }

      .ki-chat-header-actions button:hover {
        background: var(--background-modifier-form-field-highlighted);
      }

      .ki-chat-history {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--background-primary);
        border: 1px solid var(--background-modifier-border);
        border-radius: 8px;
        box-shadow: var(--shadow-l);
        z-index: 1000;
        max-height: 400px;
        overflow-y: auto;
      }

      .ki-chat-history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
        background: var(--background-modifier-form-field);
      }

      .ki-chat-history-header h4 {
        margin: 0;
        font-size: 1rem;
      }

      .ki-chat-history-close {
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        color: var(--text-muted);
        padding: 0.25rem;
        line-height: 1;
      }

      .ki-chat-history-close:hover {
        color: var(--text-normal);
      }

      .ki-chat-history-list {
        max-height: 300px;
        overflow-y: auto;
      }

      .ki-chat-history-entry {
        position: relative;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--background-modifier-border);
        cursor: pointer;
        transition: background 0.2s;
      }

      .ki-chat-history-entry:hover {
        background: var(--background-modifier-hover);
      }

      .ki-chat-history-entry.active {
        background: var(--background-modifier-form-field);
        border-left: 3px solid var(--interactive-accent);
      }

      .ki-chat-history-entry-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
      }

      .ki-chat-history-entry-title {
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-normal);
        max-width: 80%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .ki-chat-history-entry-meta {
        display: flex;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 0.25rem;
      }

      .ki-chat-history-entry-preview {
        font-size: 0.8rem;
        color: var(--text-muted);
        line-height: 1.4;
        max-height: 2.8rem;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .ki-chat-history-delete-btn {
        position: absolute;
        top: 0.5rem;
        right: 0.5rem;
        background: none;
        border: none;
        font-size: 0.9rem;
        cursor: pointer;
        color: var(--text-muted);
        padding: 0.25rem;
        border-radius: 4px;
        opacity: 0;
        transition: all 0.2s;
      }

      .ki-chat-history-entry:hover .ki-chat-history-delete-btn {
        opacity: 1;
      }

      .ki-chat-history-delete-btn:hover {
        background: var(--background-modifier-error);
        color: var(--text-on-accent);
      }
    `;
    document.head.append(style);
  }

  async destroy() {
    // Speichere aktuelle Sitzung vor dem Schließen
    if (this.currentSession && this.chatStorage.settings.autoSave) {
      await this.saveCurrentSession();
    }
    
    // Cleanup
    this.messages = [];
    this.currentSession = null;
  }
}