/**
 * PatternShield v2.0 Configuration
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
    DEBOUNCE_DELAY: 1000,
    MAX_ELEMENTS_PER_SCAN: 150,
    BATCH_SIZE: 25,
  },

  PATTERNS: {
    'Urgency/Scarcity': {
      color: '#ef4444', label: 'Urgency/Scarcity',
      icon: '⏰', description: 'Creates false sense of urgency or scarcity'
    },
    'Confirmshaming': {
      color: '#f97316', label: 'Confirmshaming',
      icon: '😔', description: 'Uses guilt or shame to manipulate decisions'
    },
    'Obstruction': {
      color: '#eab308', label: 'Obstruction',
      icon: '🚧', description: 'Makes desired actions difficult to complete'
    },
    'Visual Interference': {
      color: '#a855f7', label: 'Visual Interference',
      icon: '👁️', description: 'Manipulates visual design to steer choices'
    },
    'Hidden Costs': {
      color: '#ec4899', label: 'Hidden Costs',
      icon: '💸', description: 'Reveals fees or charges only at later stages'
    },
    'Forced Continuity': {
      color: '#14b8a6', label: 'Forced Continuity',
      icon: '🔄', description: 'Auto-enrolls in recurring payments or traps after trials'
    },
    'Sneaking': {
      color: '#6366f1', label: 'Sneaking',
      icon: '🕵️', description: 'Adds items or options without clear consent'
    },
    'Social Proof': {
      color: '#f59e0b', label: 'Social Proof',
      icon: '👥', description: 'Uses potentially fake social validation'
    },
    'Misdirection': {
      color: '#10b981', label: 'Misdirection',
      icon: '🎯', description: 'Steers attention toward or away from choices'
    },
    'Price Comparison Prevention': {
      color: '#8b5cf6', label: 'Price Comparison Prevention',
      icon: '🔒', description: 'Makes it hard to compare prices or options'
    },
    'No Pattern': {
      color: '#22c55e', label: 'No Pattern',
      icon: '✅', description: 'Legitimate UI element'
    }
  },

  SEVERITY_COLORS: {
    critical: '#dc2626',
    high: '#ef4444',
    medium: '#f97316',
    low: '#eab308',
    none: '#22c55e',
  },

  UI: {
    HIGHLIGHT_BORDER_WIDTH: '3px',
    HIGHLIGHT_OPACITY: 0.3,
    POPUP_MAX_RESULTS: 15,
  },

  STORAGE_KEYS: {
    SETTINGS: 'patternshield_settings',
    WHITELIST: 'patternshield_whitelist',
    STATS: 'patternshield_stats',
    OFFLINE_RULES: 'patternshield_offline_rules',
    TEMPORAL_HISTORY: 'patternshield_temporal',
  },

  DEFAULT_SETTINGS: {
    autoScan: true,
    confidenceThreshold: 0.35,
    showNotifications: true,
    highlightElements: true,
    apiUrl: 'http://localhost:5000',
    offlineMode: false,
    enableFeedback: true,
    enableTemporal: true,
    enabledPatterns: {
      'Urgency/Scarcity': true,
      'Confirmshaming': true,
      'Obstruction': true,
      'Visual Interference': true,
      'Hidden Costs': true,
      'Forced Continuity': true,
      'Sneaking': true,
      'Social Proof': true,
      'Misdirection': true,
      'Price Comparison Prevention': true,
    },
    highlightStyle: 'outline', // outline, background, badge
  },
};

if (typeof window !== 'undefined') window.CONFIG = CONFIG;
if (typeof module !== 'undefined' && module.exports) module.exports = CONFIG;
