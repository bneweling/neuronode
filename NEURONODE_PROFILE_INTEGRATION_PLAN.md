# 🎯 NEURONODE LITELLM PROFILE-ROUTING INTEGRATION PLAN

## 📋 EXECUTIVE SUMMARY

**Ziel:** Integration von Model-Profilen direkt in das LiteLLM routing_strategy System mit **Custom Routing Strategy** und **model_group_alias**.

**Ansatz:** Nutze LiteLLM's native **Custom Routing Strategy** + **model_group_alias** Features für Profile-basierte Model-Zuordnung.

**Status:** **SOFORTIGE IMPLEMENTIERUNG MÖGLICH** - nutzt vorhandene LiteLLM Features!

---

## 🔍 LITELLM DOKUMENTATIONS-ANALYSE

### ✅ **Verfügbare Routing Strategies (aus Dokumentation)**
```yaml
router_settings:
  routing_strategy: 
    - "simple-shuffle" (default)
    - "least-busy" 
    - "usage-based-routing"
    - "latency-based-routing"
    - "usage-based-routing-v2"
    - "custom"  # 🎯 LÖSUNG GEFUNDEN!
```

### ✅ **model_group_alias Feature (SCHLÜSSEL!)**
```yaml
router_settings:
  model_group_alias: {"gpt-4": "gpt-4o"}  # Alle gpt-4 Requests → gpt-4o
```

### ✅ **routing_strategy_args für Custom Logic**
```yaml
router_settings:
  routing_strategy_args: {"profile": "premium"}
```

---

## 🚀 IMPLEMENTIERUNGSSTRATEGIE (DOKUMENTATIONS-BASIERT)

### **LÖSUNG: model_group_alias für Profile-Mapping**

**Konzept:** Jedes Profil definiert Task-Aliases die zu konkreten Smart-Aliases gemappt werden.

```yaml
# litellm_config.yaml - PRODUCTION READY LÖSUNG
router_settings:
  routing_strategy: "simple-shuffle"  # Behalten für Performance
  
  # PROFILE-BASIERTE MODEL GROUP ALIASES
  model_group_alias:
    # PREMIUM PROFILE
    "classification": "classification_premium"
    "extraction": "extraction_premium"  
    "synthesis": "synthesis_premium"
    "validation_primary": "validation_primary_premium"
    "validation_secondary": "validation_secondary_premium"
    
    # TASK-BASIERTE FALLBACKS (wenn Profile nicht explizit gesetzt)
    "task_classification": "classification_balanced"
    "task_extraction": "extraction_balanced"
    "task_synthesis": "synthesis_balanced"
```

### **PROFILE-SWITCHING VIA CONFIG UPDATE**

**Admin Workflow:**
1. **Profile wählen** in LiteLLM UI Admin Settings
2. **model_group_alias wird automatisch aktualisiert**
3. **Alle Task-Requests werden zu Profile-Modellen geroutet**
4. **Sofort wirksam ohne Restart**

---

## 🛠️ TECHNISCHE IMPLEMENTIERUNG

### **Phase 1: Custom Profile Router (SOFORT)**

#### 1.1 Enhanced litellm_config.yaml
```yaml
# PRODUKTIONS-KONFIGURATION mit Profile-Support
model_list:
  # Alle 25 Smart-Alias Modelle bleiben unverändert
  - model_name: "classification_premium"
    litellm_params:
      model: "openai/gpt-4o"
      api_key: "os.environ/OPENAI_API_KEY"
      
  - model_name: "classification_balanced"  
    litellm_params:
      model: "gemini/gemini-1.5-pro-latest"
      api_key: "os.environ/GEMINI_API_KEY"
      
  # ... alle anderen 23 Modelle

router_settings:
  routing_strategy: "simple-shuffle"
  
  # 🎯 PROFILE-SYSTEM via model_group_alias
  model_group_alias:
    # DYNAMIC PROFILE MAPPING (wird via API geändert)
    "classification": "classification_premium"     # Aktuelles Profile: premium
    "extraction": "extraction_premium"
    "synthesis": "synthesis_premium" 
    "validation_primary": "validation_primary_premium"
    "validation_secondary": "validation_secondary_premium"
    
  # PERFORMANCE OPTIMIERUNG
  num_retries: 2
  timeout: 30
  enable_pre_call_checks: true
  
# PROFILE METADATA (für UI)
profile_settings:
  current_profile: "premium"
  available_profiles:
    premium:
      cost_level: "high"
      performance_level: "maximum"
      description: "Beste Modelle für Production"
    balanced:
      cost_level: "medium" 
      performance_level: "high"
      description: "Ausgewogene Performance und Kosten"
    cost_effective:
      cost_level: "low"
      performance_level: "good"
      description: "Budget-optimiert"
    specialized:
      cost_level: "medium"
      performance_level: "high"  
      description: "Spezialisierte Tasks"
    ultra_fast:
      cost_level: "low"
      performance_level: "good"
      description: "Maximale Geschwindigkeit"
```

#### 1.2 Profile-Switching API Implementation
```python
# LiteLLM Admin API Extension
class ProfileManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.profiles = {
            "premium": {
                "classification": "classification_premium",
                "extraction": "extraction_premium", 
                "synthesis": "synthesis_premium",
                "validation_primary": "validation_primary_premium",
                "validation_secondary": "validation_secondary_premium"
            },
            "balanced": {
                "classification": "classification_balanced",
                "extraction": "extraction_balanced",
                "synthesis": "synthesis_balanced", 
                "validation_primary": "validation_primary_balanced",
                "validation_secondary": "validation_secondary_balanced"
            },
            "cost_effective": {
                "classification": "classification_cost_effective",
                "extraction": "extraction_cost_effective",
                "synthesis": "synthesis_cost_effective",
                "validation_primary": "validation_primary_cost_effective", 
                "validation_secondary": "validation_secondary_cost_effective"
            },
            "specialized": {
                "classification": "classification_specialized",
                "extraction": "extraction_specialized",
                "synthesis": "synthesis_specialized",
                "validation_primary": "validation_primary_specialized",
                "validation_secondary": "validation_secondary_specialized"
            },
            "ultra_fast": {
                "classification": "classification_ultra_fast",
                "extraction": "extraction_ultra_fast",
                "synthesis": "synthesis_ultra_fast",
                "validation_primary": "validation_primary_ultra_fast",
                "validation_secondary": "validation_secondary_ultra_fast"
            }
        }
    
    def switch_profile(self, profile_name: str) -> bool:
        """Wechselt Profil durch Aktualisierung der model_group_alias"""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
            
        # Lade aktuelle Konfiguration
        config = self.load_config()
        
        # Update model_group_alias für neues Profil
        config['router_settings']['model_group_alias'] = self.profiles[profile_name]
        config['profile_settings']['current_profile'] = profile_name
        
        # Speichere Konfiguration
        self.save_config(config)
        
        # Reload LiteLLM Router (Hot-Reload)
        self.reload_router()
        
        return True
    
    def get_current_profile(self) -> dict:
        """Gibt aktuelles Profil mit Status zurück"""
        config = self.load_config()
        current_profile = config.get('profile_settings', {}).get('current_profile', 'premium')
        
        return {
            "active_profile": current_profile,
            "active_mappings": config.get('router_settings', {}).get('model_group_alias', {}),
            "profile_metadata": config.get('profile_settings', {}).get('available_profiles', {}).get(current_profile, {})
        }
```

---

### **Phase 2: LiteLLM UI Integration**

#### 2.1 Admin UI Profile-Dashboard
```javascript
// LiteLLM UI Extension - Profile Management
class ProfileDashboard extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            currentProfile: 'premium',
            availableProfiles: ['premium', 'balanced', 'cost_effective', 'specialized', 'ultra_fast'],
            activeModels: {},
            profileMetadata: {}
        };
    }
    
    async switchProfile(newProfile) {
        try {
            // API Call zu Profile Manager
            const response = await fetch('/admin/profiles/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: newProfile })
            });
            
            if (response.ok) {
                // Update UI State
                this.setState({ currentProfile: newProfile });
                await this.loadProfileStatus();
                this.showSuccessMessage(`Profile switched to ${newProfile}`);
            }
        } catch (error) {
            this.showErrorMessage(`Failed to switch profile: ${error.message}`);
        }
    }
    
    render() {
        return (
            <div className="profile-dashboard">
                <h2>🎯 Model Profile Management</h2>
                
                {/* Profile Selector */}
                <div className="profile-selector">
                    <label>Active Profile:</label>
                    <select 
                        value={this.state.currentProfile}
                        onChange={(e) => this.switchProfile(e.target.value)}
                    >
                        {this.state.availableProfiles.map(profile => (
                            <option key={profile} value={profile}>
                                {profile.charAt(0).toUpperCase() + profile.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>
                
                {/* Active Models Display */}
                <div className="active-models">
                    <h3>Active Model Mappings:</h3>
                    {Object.entries(this.state.activeModels).map(([task, model]) => (
                        <div key={task} className="model-mapping">
                            <span className="task">{task}</span>
                            <span className="arrow">→</span>
                            <span className="model">{model}</span>
                            <button onClick={() => this.editModelAssignment(task, model)}>
                                Edit
                            </button>
                        </div>
                    ))}
                </div>
                
                {/* Profile Metadata */}
                <div className="profile-info">
                    <div className="cost-level">
                        Cost: {this.state.profileMetadata.cost_level}
                    </div>
                    <div className="performance-level">
                        Performance: {this.state.profileMetadata.performance_level}
                    </div>
                </div>
            </div>
        );
    }
}
```

#### 2.2 Router Settings Integration
```yaml
# UI Integration in bestehende Router Settings
router_settings:
  routing_strategy: simple-shuffle
  
  # ERWEITERT: Profile-Management UI
  profile_management:
    enabled: true
    ui_integration: true
    api_endpoints:
      switch_profile: "/admin/profiles/switch"
      get_status: "/admin/profiles/status"
      list_profiles: "/admin/profiles/list"
  
  # BESTEHEND: model_group_alias (wird dynamisch aktualisiert)
  model_group_alias:
    classification: "classification_premium"
    extraction: "extraction_premium"
    synthesis: "synthesis_premium"
    validation_primary: "validation_primary_premium"
    validation_secondary: "validation_secondary_premium"
```

---

### **Phase 3: Backend Integration**

#### 3.1 Neuronode Backend Anpassung (MINIMAL)
```python
# src/llm/litellm_client.py - Einzige nötige Änderung
class LiteLLMClient:
    def __init__(self):
        self.base_url = settings.litellm_proxy_url
        
    async def completion(self, task_type: str, messages: list, **kwargs):
        """
        Nutzt Task-Aliases statt Smart-Aliases
        LiteLLM routing_alias mapped automatisch zu aktuellem Profil
        """
        # ÄNDERUNG: Nutze Task-Alias statt Smart-Alias
        # Beispiel: "classification" statt "classification_premium"
        model_alias = self.get_task_alias(task_type)
        
        response = await litellm.acompletion(
            model=model_alias,  # z.B. "classification" 
            messages=messages,
            base_url=self.base_url,
            **kwargs
        )
        
        return response
    
    def get_task_alias(self, task_type: TaskType) -> str:
        """Mapped TaskType zu Task-Alias für LiteLLM routing"""
        mapping = {
            TaskType.CLASSIFICATION: "classification",
            TaskType.EXTRACTION: "extraction", 
            TaskType.SYNTHESIS: "synthesis",
            TaskType.VALIDATION_PRIMARY: "validation_primary",
            TaskType.VALIDATION_SECONDARY: "validation_secondary"
        }
        return mapping.get(task_type, "classification")
```

---

## 📊 REQUEST-FLOW DIAGRAMM

```
Neuronode Backend Request:
├── Task: "classification"
├── LiteLLM Client call: model="classification"
├── LiteLLM Router: model_group_alias["classification"] = "classification_premium"
├── Smart-Alias Resolution: "classification_premium" → "openai/gpt-4o"
└── OpenAI API Call: model="gpt-4o"

Profile Switch:
├── Admin UI: Switch to "balanced"
├── API Call: POST /admin/profiles/switch {"profile": "balanced"}
├── Update model_group_alias: "classification" → "classification_balanced" 
├── Hot-Reload LiteLLM Router
└── Next Request: "classification" → "classification_balanced" → "gemini/gemini-1.5-pro"
```

---

## 🎯 SOFORTIGE IMPLEMENTIERUNG (OHNE KOMPROMISSE)

### **Step 1: Enhanced litellm_config.yaml (JETZT)**
- ✅ Erweitere bestehende Konfiguration um `model_group_alias`
- ✅ Definiere alle 5 Profile-Mappings
- ✅ Add `profile_settings` für Metadata

### **Step 2: Profile Manager API (HEUTE)**
- ✅ Implementiere `ProfileManager` Klasse
- ✅ Add API Endpoints für Profile-Switching
- ✅ Hot-Reload Funktionalität

### **Step 3: UI Integration (MORGEN)**
- ✅ Erweitere LiteLLM UI um Profile-Dashboard
- ✅ Profile-Selector mit Live-Update
- ✅ Model-Mapping-Visualisierung

### **Step 4: Backend Integration (ÜBERMORGEN)**
- ✅ Minimale Änderung in `LiteLLMClient`
- ✅ Task-Aliases statt Smart-Aliases
- ✅ Testing aller 5 Profile

---

## ✅ ERFOLGSKRITERIEN (MESSBAR)

### **Funktional:**
1. ✅ **Ein-Klick Profile-Switch** in LiteLLM UI
2. ✅ **Sofortige Wirksamkeit** ohne Service-Restart
3. ✅ **Live-Validierung** aller 5×5=25 Kombinationen
4. ✅ **Backward Compatibility** mit bestehenden Smart-Aliases

### **Performance:**
1. ✅ **< 100ms Profile-Switch** Zeit
2. ✅ **Zero-Impact** auf Request-Latenz
3. ✅ **Hot-Reload** ohne Connection-Drops
4. ✅ **Memory-Efficiency** durch Alias-System

### **Enterprise:**
1. ✅ **Audit-Log** für alle Profile-Wechsel
2. ✅ **Cost-Tracking** pro Profile
3. ✅ **Performance-Monitoring** pro Profile
4. ✅ **Team-based Access Control**

---

## 🚀 IMPLEMENTIERUNG STARTET JETZT

**KEINE KOMPROMISSE - VOLLSTÄNDIGE UMSETZUNG:**

**Tag 1:** Enhanced Config + Profile Manager API
**Tag 2:** LiteLLM UI Integration + Dashboard  
**Tag 3:** Backend Integration + Testing
**Tag 4:** Enterprise Features + Documentation

**Status: READY TO IMPLEMENT** 🎯

---

*Plan basiert auf LiteLLM Dokumentation v1.61.20-stable*  
*Implementation: Ohne Kompromisse, Production-Ready* 