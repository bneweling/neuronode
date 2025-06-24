import { MarkdownRenderer, Component } from 'obsidian';
import KIWissenssystemPlugin from '../../main';
import { Message } from '../types';

export class ChatInterface extends Component {
  private container: HTMLElement;
  private plugin: KIWissenssystemPlugin;
  private messages: Message[] = [];
  private onSendMessage: (message: string) => void;
  private onContextClick: (nodeId: string) => void;
  private inputField: HTMLTextAreaElement;
  private messagesContainer: HTMLElement;
  private suggestionsContainer: HTMLElement;

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
    this.initialize();
  }

  private initialize() {
    // Header
    const header = this.container.createDiv('ki-chat-header');
    header.createEl('h3', { text: 'KI-Assistent' });
    
    const headerActions = header.createDiv('ki-chat-header-actions');
    
    // Clear chat button
    const clearBtn = headerActions.createEl('button', {
      text: 'Chat leeren',
      cls: 'ki-chat-clear-btn'
    });
    clearBtn.addEventListener('click', () => this.clearChat());

    // Messages container
    this.messagesContainer = this.container.createDiv('ki-chat-messages');
    
    // Welcome message
    this.addMessage({
      role: 'assistant',
      content: 'Hallo! Ich bin Ihr KI-Assistent für Compliance und Sicherheit. Wie kann ich Ihnen helfen?',
      timestamp: new Date()
    });

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
    `;
    document.head.append(style);
  }

  destroy() {
    // Cleanup
    this.messages = [];
  }
}