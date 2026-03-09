/**
 * PatternShield v2.1 Configuration
 */

const CONFIG = {
  API_URL: 'http://localhost:5000',
  API_ENDPOINTS: {
    ANALYZE: '/analyze',
    BATCH: '/batch/analyze',
    HEALTH: '/health',
    PATTERN_TYPES: '/pattern-types',
    SITE_SCORE: '/site-score',
    FEEDBACK: '/feedback',
    TEMPORAL_RECORD: '/temporal/record',
    TEMPORAL_CHECK: '/temporal/check',
    OFFLINE_RULES: '/offline-rules',
  },

  DETECTION: {
    AUTO_SCAN: true,
    CONFIDENCE_THRESHOLD: 0.35,
    DEBOUNCE_DELAY: 3000,
    MAX_ELEMENTS_PER_SCAN: 200,
    BATCH_SIZE: 20,
    API_RETRY_COOLDOWN_MS: 3 * 60 * 1000, // 3 minutes between backend retries when unavailable
  },

  PATTERNS: {
    'Urgency/Scarcity': {
      color: '#ef4444', label: 'Urgency / Scarcity',
      icon: '⏰', description: 'Creates false sense of urgency or scarcity',
    },
    'Confirmshaming': {
      color: '#f97316', label: 'Confirmshaming',
      icon: '😔', description: 'Uses guilt or shame to manipulate decisions',
    },
    'Obstruction': {
      color: '#eab308', label: 'Obstruction',
      icon: '🚧', description: 'Makes desired actions deliberately difficult',
    },
    'Visual Interference': {
      color: '#a855f7', label: 'Visual Interference',
      icon: '👁️', description: 'Manipulates visual design to steer choices',
    },
    'Hidden Costs': {
      color: '#ec4899', label: 'Hidden Costs',
      icon: '💸', description: 'Reveals fees or charges only at later stages',
    },
    'Forced Continuity': {
      color: '#14b8a6', label: 'Forced Continuity',
      icon: '🔄', description: 'Auto-enrolls in recurring payments or traps after trials',
    },
    'Sneaking': {
      color: '#6366f1', label: 'Sneaking',
      icon: '🕵️', description: 'Adds items or options without clear consent',
    },
    'Social Proof': {
      color: '#f59e0b', label: 'Social Proof',
      icon: '👥', description: 'Uses potentially fake social validation',
    },
    'Misdirection': {
      color: '#10b981', label: 'Misdirection',
      icon: '🎯', description: 'Steers attention toward or away from choices',
    },
    'Price Comparison Prevention': {
      color: '#8b5cf6', label: 'Price Comparison Prevention',
      icon: '🔒', description: 'Makes it hard to compare prices or options',
    },
    'No Pattern': {
      color: '#22c55e', label: 'No Pattern',
      icon: '✅', description: 'Legitimate UI element',
    },
  },

  SEVERITY_COLORS: {
    critical: '#dc2626',
    high:     '#ef4444',
    medium:   '#f97316',
    low:      '#eab308',
    none:     '#22c55e',
  },

  UI: {
    HIGHLIGHT_BORDER_WIDTH: '3px',
    HIGHLIGHT_OPACITY: 0.3,
    POPUP_MAX_RESULTS: 15,
  },

  STORAGE_KEYS: {
    SETTINGS:          'patternshield_settings',
    WHITELIST:         'patternshield_whitelist',
    STATS:             'patternshield_stats',
    OFFLINE_RULES:     'patternshield_offline_rules',
    TEMPORAL_HISTORY:  'patternshield_temporal',
    DISMISSED_PANELS:  'patternshield_dismissed_panels',
  },

  DEFAULT_SETTINGS: {
    autoScan:            true,
    dynamicScan:         true,
    enableTemporal:      true,
    highlightElements:   true,
    showFloatingPanel:   true,
    richTooltips:        true,
    enableFeedback:      true,
    offlineMode:         false,
    cookieAnalysis:      true,
    showNotifications:   true,
    confidenceThreshold: 0.35,
    apiUrl:              'http://localhost:5000',
    enabledPatterns:     {},
  },
};

if (typeof window !== 'undefined') window.CONFIG = CONFIG;
if (typeof module !== 'undefined' && module.exports) module.exports = CONFIG;
