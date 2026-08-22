import React, { useState, useEffect } from 'react';
import './playbook-builder.css';

interface Playbook {
  id: number;
  name: string;
  description: string;
  category: string;
  status: string;
  trigger_type: string;
  actions_count: number;
  used_count: number;
  success_rate: number;
  created_at: string;
}

interface PlaybookAction {
  id: string;
  type: string;
  sequence: number;
  config: Record<string, any>;
  condition?: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  actions: PlaybookAction[];
  icon: string;
}

type Tab = 'gallery' | 'builder' | 'templates' | 'performance';

const PLAYBOOK_TEMPLATES: Template[] = [
  {
    id: 'churn-prevention',
    name: 'Churn Prevention',
    description: 'Identify at-risk customers and reach out proactively',
    category: 'retention',
    icon: '🚨',
    actions: [
      {
        id: '1',
        type: 'email',
        sequence: 0,
        config: {
          to_field: '{customer_email}',
          subject_template: 'We miss you, {customer_name}',
          body_template: 'We noticed you haven\'t been active lately...'
        }
      },
      {
        id: '2',
        type: 'slack',
        sequence: 1,
        config: {
          channel: '#churn-alerts',
          message_template: '⚠️ {customer_name} at risk'
        }
      },
      {
        id: '3',
        type: 'task',
        sequence: 2,
        config: {
          title_template: 'Follow up: {customer_name}',
          description_template: 'Customer risk score: {risk_score}'
        }
      }
    ]
  },
  {
    id: 'upsell-opportunity',
    name: 'Upsell Opportunity',
    description: 'Target high-value customers for expansion',
    category: 'growth',
    icon: '📈',
    actions: [
      {
        id: '1',
        type: 'email',
        sequence: 0,
        config: {
          to_field: '{account_owner_email}',
          subject_template: 'Expansion Opportunity: {customer_name}',
          body_template: 'Based on their usage patterns...'
        }
      },
      {
        id: '2',
        type: 'salesforce',
        sequence: 1,
        config: {
          object: 'Opportunity',
          action: 'create',
          field_mapping: {
            'AccountId': '{customer_id}',
            'Amount': '{expansion_value}',
            'StageName': 'Prospecting'
          }
        }
      }
    ]
  },
  {
    id: 'onboarding-success',
    name: 'Onboarding Success',
    description: 'Guide new customers through successful implementation',
    category: 'onboarding',
    icon: '🎯',
    actions: [
      {
        id: '1',
        type: 'email',
        sequence: 0,
        config: {
          to_field: '{customer_email}',
          subject_template: 'Welcome to {product_name}!',
          body_template: 'Let\'s get you set up for success...'
        }
      },
      {
        id: '2',
        type: 'task',
        sequence: 1,
        config: {
          title_template: 'Onboarding call: {customer_name}',
          description_template: 'Schedule training session'
        }
      }
    ]
  },
  {
    id: 'renewal-preparation',
    name: 'Renewal Preparation',
    description: 'Prepare for upcoming customer renewals',
    category: 'renewal',
    icon: '📅',
    actions: [
      {
        id: '1',
        type: 'email',
        sequence: 0,
        config: {
          to_field: '{customer_email}',
          subject_template: 'Your renewal is coming up - {renewal_date}',
          body_template: 'Your contract renews in 30 days...'
        }
      },
      {
        id: '2',
        type: 'salesforce',
        sequence: 1,
        config: {
          object: 'Account',
          action: 'update',
          field_mapping: {
            'Renewal_Status__c': 'Prepare',
            'Next_Renewal_Date__c': '{renewal_date}'
          }
        }
      }
    ]
  }
];

export const PlaybookBuilder: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('gallery');
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const [editing, setEditing] = useState<Playbook | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      // Mock data - replace with actual API call
      const mockPlaybooks: Playbook[] = [
        {
          id: 1,
          name: 'High-Value Churn Alert',
          description: 'Alert team when high-value customers show churn risk',
          category: 'retention',
          status: 'active',
          trigger_type: 'prediction_threshold',
          actions_count: 3,
          used_count: 142,
          success_rate: 0.68,
          created_at: '2026-08-15T00:00:00Z'
        },
        {
          id: 2,
          name: 'Mid-Market Expansion',
          description: 'Target mid-market customers for upsell',
          category: 'growth',
          status: 'active',
          trigger_type: 'segment_match',
          actions_count: 2,
          used_count: 89,
          success_rate: 0.52,
          created_at: '2026-08-10T00:00:00Z'
        }
      ];
      setPlaybooks(mockPlaybooks);
    } catch (error) {
      console.error('Error fetching playbooks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFromTemplate = (template: Template) => {
    const newPlaybook: Playbook = {
      id: Date.now(),
      name: template.name,
      description: template.description,
      category: template.category,
      status: 'draft',
      trigger_type: 'prediction_threshold',
      actions_count: template.actions.length,
      used_count: 0,
      success_rate: 0,
      created_at: new Date().toISOString()
    };
    setEditing(newPlaybook);
    setShowBuilder(true);
  };

  const filteredPlaybooks = filter === 'all'
    ? playbooks
    : playbooks.filter(p => p.category === filter);

  return (
    <div className="playbook-builder">
      <div className="pb-header">
        <div className="pb-title-section">
          <h1>Playbook Builder</h1>
          <p>Create and manage automated workflows for customer success</p>
        </div>
        <button className="pb-btn-primary" onClick={() => setShowBuilder(true)}>
          + New Playbook
        </button>
      </div>

      <div className="pb-tabs">
        <button
          className={`pb-tab ${activeTab === 'gallery' ? 'active' : ''}`}
          onClick={() => setActiveTab('gallery')}
        >
          📚 Playbooks
        </button>
        <button
          className={`pb-tab ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          🎨 Templates
        </button>
        <button
          className={`pb-tab ${activeTab === 'builder' ? 'active' : ''}`}
          onClick={() => setActiveTab('builder')}
          disabled={!editing}
        >
          🛠️ Builder
        </button>
        <button
          className={`pb-tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          📊 Performance
        </button>
      </div>

      {activeTab === 'gallery' && (
        <PlaybookGallery
          playbooks={filteredPlaybooks}
          filter={filter}
          onFilterChange={setFilter}
          onSelect={setSelectedPlaybook}
          selectedPlaybook={selectedPlaybook}
        />
      )}

      {activeTab === 'templates' && (
        <TemplatesSection onSelectTemplate={handleCreateFromTemplate} />
      )}

      {activeTab === 'builder' && editing && (
        <BuilderSection
          playbook={editing}
          onChange={setEditing}
          onSave={() => {
            setPlaybooks([...playbooks, editing]);
            setEditing(null);
            setActiveTab('gallery');
          }}
          onCancel={() => {
            setEditing(null);
            setShowBuilder(false);
          }}
        />
      )}

      {activeTab === 'performance' && selectedPlaybook && (
        <PerformanceSection playbook={selectedPlaybook} />
      )}

      {showBuilder && !editing && (
        <NewPlaybookModal
          onClose={() => setShowBuilder(false)}
          onCreateBlank={() => {
            setEditing({
              id: Date.now(),
              name: 'New Playbook',
              description: '',
              category: 'custom',
              status: 'draft',
              trigger_type: 'prediction_threshold',
              actions_count: 0,
              used_count: 0,
              success_rate: 0,
              created_at: new Date().toISOString()
            });
            setActiveTab('builder');
          }}
          onSelectTemplate={handleCreateFromTemplate}
        />
      )}
    </div>
  );
};

const PlaybookGallery: React.FC<{
  playbooks: Playbook[];
  filter: string;
  onFilterChange: (filter: string) => void;
  onSelect: (playbook: Playbook) => void;
  selectedPlaybook: Playbook | null;
}> = ({ playbooks, filter, onFilterChange, onSelect, selectedPlaybook }) => {
  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      retention: '🛡️',
      growth: '📈',
      onboarding: '🎯',
      renewal: '📅',
      custom: '⚙️'
    };
    return icons[category] || '📌';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'draft': return '#f59e0b';
      case 'archived': return '#9ca3af';
      default: return '#6b7280';
    }
  };

  return (
    <div className="pb-section">
      <div className="pb-section-header">
        <div>
          <h2>Playbooks ({playbooks.length})</h2>
          <p>Pre-configured workflows for common scenarios</p>
        </div>
        <select
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
          className="pb-filter-select"
        >
          <option value="all">All Categories</option>
          <option value="retention">🛡️ Retention</option>
          <option value="growth">📈 Growth</option>
          <option value="onboarding">🎯 Onboarding</option>
          <option value="renewal">📅 Renewal</option>
          <option value="custom">⚙️ Custom</option>
        </select>
      </div>

      {playbooks.length === 0 ? (
        <div className="pb-empty">
          <p>No playbooks yet. Start with a template or create a new one.</p>
        </div>
      ) : (
        <div className="pb-grid">
          {playbooks.map((playbook) => (
            <div
              key={playbook.id}
              className={`pb-card ${selectedPlaybook?.id === playbook.id ? 'selected' : ''}`}
              onClick={() => onSelect(playbook)}
            >
              <div className="pb-card-header">
                <div className="pb-card-title">
                  <span className="pb-category-icon">{getCategoryIcon(playbook.category)}</span>
                  <div>
                    <h3>{playbook.name}</h3>
                    <p>{playbook.description}</p>
                  </div>
                </div>
                <span
                  className="pb-status"
                  style={{ backgroundColor: getStatusColor(playbook.status) }}
                >
                  {playbook.status}
                </span>
              </div>

              <div className="pb-card-metrics">
                <div className="pb-metric">
                  <label>Actions</label>
                  <span>{playbook.actions_count}</span>
                </div>
                <div className="pb-metric">
                  <label>Used</label>
                  <span>{playbook.used_count}</span>
                </div>
                <div className="pb-metric">
                  <label>Success</label>
                  <span>{(playbook.success_rate * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div className="pb-card-footer">
                <button className="pb-btn-secondary">View</button>
                <button className="pb-btn-secondary">Edit</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const TemplatesSection: React.FC<{
  onSelectTemplate: (template: Template) => void;
}> = ({ onSelectTemplate }) => {
  return (
    <div className="pb-section">
      <h2>Playbook Templates</h2>
      <p>Start with pre-built templates and customize for your needs</p>

      <div className="pb-templates-grid">
        {PLAYBOOK_TEMPLATES.map((template) => (
          <div key={template.id} className="pb-template-card">
            <div className="pb-template-icon">{template.icon}</div>
            <h3>{template.name}</h3>
            <p>{template.description}</p>
            <div className="pb-template-actions">
              <span className="pb-template-count">
                {template.actions.length} actions
              </span>
              <button
                className="pb-btn-primary"
                onClick={() => onSelectTemplate(template)}
              >
                Use Template
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const BuilderSection: React.FC<{
  playbook: Playbook;
  onChange: (playbook: Playbook) => void;
  onSave: () => void;
  onCancel: () => void;
}> = ({ playbook, onChange, onSave, onCancel }) => {
  const [actions, setActions] = useState<PlaybookAction[]>([]);
  const [showActionForm, setShowActionForm] = useState(false);

  const addAction = (type: string) => {
    const newAction: PlaybookAction = {
      id: `action-${Date.now()}`,
      type,
      sequence: actions.length,
      config: {}
    };
    setActions([...actions, newAction]);
    setShowActionForm(false);
  };

  const removeAction = (id: string) => {
    setActions(actions.filter(a => a.id !== id));
  };

  const updateAction = (id: string, updates: Partial<PlaybookAction>) => {
    setActions(actions.map(a => a.id === id ? { ...a, ...updates } : a));
  };

  const reorderActions = (fromIndex: number, toIndex: number) => {
    const newActions = [...actions];
    const [removed] = newActions.splice(fromIndex, 1);
    newActions.splice(toIndex, 0, removed);
    setActions(newActions.map((a, i) => ({ ...a, sequence: i })));
  };

  const actionIcons: Record<string, string> = {
    email: '✉️',
    slack: '💬',
    salesforce: '☁️',
    webhook: '🔗',
    task: '✓'
  };

  return (
    <div className="pb-builder">
      <div className="pb-builder-header">
        <div>
          <input
            type="text"
            value={playbook.name}
            onChange={(e) => onChange({ ...playbook, name: e.target.value })}
            placeholder="Playbook name"
            className="pb-builder-title"
          />
          <textarea
            value={playbook.description}
            onChange={(e) => onChange({ ...playbook, description: e.target.value })}
            placeholder="Playbook description"
            className="pb-builder-description"
          />
        </div>
        <div className="pb-builder-actions">
          <button className="pb-btn-secondary" onClick={onCancel}>Cancel</button>
          <button className="pb-btn-primary" onClick={onSave}>Save Playbook</button>
        </div>
      </div>

      <div className="pb-builder-config">
        <div className="pb-config-group">
          <label>Trigger Type</label>
          <select
            value={playbook.trigger_type}
            onChange={(e) => onChange({ ...playbook, trigger_type: e.target.value })}
          >
            <option value="prediction_threshold">Prediction Threshold</option>
            <option value="segment_match">Segment Match</option>
            <option value="time_based">Time Based</option>
            <option value="manual">Manual Trigger</option>
          </select>
        </div>

        <div className="pb-config-group">
          <label>Category</label>
          <select
            value={playbook.category}
            onChange={(e) => onChange({ ...playbook, category: e.target.value })}
          >
            <option value="retention">Retention</option>
            <option value="growth">Growth</option>
            <option value="onboarding">Onboarding</option>
            <option value="renewal">Renewal</option>
            <option value="custom">Custom</option>
          </select>
        </div>
      </div>

      <div className="pb-actions-section">
        <div className="pb-actions-header">
          <h3>Actions</h3>
          {!showActionForm ? (
            <button
              className="pb-btn-secondary"
              onClick={() => setShowActionForm(true)}
            >
              + Add Action
            </button>
          ) : null}
        </div>

        {showActionForm && (
          <div className="pb-action-type-selector">
            {Object.keys(actionIcons).map((type) => (
              <button
                key={type}
                className="pb-action-type-btn"
                onClick={() => addAction(type)}
              >
                <span className="pb-action-icon">{actionIcons[type]}</span>
                <span className="pb-action-label">{type}</span>
              </button>
            ))}
            <button
              className="pb-btn-secondary"
              onClick={() => setShowActionForm(false)}
            >
              Cancel
            </button>
          </div>
        )}

        {actions.length === 0 ? (
          <div className="pb-empty-actions">
            <p>No actions yet. Click "Add Action" to start building.</p>
          </div>
        ) : (
          <div className="pb-actions-list">
            {actions.map((action, index) => (
              <div key={action.id} className="pb-action-item">
                <div className="pb-action-drag">
                  <span className="pb-drag-handle">⋮⋮</span>
                  <span className="pb-action-index">{index + 1}</span>
                </div>

                <div className="pb-action-content">
                  <div className="pb-action-type">
                    <span className="pb-action-icon">{actionIcons[action.type]}</span>
                    <strong>{action.type}</strong>
                  </div>

                  <div className="pb-action-config">
                    {action.type === 'email' && (
                      <div>
                        <input
                          type="text"
                          placeholder="Subject template"
                          value={action.config.subject_template || ''}
                          onChange={(e) =>
                            updateAction(action.id, {
                              config: { ...action.config, subject_template: e.target.value }
                            })
                          }
                        />
                      </div>
                    )}
                    {action.type === 'slack' && (
                      <div>
                        <input
                          type="text"
                          placeholder="Channel"
                          value={action.config.channel || ''}
                          onChange={(e) =>
                            updateAction(action.id, {
                              config: { ...action.config, channel: e.target.value }
                            })
                          }
                        />
                      </div>
                    )}
                    {action.type === 'task' && (
                      <div>
                        <input
                          type="text"
                          placeholder="Task title template"
                          value={action.config.title_template || ''}
                          onChange={(e) =>
                            updateAction(action.id, {
                              config: { ...action.config, title_template: e.target.value }
                            })
                          }
                        />
                      </div>
                    )}
                    <textarea
                      placeholder="Add conditions (optional)"
                      value={action.condition || ''}
                      onChange={(e) =>
                        updateAction(action.id, { condition: e.target.value })
                      }
                    />
                  </div>
                </div>

                <button
                  className="pb-btn-remove"
                  onClick={() => removeAction(action.id)}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const PerformanceSection: React.FC<{ playbook: Playbook }> = ({ playbook }) => {
  const mockExecutions = [
    { date: '2026-08-22', executions: 42, successes: 28, success_rate: 0.67 },
    { date: '2026-08-21', executions: 38, successes: 25, success_rate: 0.66 },
    { date: '2026-08-20', executions: 45, successes: 31, success_rate: 0.69 },
  ];

  return (
    <div className="pb-section">
      <h2>{playbook.name} - Performance</h2>

      <div className="pb-performance-grid">
        <div className="pb-perf-card">
          <h3>Total Executions</h3>
          <div className="pb-perf-metric">{playbook.used_count}</div>
          <p>Playbook has been executed {playbook.used_count} times</p>
        </div>

        <div className="pb-perf-card">
          <h3>Success Rate</h3>
          <div className="pb-perf-metric">{(playbook.success_rate * 100).toFixed(1)}%</div>
          <div className="pb-perf-bar">
            <div
              className="pb-perf-fill"
              style={{ width: `${playbook.success_rate * 100}%` }}
            />
          </div>
        </div>

        <div className="pb-perf-card">
          <h3>Status</h3>
          <div className="pb-perf-metric">{playbook.status}</div>
          <p>Playbook is {playbook.status}</p>
        </div>
      </div>

      <div className="pb-perf-history">
        <h3>Execution History</h3>
        <div className="pb-perf-table">
          <div className="pb-perf-row pb-perf-header">
            <div>Date</div>
            <div>Executions</div>
            <div>Successes</div>
            <div>Success Rate</div>
          </div>
          {mockExecutions.map((exec, i) => (
            <div key={i} className="pb-perf-row">
              <div>{exec.date}</div>
              <div>{exec.executions}</div>
              <div>{exec.successes}</div>
              <div>{(exec.success_rate * 100).toFixed(1)}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const NewPlaybookModal: React.FC<{
  onClose: () => void;
  onCreateBlank: () => void;
  onSelectTemplate: (template: Template) => void;
}> = ({ onClose, onCreateBlank, onSelectTemplate }) => {
  const [mode, setMode] = useState<'choose' | 'templates'>('choose');

  return (
    <div className="pb-modal-overlay" onClick={onClose}>
      <div className="pb-modal" onClick={(e) => e.stopPropagation()}>
        <div className="pb-modal-header">
          <h2>Create New Playbook</h2>
          <button className="pb-close" onClick={onClose}>✕</button>
        </div>

        {mode === 'choose' ? (
          <div className="pb-modal-content">
            <button
              className="pb-modal-choice"
              onClick={() => onCreateBlank()}
            >
              <span className="pb-choice-icon">🎨</span>
              <div>
                <h3>Blank Playbook</h3>
                <p>Start from scratch with full control</p>
              </div>
              <span className="pb-choice-arrow">→</span>
            </button>

            <button
              className="pb-modal-choice"
              onClick={() => setMode('templates')}
            >
              <span className="pb-choice-icon">📚</span>
              <div>
                <h3>Use Template</h3>
                <p>Start with pre-built workflow templates</p>
              </div>
              <span className="pb-choice-arrow">→</span>
            </button>
          </div>
        ) : (
          <div className="pb-modal-templates">
            {PLAYBOOK_TEMPLATES.map((template) => (
              <button
                key={template.id}
                className="pb-modal-template"
                onClick={() => onSelectTemplate(template)}
              >
                <span>{template.icon}</span>
                <h3>{template.name}</h3>
                <p>{template.description}</p>
              </button>
            ))}
            <button
              className="pb-btn-secondary"
              style={{ gridColumn: '1 / -1' }}
              onClick={() => setMode('choose')}
            >
              ← Back
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybookBuilder;
