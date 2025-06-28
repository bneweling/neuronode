import { ApiClient } from '../api/ApiClient';

export interface DocumentAnalysis {
  filename: string;
  file_type: string;
  predicted_document_type: string;
  preview_text: string;
  file_size_bytes: number;
  word_count: number;
  processing_estimate: {
    estimated_duration_seconds: number;
    estimated_chunks: number;
    will_extract_controls: boolean;
    processing_steps: string[];
  };
  confidence_indicators: {
    type_detection: string;
    classification: string;
  };
}

export interface ProcessingStatus {
  task_id: string;
  status: string;
  progress: number;
  steps_completed: string[];
  current_step: string;
  estimated_completion: string;
}

export class DocumentUploadInterface {
  private container: HTMLElement;
  private apiClient: ApiClient;
  private currentAnalysis: DocumentAnalysis | null = null;
  private uploadInProgress = false;

  constructor(container: HTMLElement, apiClient: ApiClient) {
    this.container = container;
    this.apiClient = apiClient;
    this.render();
  }

  private render() {
    this.container.innerHTML = `
      <div class="ki-upload-interface">
        <div class="ki-upload-header">
          <h3>📄 Dokument-Upload mit Transparenz</h3>
          <p>Verstehen Sie, wie Ihr Dokument verarbeitet wird</p>
        </div>
        
        <div class="ki-upload-zone" id="upload-zone">
          <div class="ki-upload-prompt">
            <div class="ki-upload-icon">📁</div>
            <p><strong>Datei hier ablegen oder klicken zum Auswählen</strong></p>
            <p class="ki-upload-hint">Unterstützt: PDF, Word, Excel, PowerPoint, Text, XML</p>
          </div>
          <input type="file" id="file-input" style="display: none;" 
                 accept=".pdf,.docx,.xlsx,.pptx,.txt,.xml">
        </div>

        <div class="ki-analysis-panel" id="analysis-panel" style="display: none;">
          <h4>🔍 Dokument-Analyse</h4>
          <div class="ki-analysis-content" id="analysis-content"></div>
          
          <div class="ki-upload-actions">
            <button id="upload-btn" class="ki-btn-primary" disabled>
              🚀 Verarbeitung starten
            </button>
            <button id="cancel-btn" class="ki-btn-secondary">
              ❌ Abbrechen
            </button>
          </div>
        </div>

        <div class="ki-progress-panel" id="progress-panel" style="display: none;">
          <h4>⚙️ Verarbeitung läuft...</h4>
          <div class="ki-progress-content" id="progress-content"></div>
        </div>

        <div class="ki-results-panel" id="results-panel" style="display: none;">
          <h4>✅ Verarbeitung abgeschlossen</h4>
          <div class="ki-results-content" id="results-content"></div>
        </div>
      </div>
    `;

    this.setupEventListeners();
  }

  private setupEventListeners() {
    const uploadZone = this.container.querySelector('#upload-zone') as HTMLElement;
    const fileInput = this.container.querySelector('#file-input') as HTMLInputElement;
    const uploadBtn = this.container.querySelector('#upload-btn') as HTMLButtonElement;
    const cancelBtn = this.container.querySelector('#cancel-btn') as HTMLButtonElement;

    // Drag & Drop
    uploadZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadZone.classList.add('ki-drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
      uploadZone.classList.remove('ki-drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadZone.classList.remove('ki-drag-over');
      
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        this.handleFileSelection(files[0]);
      }
    });

    // Click to select
    uploadZone.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
      const files = (e.target as HTMLInputElement).files;
      if (files && files.length > 0) {
        this.handleFileSelection(files[0]);
      }
    });

    // Action buttons
    uploadBtn.addEventListener('click', () => {
      this.startProcessing();
    });

    cancelBtn.addEventListener('click', () => {
      this.resetInterface();
    });
  }

  private async handleFileSelection(file: File) {
    if (this.uploadInProgress) return;

    try {
      // Zeige Loading-State
      this.showAnalysisPanel();
      this.setAnalysisContent(`
        <div class="ki-loading">
          <div class="ki-spinner"></div>
          <p>Analysiere Dokument...</p>
        </div>
      `);

      // Analysiere Dokument
      const analysis = await this.apiClient.analyzeDocumentPreview(file);
      this.currentAnalysis = analysis;
      
      // Zeige Analyse-Ergebnisse
      this.displayAnalysis(analysis);
      
      // Aktiviere Upload-Button
      const uploadBtn = this.container.querySelector('#upload-btn') as HTMLButtonElement;
      uploadBtn.disabled = false;

    } catch (error) {
      this.showError(`Fehler bei der Dokumentanalyse: ${error.message}`);
    }
  }

  private displayAnalysis(analysis: DocumentAnalysis) {
    const confidence = this.getOverallConfidence(analysis);
    const confidenceColor = confidence >= 0.8 ? 'green' : confidence >= 0.6 ? 'orange' : 'red';
    
    this.setAnalysisContent(`
      <div class="ki-analysis-grid">
        <div class="ki-analysis-item">
          <strong>📄 Dateiname:</strong>
          <span>${analysis.filename}</span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>📊 Dateityp:</strong>
          <span class="ki-badge ki-badge-${analysis.confidence_indicators.type_detection}">
            ${analysis.file_type.toUpperCase()}
            <span class="ki-confidence">${analysis.confidence_indicators.type_detection}</span>
          </span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>🎯 Dokumenttyp:</strong>
          <span class="ki-badge ki-badge-${analysis.confidence_indicators.classification}">
            ${this.getDocumentTypeLabel(analysis.predicted_document_type)}
            <span class="ki-confidence">${analysis.confidence_indicators.classification}</span>
          </span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>📏 Größe:</strong>
          <span>${this.formatFileSize(analysis.file_size_bytes)} (${analysis.word_count.toLocaleString()} Wörter)</span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>⏱️ Geschätzte Dauer:</strong>
          <span>${this.formatDuration(analysis.processing_estimate.estimated_duration_seconds)}</span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>🧩 Erwartete Chunks:</strong>
          <span>${analysis.processing_estimate.estimated_chunks}</span>
        </div>
        
        <div class="ki-analysis-item">
          <strong>🎛️ Control-Extraktion:</strong>
          <span class="ki-badge ${analysis.processing_estimate.will_extract_controls ? 'ki-badge-success' : 'ki-badge-info'}">
            ${analysis.processing_estimate.will_extract_controls ? '✅ Ja' : '📝 Nein'}
          </span>
        </div>
      </div>
      
      <div class="ki-preview-section">
        <h5>👀 Dokumentvorschau:</h5>
        <div class="ki-preview-text">${this.escapeHtml(analysis.preview_text.substring(0, 500))}${analysis.preview_text.length > 500 ? '...' : ''}</div>
      </div>
      
      <div class="ki-steps-section">
        <h5>🔄 Verarbeitungsschritte:</h5>
        <ol class="ki-processing-steps">
          ${analysis.processing_estimate.processing_steps.map(step => 
            `<li class="ki-step">${step}</li>`
          ).join('')}
        </ol>
      </div>
      
      <div class="ki-confidence-overall">
        <strong>🎯 Gesamtbewertung:</strong>
        <span class="ki-confidence-bar">
          <div class="ki-confidence-fill" style="width: ${confidence * 100}%; background-color: ${confidenceColor};"></div>
          <span class="ki-confidence-text">${Math.round(confidence * 100)}% Konfidenz</span>
        </span>
      </div>
    `);
  }

  private async startProcessing() {
    if (!this.currentAnalysis || this.uploadInProgress) return;

    this.uploadInProgress = true;
    
    try {
      // Hole File-Input
      const fileInput = this.container.querySelector('#file-input') as HTMLInputElement;
      const file = fileInput.files?.[0];
      
      if (!file) {
        throw new Error('Keine Datei ausgewählt');
      }

      // Verstecke Analyse-Panel, zeige Progress-Panel
      this.hideAnalysisPanel();
      this.showProgressPanel();

      // Starte Upload
      const uploadResult = await this.apiClient.uploadDocument(file, {
        validate: true
      });

      if (uploadResult.status === 'processing') {
        // Überwache Fortschritt
        await this.monitorProgress(uploadResult.task_id);
      } else if (uploadResult.status === 'completed') {
        // Direkt abgeschlossen
        this.showResults(uploadResult);
      }

    } catch (error) {
      this.showError(`Fehler beim Upload: ${error.message}`);
    } finally {
      this.uploadInProgress = false;
    }
  }

  private async monitorProgress(taskId: string) {
    const maxAttempts = 60; // 5 Minuten bei 5s Intervall
    let attempts = 0;

    const checkProgress = async () => {
      try {
        const status = await this.apiClient.getProcessingStatus(taskId);
        this.updateProgressDisplay(status);

        if (status.status === 'completed') {
          this.showResults(status);
          return;
        } else if (status.status === 'failed') {
          throw new Error('Verarbeitung fehlgeschlagen');
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkProgress, 5000); // 5 Sekunden warten
        } else {
          throw new Error('Timeout bei der Verarbeitung');
        }

      } catch (error) {
        this.showError(`Fehler bei der Fortschrittsüberwachung: ${error.message}`);
      }
    };

    checkProgress();
  }

  private updateProgressDisplay(status: ProcessingStatus) {
    const progressContent = this.container.querySelector('#progress-content') as HTMLElement;
    
    progressContent.innerHTML = `
      <div class="ki-progress-bar">
        <div class="ki-progress-fill" style="width: ${status.progress * 100}%"></div>
        <span class="ki-progress-text">${Math.round(status.progress * 100)}%</span>
      </div>
      
      <div class="ki-current-step">
        <strong>Aktueller Schritt:</strong> ${status.current_step}
      </div>
      
      <div class="ki-completed-steps">
        <h5>✅ Abgeschlossene Schritte:</h5>
        <ul>
          ${status.steps_completed.map(step => `<li class="ki-completed">${step}</li>`).join('')}
        </ul>
      </div>
      
      <div class="ki-eta">
        <strong>Voraussichtlicher Abschluss:</strong> ${new Date(status.estimated_completion).toLocaleTimeString()}
      </div>
    `;
  }

  private showResults(result: any) {
    this.hideProgressPanel();
    this.showResultsPanel();
    
    const resultsContent = this.container.querySelector('#results-content') as HTMLElement;
    
    resultsContent.innerHTML = `
      <div class="ki-results-summary">
        <div class="ki-result-item">
          <strong>📄 Dokument:</strong> ${result.filename}
        </div>
        <div class="ki-result-item">
          <strong>📊 Typ:</strong> ${this.getDocumentTypeLabel(result.document_type)}
        </div>
        <div class="ki-result-item">
          <strong>🎛️ Controls extrahiert:</strong> ${result.num_controls || 0}
        </div>
        <div class="ki-result-item">
          <strong>🧩 Chunks erstellt:</strong> ${result.num_chunks || 0}
        </div>
      </div>
      
      <div class="ki-next-steps">
        <h5>🚀 Nächste Schritte:</h5>
        <ul>
          <li>Dokument ist jetzt im Wissensgraph verfügbar</li>
          <li>Stellen Sie Fragen im Chat-Interface</li>
          <li>Erkunden Sie Verbindungen im Graph-View</li>
          <li>Überprüfen Sie extrahierte Controls</li>
        </ul>
      </div>
      
      <div class="ki-result-actions">
        <button id="view-graph-btn" class="ki-btn-primary">📊 Graph anzeigen</button>
        <button id="new-upload-btn" class="ki-btn-secondary">📄 Neues Dokument</button>
      </div>
    `;

    // Event Listeners für Result-Actions
    const viewGraphBtn = resultsContent.querySelector('#view-graph-btn') as HTMLButtonElement;
    const newUploadBtn = resultsContent.querySelector('#new-upload-btn') as HTMLButtonElement;

    viewGraphBtn?.addEventListener('click', () => {
      // Trigger Graph-View öffnen
      this.container.dispatchEvent(new CustomEvent('openGraphView'));
    });

    newUploadBtn?.addEventListener('click', () => {
      this.resetInterface();
    });
  }

  // Hilfsmethoden
  private getOverallConfidence(analysis: DocumentAnalysis): number {
    const typeConf = analysis.confidence_indicators.type_detection === 'high' ? 0.9 : 
                    analysis.confidence_indicators.type_detection === 'medium' ? 0.7 : 0.5;
    const classConf = analysis.confidence_indicators.classification === 'high' ? 0.9 :
                     analysis.confidence_indicators.classification === 'medium' ? 0.7 : 0.5;
    return (typeConf + classConf) / 2;
  }

  private getDocumentTypeLabel(type: string): string {
    const labels = {
      'bsi_grundschutz': 'BSI IT-Grundschutz',
      'bsi_c5': 'BSI C5 Cloud',
      'iso_27001': 'ISO 27001',
      'nist_csf': 'NIST Cybersecurity Framework',
      'whitepaper': 'Technisches Whitepaper',
      'technical_doc': 'Technische Dokumentation',
      'faq': 'FAQ Dokument',
      'unknown': 'Unbekannter Typ'
    };
    return labels[type] || type;
  }

  private formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }

  private formatDuration(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Panel-Management
  private showAnalysisPanel() {
    const panel = this.container.querySelector('#analysis-panel') as HTMLElement;
    panel.style.display = 'block';
  }

  private hideAnalysisPanel() {
    const panel = this.container.querySelector('#analysis-panel') as HTMLElement;
    panel.style.display = 'none';
  }

  private showProgressPanel() {
    const panel = this.container.querySelector('#progress-panel') as HTMLElement;
    panel.style.display = 'block';
  }

  private hideProgressPanel() {
    const panel = this.container.querySelector('#progress-panel') as HTMLElement;
    panel.style.display = 'none';
  }

  private showResultsPanel() {
    const panel = this.container.querySelector('#results-panel') as HTMLElement;
    panel.style.display = 'block';
  }

  private setAnalysisContent(html: string) {
    const content = this.container.querySelector('#analysis-content') as HTMLElement;
    content.innerHTML = html;
  }

  private showError(message: string) {
    this.setAnalysisContent(`
      <div class="ki-error">
        <div class="ki-error-icon">❌</div>
        <div class="ki-error-message">${message}</div>
      </div>
    `);
  }

  private resetInterface() {
    this.currentAnalysis = null;
    this.uploadInProgress = false;
    
    // Verstecke alle Panels außer Upload-Zone
    this.hideAnalysisPanel();
    this.hideProgressPanel();
    const resultsPanel = this.container.querySelector('#results-panel') as HTMLElement;
    resultsPanel.style.display = 'none';
    
    // Reset File-Input
    const fileInput = this.container.querySelector('#file-input') as HTMLInputElement;
    fileInput.value = '';
    
    // Reset Upload-Button
    const uploadBtn = this.container.querySelector('#upload-btn') as HTMLButtonElement;
    uploadBtn.disabled = true;
  }
} 