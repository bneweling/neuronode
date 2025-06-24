import { 
  App, 
  Plugin, 
  PluginSettingTab, 
  Setting, 
  WorkspaceLeaf,
  Notice
} from 'obsidian';
import { KnowledgeChatView, VIEW_TYPE_KNOWLEDGE_CHAT } from './src/views/KnowledgeChatView';
import { KnowledgeGraphView, VIEW_TYPE_KNOWLEDGE_GRAPH } from './src/views/KnowledgeGraphView';
import { DocumentUploadView, DOCUMENT_UPLOAD_VIEW_TYPE } from './src/views/DocumentUploadView';
import { ApiClient } from './src/api/ApiClient';
import { WebSocketClient } from './src/api/WebSocketClient';

interface KIWissenssystemSettings {
  apiUrl: string;
  wsUrl: string;
  apiKey: string;
  maxContextNodes: number;
  graphDepth: number;
  theme: 'light' | 'dark' | 'auto';
}

const DEFAULT_SETTINGS: KIWissenssystemSettings = {
  apiUrl: 'http://localhost:8080',
  wsUrl: 'ws://localhost:8080/ws/chat',
  apiKey: '',
  maxContextNodes: 10,
  graphDepth: 2,
  theme: 'auto'
}

export default class KIWissenssystemPlugin extends Plugin {
  settings: KIWissenssystemSettings;
  apiClient: ApiClient;
  wsClient: WebSocketClient;

  async onload() {
    await this.loadSettings();

    // Initialize API clients
    this.apiClient = new ApiClient(this.settings.apiUrl, this.settings.apiKey);
    this.wsClient = new WebSocketClient(this.settings.wsUrl);

    // Register views
    this.registerView(
      VIEW_TYPE_KNOWLEDGE_CHAT,
      (leaf) => new KnowledgeChatView(leaf, this)
    );

    this.registerView(
      VIEW_TYPE_KNOWLEDGE_GRAPH,
      (leaf) => new KnowledgeGraphView(leaf, this)
    );

    this.registerView(
      DOCUMENT_UPLOAD_VIEW_TYPE,
      (leaf) => new DocumentUploadView(leaf, this)
    );

    // Add ribbon icons
    this.addRibbonIcon('message-circle', 'KI-Wissenssystem Chat', () => {
      this.activateChatView();
    });

    this.addRibbonIcon('git-branch', 'Knowledge Graph', () => {
      this.activateGraphView();
    });

    this.addRibbonIcon('upload', 'Dokument Upload', () => {
      this.activateUploadView();
    });

    // Add commands
    this.addCommand({
      id: 'open-knowledge-chat',
      name: 'Open Knowledge Chat',
      callback: () => {
        this.activateChatView();
      }
    });

    this.addCommand({
      id: 'open-knowledge-graph',
      name: 'Open Knowledge Graph',
      callback: () => {
        this.activateGraphView();
      }
    });

    this.addCommand({
      id: 'open-document-upload',
      name: 'Open Document Upload',
      callback: () => {
        this.activateUploadView();
      }
    });

    this.addCommand({
      id: 'search-knowledge',
      name: 'Search Knowledge Base',
      callback: () => {
        this.showSearchModal();
      }
    });

    // Add settings tab
    this.addSettingTab(new KIWissenssystemSettingTab(this.app, this));

    // Initialize workspace layouts
    this.app.workspace.onLayoutReady(() => {
      this.initializeDefaultLayout();
    });
  }

  onunload() {
    this.wsClient?.disconnect();
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
    // Update API clients with new settings
    this.apiClient.updateSettings(this.settings.apiUrl, this.settings.apiKey);
    this.wsClient.updateUrl(this.settings.wsUrl);
  }

  async activateChatView() {
    const { workspace } = this.app;
    
    let leaf: WorkspaceLeaf | null = null;
    const leaves = workspace.getLeavesOfType(VIEW_TYPE_KNOWLEDGE_CHAT);
    
    if (leaves.length > 0) {
      leaf = leaves[0];
    } else {
      leaf = workspace.getRightLeaf(false);
      await leaf.setViewState({
        type: VIEW_TYPE_KNOWLEDGE_CHAT,
        active: true,
      });
    }
    
    workspace.revealLeaf(leaf);
  }

  async activateGraphView() {
    const { workspace } = this.app;
    
    let leaf: WorkspaceLeaf | null = null;
    const leaves = workspace.getLeavesOfType(VIEW_TYPE_KNOWLEDGE_GRAPH);
    
    if (leaves.length > 0) {
      leaf = leaves[0];
    } else {
      leaf = workspace.getLeaf('tab');
      if (leaf) {
        await leaf.setViewState({
          type: VIEW_TYPE_KNOWLEDGE_GRAPH,
          active: true,
        });
      }
    }
    
    if (leaf) {
      workspace.revealLeaf(leaf);
    }
  }

  async activateUploadView() {
    const { workspace } = this.app;
    
    let leaf: WorkspaceLeaf | null = null;
    const leaves = workspace.getLeavesOfType(DOCUMENT_UPLOAD_VIEW_TYPE);
    
    if (leaves.length > 0) {
      leaf = leaves[0];
    } else {
      leaf = workspace.getRightLeaf(false);
      await leaf.setViewState({
        type: DOCUMENT_UPLOAD_VIEW_TYPE,
        active: true,
      });
    }
    
    workspace.revealLeaf(leaf);
  }

  async showSearchModal() {
    // Implementation for search modal
    new Notice('Search modal coming soon!');
  }

  initializeDefaultLayout() {
    // Set up default layout if needed
    if (this.settings.theme === 'auto') {
      this.detectAndApplyTheme();
    }
  }

  detectAndApplyTheme() {
    const isDarkMode = document.body.classList.contains('theme-dark');
    // Apply theme to plugin components
  }
}

class KIWissenssystemSettingTab extends PluginSettingTab {
  plugin: KIWissenssystemPlugin;

  constructor(app: App, plugin: KIWissenssystemPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'KI-Wissenssystem Settings' });

    new Setting(containerEl)
      .setName('API URL')
      .setDesc('URL of the KI-Wissenssystem API')
      .addText(text => text
        .setPlaceholder('http://localhost:8080')
        .setValue(this.plugin.settings.apiUrl)
        .onChange(async (value) => {
          this.plugin.settings.apiUrl = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('WebSocket URL')
      .setDesc('WebSocket URL for real-time chat')
      .addText(text => text
        .setPlaceholder('ws://localhost:8080/ws/chat')
        .setValue(this.plugin.settings.wsUrl)
        .onChange(async (value) => {
          this.plugin.settings.wsUrl = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('API Key')
      .setDesc('API authentication key (if required)')
      .addText(text => text
        .setPlaceholder('Enter your API key')
        .setValue(this.plugin.settings.apiKey)
        .onChange(async (value) => {
          this.plugin.settings.apiKey = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Max Context Nodes')
      .setDesc('Maximum number of context nodes to display')
      .addSlider(slider => slider
        .setLimits(5, 50, 5)
        .setValue(this.plugin.settings.maxContextNodes)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.maxContextNodes = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Graph Depth')
      .setDesc('Depth of relationships to show in graph')
      .addSlider(slider => slider
        .setLimits(1, 5, 1)
        .setValue(this.plugin.settings.graphDepth)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.graphDepth = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Theme')
      .setDesc('Color theme for the plugin')
      .addDropdown(dropdown => dropdown
        .addOption('light', 'Light')
        .addOption('dark', 'Dark')
        .addOption('auto', 'Auto')
        .setValue(this.plugin.settings.theme)
        .onChange(async (value: 'light' | 'dark' | 'auto') => {
          this.plugin.settings.theme = value;
          await this.plugin.saveSettings();
        }));
  }
}