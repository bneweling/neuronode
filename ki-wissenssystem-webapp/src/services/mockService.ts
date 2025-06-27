/**
 * Mock Service for Demo Mode
 * Provides realistic demo data without backend dependency
 */

import { KIWissenssystemAPI, GraphNodeData, GraphEdgeData } from '@/lib/api'

export class MockAPIService implements KIWissenssystemAPI {
  private simulateDelay = (ms: number = 1000) => 
    new Promise(resolve => setTimeout(resolve, ms))

  async sendMessage(message: string): Promise<{ message: string; metadata?: Record<string, unknown> }> {
    await this.simulateDelay(1500)
    
    // Demo responses based on message content
    const responses = [
      {
        trigger: ['hallo', 'hi', 'guten tag'],
        response: 'Hallo! Ich bin Ihr KI-Assistent im Demo-Modus. Ich kann Ihnen bei Fragen zu IT-Sicherheit, Compliance und Wissensgraph-Navigation helfen. Was möchten Sie wissen?'
      },
      {
        trigger: ['iso 27001', 'iso27001'],
        response: 'ISO 27001 ist ein internationaler Standard für Informationssicherheits-Managementsysteme (ISMS). Er definiert Anforderungen für die Einrichtung, Implementierung, Aufrechterhaltung und kontinuierliche Verbesserung eines ISMS. Möchten Sie mehr über spezielle Controls erfahren?'
      },
      {
        trigger: ['bsi grundschutz', 'grundschutz'],
        response: 'BSI Grundschutz bietet eine Methodik für das Management von Informationssicherheit. Die Grundschutz-Kompendien enthalten über 80 Bausteine mit Standard-Sicherheitsmaßnahmen. Haben Sie Fragen zu einem bestimmten Baustein?'
      },
      {
        trigger: ['nist csf', 'nist cybersecurity framework'],
        response: 'Das NIST Cybersecurity Framework gliedert sich in fünf Kernfunktionen: Identify, Protect, Detect, Respond, Recover. Es bietet einen risikobasierten Ansatz zur Verbesserung der Cybersicherheit. Welche Funktion interessiert Sie?'
      },
      {
        trigger: ['graph', 'wissensgraph', 'knoten', 'verbindungen'],
        response: 'Der Wissensgraph zeigt Beziehungen zwischen Dokumenten, Konzepten und Entitäten. Sie können auf Knoten klicken, um Details zu sehen, oder die Suchfunktion nutzen. Derzeit sind 47 Knoten mit 82 Verbindungen verfügbar.'
      }
    ]

    const lowerMessage = message.toLowerCase()
    const matchedResponse = responses.find(r => 
      r.trigger.some(trigger => lowerMessage.includes(trigger))
    )

    const responseMessage = matchedResponse?.response || `Das ist eine interessante Frage zu "${message}". Im Demo-Modus kann ich Ihnen zeigen, wie das System funktioniert. In der Produktionsversion würde ich auf Ihre echten Dokumente und Datenquellen zugreifen, um eine präzise Antwort zu geben.`

    // Simulate graph metadata for specific triggers
    const isGraphRelevant = ['graph', 'wissensgraph', 'knoten', 'verbindung', 'beziehung', 'struktur', 'zusammenhang'].some(keyword => 
      lowerMessage.includes(keyword)
    )

    return {
      message: responseMessage,
      metadata: {
        graph_relevant: isGraphRelevant,
        graph_confidence: isGraphRelevant ? 0.85 : 0.1,
        suggested_visualization: isGraphRelevant ? "knowledge_graph" : "none"
      }
    }
  }

  async analyzeDocumentPreview(formData: FormData): Promise<{
    predicted_document_type: string
    file_type: string
    preview_text: string
    processing_estimate: {
      estimated_duration_seconds: number
      estimated_chunks: number
      will_extract_controls: boolean
      processing_steps: string[]
    }
    confidence_indicators: {
      type_detection: string
      classification: string
    }
    estimated_processing_time?: string
    estimated_chunk_count?: number
    estimated_control_count?: number
    preview_image?: string
    file_size_mb?: number
    complexity_score?: number
    warnings?: string[]
  }> {
    await this.simulateDelay(1000)
    
    const file = formData.get('file') as File
    if (!file) {
      throw new Error('Keine Datei gefunden')
    }

    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    const fileSizeMB = file.size / 1024 / 1024

    // Simulate document type detection based on filename
    let predictedType = 'GENERAL_DOCUMENT'
    let willExtractControls = false
    let estimatedControls = 0

    if (file.name.toLowerCase().includes('grundschutz') || file.name.toLowerCase().includes('bsi')) {
      predictedType = 'BSI_GRUNDSCHUTZ'
      willExtractControls = true
      estimatedControls = Math.floor(Math.random() * 50) + 20
    } else if (file.name.toLowerCase().includes('iso') && file.name.toLowerCase().includes('27001')) {
      predictedType = 'ISO_27001'
      willExtractControls = true
      estimatedControls = Math.floor(Math.random() * 30) + 15
    } else if (file.name.toLowerCase().includes('nist')) {
      predictedType = 'NIST_CSF'
      willExtractControls = true
      estimatedControls = Math.floor(Math.random() * 40) + 10
    }

    const estimatedChunks = Math.max(1, Math.floor(fileSizeMB * 10))
    const estimatedDuration = Math.max(30, Math.floor(fileSizeMB * 15))

    return {
      predicted_document_type: predictedType,
      file_type: fileExtension || 'unknown',
      preview_text: `Demo-Vorschau für ${file.name}. Dies ist eine Simulation der Dokumentenanalyse. In der Produktionsversion würde hier der echte Dokumenteninhalt analysiert werden.`,
      processing_estimate: {
        estimated_duration_seconds: estimatedDuration,
        estimated_chunks: estimatedChunks,
        will_extract_controls: willExtractControls,
        processing_steps: willExtractControls 
          ? ['Dokumentanalyse', 'Control-Extraktion', 'Strukturierung', 'Graph-Integration']
          : ['Dokumentanalyse', 'Text-Extraktion', 'Chunking', 'Vektorisierung']
      },
      confidence_indicators: {
        type_detection: willExtractControls ? 'high' : 'medium',
        classification: 'demo_mode'
      },
      estimated_processing_time: `${Math.floor(estimatedDuration / 60)}:${(estimatedDuration % 60).toString().padStart(2, '0')} min`,
      estimated_chunk_count: estimatedChunks,
      estimated_control_count: estimatedControls,
      file_size_mb: Math.round(fileSizeMB * 100) / 100,
      complexity_score: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
      warnings: fileSizeMB > 10 ? ['Große Datei - längere Verarbeitungszeit erwartet'] : undefined
    }
  }

  async getProcessingStatus(taskId: string): Promise<{
    task_id: string
    status: string
    progress: number
    steps_completed: string[]
    current_step: string
    estimated_completion: string
    current_operation?: string
    llm_metadata?: {
      model_used?: string
      tokens_processed?: number
      confidence?: number
    }
    processing_start_time?: string
    processing_end_time?: string
  }> {
    await this.simulateDelay(500)
    
    // Simulate progressive processing
    const now = Date.now()
    const taskStartTime = parseInt(taskId.split('_').pop() || '0')
    const elapsedSeconds = Math.floor((now - taskStartTime) / 1000)
    
    let status = 'processing'
    let progress = Math.min(100, Math.floor(elapsedSeconds * 10))
    let currentStep = 'loading'
    let stepsCompleted: string[] = []
    
    if (progress >= 20) {
      stepsCompleted.push('loading')
      currentStep = 'classifying'
    }
    if (progress >= 40) {
      stepsCompleted.push('classifying')
      currentStep = 'extracting'
    }
    if (progress >= 60) {
      stepsCompleted.push('extracting')
      currentStep = 'chunking'
    }
    if (progress >= 80) {
      stepsCompleted.push('chunking')
      currentStep = 'storing'
    }
    if (progress >= 100) {
      stepsCompleted.push('storing')
      currentStep = 'completed'
      status = 'completed'
    }

    return {
      task_id: taskId,
      status,
      progress,
      steps_completed: stepsCompleted,
      current_step: currentStep,
      estimated_completion: status === 'completed' ? 'completed' : `${Math.max(0, 120 - elapsedSeconds)}s`,
      current_operation: status === 'completed' ? undefined : `Demo-${currentStep}`,
      llm_metadata: {
        model_used: 'demo-model',
        tokens_processed: Math.floor(progress * 50),
        confidence: 0.85
      },
      processing_start_time: new Date(taskStartTime).toISOString(),
      processing_end_time: status === 'completed' ? new Date().toISOString() : undefined
    }
  }

  async uploadDocument(formData: FormData): Promise<{ success: boolean; id?: string; status?: string; task_id?: string; filename?: string; document_type?: string; num_chunks?: number; num_controls?: number; metadata?: any; processing_duration?: number; quality_score?: number; extracted_entities?: string[]; graph_nodes_created?: number; graph_relationships_created?: number }> {
    await this.simulateDelay(2000)
    
    const file = formData.get('file') as File
    if (!file) {
      throw new Error('Keine Datei gefunden')
    }

    // Simulate processing
    const documentId = `demo_doc_${Date.now()}`
    const taskId = `task_${Date.now()}`
    
    // Simulate different response types based on file size
    if (file.size > 5 * 1024 * 1024) { // > 5MB
      return {
        success: true,
        id: documentId,
        status: 'processing',
        task_id: taskId,
        filename: file.name
      }
    } else {
      // Small file - immediate processing
      return {
        success: true,
        id: documentId,
        status: 'completed',
        filename: file.name,
        document_type: 'DEMO_DOCUMENT',
        num_chunks: Math.floor(Math.random() * 20) + 5,
        num_controls: Math.floor(Math.random() * 15) + 3,
        metadata: { demo_mode: true },
        processing_duration: Math.random() * 30 + 10,
        quality_score: Math.random() * 0.3 + 0.7,
        extracted_entities: ['Demo Entity 1', 'Demo Entity 2'],
        graph_nodes_created: Math.floor(Math.random() * 10) + 3,
        graph_relationships_created: Math.floor(Math.random() * 15) + 5
      }
    }
  }

  async getKnowledgeGraph(): Promise<{ nodes: GraphNodeData[]; edges: GraphEdgeData[] }> {
    await this.simulateDelay(800)
    
    return {
      nodes: [
        // IT-Security Concepts
        { id: '1', label: 'ISO 27001', type: 'concept', properties: { 
          description: 'Internationaler Standard für ISMS',
          category: 'standard',
          importance: 'high'
        }},
        { id: '2', label: 'BSI Grundschutz', type: 'concept', properties: { 
          description: 'Deutsche IT-Sicherheits-Methodik',
          category: 'standard',
          importance: 'high'
        }},
        { id: '3', label: 'NIST CSF', type: 'concept', properties: { 
          description: 'US Cybersecurity Framework',
          category: 'framework',
          importance: 'medium'
        }},
        
        // Security Controls
        { id: '4', label: 'Zugangskontrollen', type: 'concept', properties: { 
          description: 'Kontrolle von Benutzerzugriffen',
          category: 'control',
          implementation: 'technical'
        }},
        { id: '5', label: 'Kryptographie', type: 'concept', properties: { 
          description: 'Verschlüsselung und Schlüsselmanagement',
          category: 'control',
          implementation: 'technical'
        }},
        { id: '6', label: 'Incident Management', type: 'concept', properties: { 
          description: 'Behandlung von Sicherheitsvorfällen',
          category: 'process',
          implementation: 'organizational'
        }},
        
        // Technologies
        { id: '7', label: 'Cloud Computing', type: 'entity', properties: { 
          description: 'Cloud-basierte IT-Services',
          category: 'technology',
          risk_level: 'medium'
        }},
        { id: '8', label: 'IoT Devices', type: 'entity', properties: { 
          description: 'Internet of Things Geräte',
          category: 'technology',
          risk_level: 'high'
        }},
        { id: '9', label: 'Mobile Devices', type: 'entity', properties: { 
          description: 'Smartphones und Tablets',
          category: 'technology',
          risk_level: 'medium'
        }},
        
        // Documents
        { id: '10', label: 'IT-Sicherheitsrichtlinie', type: 'document', properties: { 
          description: 'Unternehmens-IT-Sicherheitsrichtlinie',
          category: 'policy',
          last_updated: '2024-01-15'
        }},
        { id: '11', label: 'Notfallhandbuch', type: 'document', properties: { 
          description: 'Handbuch für IT-Notfälle',
          category: 'procedure',
          last_updated: '2024-01-10'
        }},
        { id: '12', label: 'Datenschutz-Leitfaden', type: 'document', properties: { 
          description: 'DSGVO-Compliance-Leitfaden',
          category: 'guideline',
          last_updated: '2024-01-08'
        }},
        
        // Vulnerabilities & Threats
        { id: '13', label: 'Phishing', type: 'concept', properties: { 
          description: 'Social Engineering Angriffe',
          category: 'threat',
          severity: 'high'
        }},
        { id: '14', label: 'Ransomware', type: 'concept', properties: { 
          description: 'Verschlüsselungs-Trojaner',
          category: 'threat',
          severity: 'critical'
        }},
        { id: '15', label: 'DDoS Angriffe', type: 'concept', properties: { 
          description: 'Distributed Denial of Service',
          category: 'threat',
          severity: 'medium'
        }}
      ],
      edges: [
        // Standard Relationships
        { id: 'e1', source: '1', target: '4', label: 'requires', weight: 0.9 },
        { id: 'e2', source: '1', target: '5', label: 'requires', weight: 0.8 },
        { id: 'e3', source: '2', target: '4', label: 'implements', weight: 0.9 },
        { id: 'e4', source: '3', target: '6', label: 'includes', weight: 0.7 },
        
        // Technology Controls
        { id: 'e5', source: '4', target: '7', label: 'applies_to', weight: 0.8 },
        { id: 'e6', source: '5', target: '7', label: 'protects', weight: 0.9 },
        { id: 'e7', source: '4', target: '8', label: 'manages', weight: 0.7 },
        { id: 'e8', source: '4', target: '9', label: 'controls', weight: 0.8 },
        
        // Document Relationships
        { id: 'e9', source: '10', target: '1', label: 'implements', weight: 0.9 },
        { id: 'e10', source: '11', target: '6', label: 'defines', weight: 0.8 },
        { id: 'e11', source: '12', target: '1', label: 'supports', weight: 0.6 },
        
        // Threat Relationships
        { id: 'e12', source: '13', target: '4', label: 'targets', weight: 0.7 },
        { id: 'e13', source: '14', target: '5', label: 'bypasses', weight: 0.8 },
        { id: 'e14', source: '15', target: '7', label: 'attacks', weight: 0.9 },
        
        // Cross-references
        { id: 'e15', source: '2', target: '3', label: 'relates_to', weight: 0.5 },
        { id: 'e16', source: '6', target: '11', label: 'documented_in', weight: 0.9 },
        { id: 'e17', source: '8', target: '14', label: 'vulnerable_to', weight: 0.8 }
      ]
    }
  }

  async getSystemStatus(): Promise<{
    status: 'online' | 'offline' | 'maintenance'
    services: Record<string, boolean>
    performance: {
      responseTime: number
      cpuUsage: number
      memoryUsage: number
      activeConnections: number
    }
  }> {
    await this.simulateDelay(500)
    
    return {
      status: 'online',
      services: {
        'API': true,
        'Database': true,
        'Vector Store': true,
        'LLM Service': true,
        'Graph Database': true
      },
      performance: {
        responseTime: Math.round(200 + Math.random() * 300), // 200-500ms
        cpuUsage: Math.round(20 + Math.random() * 30), // 20-50%
        memoryUsage: Math.round(40 + Math.random() * 20), // 40-60%
        activeConnections: Math.round(5 + Math.random() * 15) // 5-20
      }
    }
  }

  // Additional demo methods for extended functionality
  async getDemoStats() {
    return {
      documentsProcessed: 127,
      knowledgeGraphNodes: 15,
      knowledgeGraphEdges: 17,
      totalQueries: 1843,
      averageResponseTime: '1.2s',
      topTopics: [
        'ISO 27001 Controls',
        'Cloud Security',
        'Incident Response',
        'Access Management',
        'Risk Assessment'
      ]
    }
  }

  async getSearchSuggestions(query: string): Promise<string[]> {
    const suggestions = [
      'ISO 27001 Kontrollen',
      'BSI Grundschutz Bausteine',
      'NIST Framework Funktionen',
      'Cloud Security Best Practices',
      'Incident Response Prozess',
      'Zugangskontrollen implementieren',
      'Kryptographie Standards',
      'Risk Assessment Methoden',
      'Compliance Audit Checkliste',
      'Security Awareness Training'
    ]
    
    return suggestions.filter(s => 
      s.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5)
  }
} 