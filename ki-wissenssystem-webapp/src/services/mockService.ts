/**
 * Mock Service for Demo Mode
 * Provides realistic demo data without backend dependency
 */

import { KIWissenssystemAPI, GraphNodeData, GraphEdgeData } from '@/lib/api'

export class MockAPIService implements KIWissenssystemAPI {
  private simulateDelay = (ms: number = 1000) => 
    new Promise(resolve => setTimeout(resolve, ms))

  async sendMessage(message: string): Promise<{ message: string }> {
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

    return {
      message: matchedResponse?.response || `Das ist eine interessante Frage zu "${message}". Im Demo-Modus kann ich Ihnen zeigen, wie das System funktioniert. In der Produktionsversion würde ich auf Ihre echten Dokumente und Datenquellen zugreifen, um eine präzise Antwort zu geben.`
    }
  }

  async uploadDocument(formData: FormData): Promise<{ success: boolean; id?: string }> {
    await this.simulateDelay(2000)
    
    const file = formData.get('file') as File
    if (!file) {
      throw new Error('Keine Datei gefunden')
    }

    // Simulate processing
    const documentId = `demo_doc_${Date.now()}`
    
    return {
      success: true,
      id: documentId
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