import { ItemView, WorkspaceLeaf } from 'obsidian';
import { DocumentUploadInterface } from '../components/DocumentUploadInterface';
import KIWissenssystemPlugin from '../../main';

export const DOCUMENT_UPLOAD_VIEW_TYPE = 'ki-document-upload';

export class DocumentUploadView extends ItemView {
  plugin: KIWissenssystemPlugin;
  uploadInterface: DocumentUploadInterface | null = null;

  constructor(leaf: WorkspaceLeaf, plugin: KIWissenssystemPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() {
    return DOCUMENT_UPLOAD_VIEW_TYPE;
  }

  getDisplayText() {
    return 'KI: Dokument Upload';
  }

  getIcon() {
    return 'upload';
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    
    // Erstelle Upload-Interface
    this.uploadInterface = new DocumentUploadInterface(
      container as HTMLElement,
      this.plugin.apiClient
    );

    // Event Listener für Graph-View öffnen
    container.addEventListener('openGraphView', () => {
      this.plugin.activateGraphView();
    });

    // Event Listener für Chat-View öffnen  
    container.addEventListener('openChatView', () => {
      this.plugin.activateChatView();
    });
  }

  async onClose() {
    if (this.uploadInterface) {
      this.uploadInterface = null;
    }
  }
} 