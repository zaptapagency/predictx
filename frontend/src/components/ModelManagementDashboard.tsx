import React, { useState, useEffect } from 'react';
import './model-management-dashboard.css';

interface Model {
  id: number;
  name: string;
  model_type: string;
  status: string;
  algorithm: string;
  accuracy: number;
  f1_score: number;
  auc_roc: number;
  features_count: number;
  training_date: string;
  is_drifted: boolean;
  created_at: string;
}

interface Prediction {
  id: number;
  customer_id: string;
  score: number;
  confidence: number;
  risk_level: string;
  recommended_action: string;
  predicted_at: string;
  has_outcome: boolean;
}

interface TrainingRun {
  id: number;
  status: string;
  started: string;
  completed: string;
  duration_seconds: number;
  records: number;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
  };
  error: string;
}

type Tab = 'models' | 'details' | 'predictions' | 'training' | 'features';

export const ModelManagementDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('models');
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [trainingRuns, setTrainingRuns] = useState<TrainingRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    if (selectedModel) {
      fetchPredictions(selectedModel.id);
      fetchTrainingRuns(selectedModel.id);
    }
  }, [selectedModel]);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/predictions/models');
      const data = await response.json();
      setModels(data.models || []);
      if (data.models?.length > 0) {
        setSelectedModel(data.models[0]);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPredictions = async (modelId: number) => {
    try {
      const response = await fetch(`/api/predictions/predictions?model_id=${modelId}&limit=50`);
      const data = await response.json();
      setPredictions(data.predictions || []);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  };

  const fetchTrainingRuns = async (modelId: number) => {
    try {
      const response = await fetch(`/api/predictions/models/${modelId}/training-runs`);
      const data = await response.json();
      setTrainingRuns(data.runs || []);
    } catch (error) {
      console.error('Error fetching training runs:', error);
    }
  };

  const handleTrainModel = async (formData: any) => {
    try {
      const response = await fetch('/api/predictions/models/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        setShowTrainModal(false);
        fetchModels();
      }
    } catch (error) {
      console.error('Error training model:', error);
    }
  };

  const filteredModels = filter === 'all'
    ? models
    : models.filter(m => m.model_type === filter);

  return (
    <div className="model-management-dashboard">
      <div className="mmd-header">
        <div className="mmd-title-section">
          <h1>Model Management</h1>
          <p>Train, monitor, and manage ML models</p>
        </div>
        <button className="mmd-btn-primary" onClick={() => setShowTrainModal(true)}>
          + Train New Model
        </button>
      </div>

      <div className="mmd-tabs">
        <button
          className={`mmd-tab ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          📊 Models
        </button>
        <button
          className={`mmd-tab ${activeTab === 'details' ? 'active' : ''}`}
          onClick={() => setActiveTab('details')}
          disabled={!selectedModel}
        >
          🔍 Details
        </button>
        <button
          className={`mmd-tab ${activeTab === 'predictions' ? 'active' : ''}`}
          onClick={() => setActiveTab('predictions')}
          disabled={!selectedModel}
        >
          🎯 Predictions
        </button>
        <button
          className={`mmd-tab ${activeTab === 'training' ? 'active' : ''}`}
          onClick={() => setActiveTab('training')}
          disabled={!selectedModel}
        >
          🏋️ Training
        </button>
        <button
          className={`mmd-tab ${activeTab === 'features' ? 'active' : ''}`}
          onClick={() => setActiveTab('features')}
          disabled={!selectedModel}
        >
          ✨ Features
        </button>
      </div>

      {activeTab === 'models' && (
        <ModelsSection
          models={filteredModels}
          selectedModel={selectedModel}
          onSelect={setSelectedModel}
          filter={filter}
          onFilterChange={setFilter}
        />
      )}

      {activeTab === 'details' && selectedModel && (
        <DetailsSection model={selectedModel} />
      )}

      {activeTab === 'predictions' && selectedModel && (
        <PredictionsSection predictions={predictions} />
      )}

      {activeTab === 'training' && selectedModel && (
        <TrainingSection runs={trainingRuns} />
      )}

      {activeTab === 'features' && selectedModel && (
        <FeaturesSection model={selectedModel} />
      )}

      {showTrainModal && (
        <TrainModelModal
          onClose={() => setShowTrainModal(false)}
          onSubmit={handleTrainModel}
        />
      )}
    </div>
  );
};

const ModelsSection: React.FC<{
  models: Model[];
  selectedModel: Model | null;
  onSelect: (model: Model) => void;
  filter: string;
  onFilterChange: (filter: string) => void;
}> = ({ models, selectedModel, onSelect, filter, onFilterChange }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'training': return '#f59e0b';
      case 'draft': return '#9ca3af';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return '✅';
      case 'training': return '⏳';
      case 'draft': return '📝';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="mmd-section">
      <div className="mmd-section-header">
        <div>
          <h2>Models ({models.length})</h2>
          <p>View and manage all models</p>
        </div>
        <div className="mmd-filters">
          <select
            value={filter}
            onChange={(e) => onFilterChange(e.target.value)}
            className="mmd-filter-select"
          >
            <option value="all">All Models</option>
            <option value="churn">Churn</option>
            <option value="opportunity">Opportunity</option>
            <option value="expansion">Expansion</option>
            <option value="health">Health</option>
          </select>
        </div>
      </div>

      {models.length === 0 ? (
        <div className="mmd-empty">
          <p>No models yet. Train your first model to get started.</p>
        </div>
      ) : (
        <div className="mmd-grid">
          {models.map((model) => (
            <div
              key={model.id}
              className={`mmd-card ${selectedModel?.id === model.id ? 'selected' : ''}`}
              onClick={() => onSelect(model)}
            >
              <div className="mmd-card-header">
                <div className="mmd-card-title">
                  <span className="mmd-model-type">{model.model_type.toUpperCase()}</span>
                  <h3>{model.name}</h3>
                </div>
                <span
                  className="mmd-status"
                  style={{ backgroundColor: getStatusColor(model.status) }}
                >
                  {getStatusIcon(model.status)} {model.status}
                </span>
              </div>

              <div className="mmd-card-metrics">
                <div className="mmd-metric">
                  <label>Accuracy</label>
                  <div className="mmd-metric-value">
                    <span className="mmd-percent">{(model.accuracy * 100).toFixed(1)}%</span>
                    <div className="mmd-progress-bar">
                      <div
                        className="mmd-progress-fill"
                        style={{ width: `${model.accuracy * 100}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="mmd-metric">
                  <label>F1 Score</label>
                  <span className="mmd-value">{(model.f1_score * 100).toFixed(1)}%</span>
                </div>

                <div className="mmd-metric">
                  <label>AUC-ROC</label>
                  <span className="mmd-value">{(model.auc_roc * 100).toFixed(1)}%</span>
                </div>

                <div className="mmd-metric">
                  <label>Features</label>
                  <span className="mmd-value">{model.features_count}</span>
                </div>
              </div>

              <div className="mmd-card-meta">
                <div>
                  <span className="mmd-label">Algorithm</span>
                  <span className="mmd-value">{model.algorithm}</span>
                </div>
                <div>
                  <span className="mmd-label">Last Trained</span>
                  <span className="mmd-value">{formatDate(model.training_date)}</span>
                </div>
                {model.is_drifted && (
                  <div className="mmd-drift-warning">
                    ⚠️ Drift Detected
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const DetailsSection: React.FC<{ model: Model }> = ({ model }) => {
  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const response = await fetch(`/api/predictions/models/${model.id}`);
        const data = await response.json();
        setDetails(data);
      } catch (error) {
        console.error('Error fetching model details:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchDetails();
  }, [model.id]);

  if (loading) return <div className="mmd-loading">Loading...</div>;
  if (!details) return <div className="mmd-empty">Failed to load details</div>;

  return (
    <div className="mmd-section">
      <h2>Model Details</h2>

      <div className="mmd-details-grid">
        <div className="mmd-details-card">
          <h3>Performance Metrics</h3>
          <div className="mmd-metrics-table">
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Accuracy</span>
              <span className="mmd-metric-val">{(details.performance?.accuracy * 100).toFixed(2)}%</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Precision</span>
              <span className="mmd-metric-val">{(details.performance?.precision * 100).toFixed(2)}%</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Recall</span>
              <span className="mmd-metric-val">{(details.performance?.recall * 100).toFixed(2)}%</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">F1 Score</span>
              <span className="mmd-metric-val">{(details.performance?.f1_score * 100).toFixed(2)}%</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">AUC-ROC</span>
              <span className="mmd-metric-val">{(details.performance?.auc_roc * 100).toFixed(2)}%</span>
            </div>
          </div>
        </div>

        <div className="mmd-details-card">
          <h3>Training Data</h3>
          <div className="mmd-metrics-table">
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Period Start</span>
              <span className="mmd-metric-val">{formatDate(details.training?.start)}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Period End</span>
              <span className="mmd-metric-val">{formatDate(details.training?.end)}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Records Used</span>
              <span className="mmd-metric-val">{details.training?.records?.toLocaleString()}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Training Date</span>
              <span className="mmd-metric-val">{formatDate(details.training?.date)}</span>
            </div>
          </div>
        </div>

        <div className="mmd-details-card">
          <h3>Model Health</h3>
          <div className="mmd-metrics-table">
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Status</span>
              <span className="mmd-metric-val">{details.status}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Is Drifted</span>
              <span className="mmd-metric-val">{details.health?.is_drifted ? '⚠️ Yes' : '✅ No'}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Features Used</span>
              <span className="mmd-metric-val">{details.features?.length || 0}</span>
            </div>
            <div className="mmd-metric-row">
              <span className="mmd-metric-name">Algorithm</span>
              <span className="mmd-metric-val">{details.algorithm}</span>
            </div>
          </div>
        </div>
      </div>

      {details.feature_importance && (
        <div className="mmd-details-card mmd-full-width">
          <h3>Top Features by Importance</h3>
          <div className="mmd-features-list">
            {Object.entries(details.feature_importance)
              .sort((a, b) => Math.abs((b[1] as number) - (a[1] as number)))
              .slice(0, 10)
              .map(([feature, importance]) => (
                <div key={feature} className="mmd-feature-item">
                  <span className="mmd-feature-name">{feature}</span>
                  <div className="mmd-feature-bar">
                    <div
                      className="mmd-feature-fill"
                      style={{ width: `${Math.abs((importance as number) * 100)}%` }}
                    />
                  </div>
                  <span className="mmd-feature-value">{((importance as number) * 100).toFixed(1)}%</span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

const PredictionsSection: React.FC<{ predictions: Prediction[] }> = ({ predictions }) => {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return '#dc2626';
      case 'high': return '#f97316';
      case 'medium': return '#eab308';
      case 'low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  return (
    <div className="mmd-section">
      <h2>Recent Predictions ({predictions.length})</h2>

      {predictions.length === 0 ? (
        <div className="mmd-empty">
          <p>No predictions yet.</p>
        </div>
      ) : (
        <div className="mmd-table-wrapper">
          <table className="mmd-table">
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Score</th>
                <th>Risk Level</th>
                <th>Confidence</th>
                <th>Action</th>
                <th>Outcome</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {predictions.map((pred) => (
                <tr key={pred.id}>
                  <td className="mmd-text-mono">{pred.customer_id}</td>
                  <td>
                    <div className="mmd-score">
                      <span className="mmd-score-val">{(pred.score * 100).toFixed(1)}%</span>
                      <div className="mmd-score-bar">
                        <div
                          className="mmd-score-fill"
                          style={{
                            width: `${pred.score * 100}%`,
                            backgroundColor: getRiskColor(pred.risk_level)
                          }}
                        />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span
                      className="mmd-badge"
                      style={{ backgroundColor: getRiskColor(pred.risk_level) }}
                    >
                      {pred.risk_level}
                    </span>
                  </td>
                  <td>{(pred.confidence * 100).toFixed(0)}%</td>
                  <td><code>{pred.recommended_action}</code></td>
                  <td>{pred.has_outcome ? '✅' : '⏳'}</td>
                  <td className="mmd-text-sm">{formatDate(pred.predicted_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const TrainingSection: React.FC<{ runs: TrainingRun[] }> = ({ runs }) => {
  return (
    <div className="mmd-section">
      <h2>Training History ({runs.length})</h2>

      {runs.length === 0 ? (
        <div className="mmd-empty">
          <p>No training runs yet.</p>
        </div>
      ) : (
        <div className="mmd-training-runs">
          {runs.map((run) => (
            <div key={run.id} className="mmd-training-card">
              <div className="mmd-training-header">
                <div>
                  <h3>Run #{run.id}</h3>
                  <p>{formatDate(run.started)}</p>
                </div>
                <span className={`mmd-status ${run.status}`}>
                  {run.status === 'success' ? '✅' : '❌'} {run.status}
                </span>
              </div>

              <div className="mmd-training-metrics">
                <div>
                  <label>Duration</label>
                  <span>{Math.round(run.duration_seconds)}s</span>
                </div>
                <div>
                  <label>Records</label>
                  <span>{run.records?.toLocaleString()}</span>
                </div>
                <div>
                  <label>Accuracy</label>
                  <span>{(run.metrics?.accuracy * 100).toFixed(2)}%</span>
                </div>
                <div>
                  <label>Precision</label>
                  <span>{(run.metrics?.precision * 100).toFixed(2)}%</span>
                </div>
                <div>
                  <label>Recall</label>
                  <span>{(run.metrics?.recall * 100).toFixed(2)}%</span>
                </div>
                <div>
                  <label>F1 Score</label>
                  <span>{(run.metrics?.f1 * 100).toFixed(2)}%</span>
                </div>
              </div>

              {run.error && (
                <div className="mmd-error">
                  <strong>Error:</strong> {run.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const FeaturesSection: React.FC<{ model: Model }> = ({ model }) => {
  const [features, setFeatures] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeatures = async () => {
      try {
        const response = await fetch('/api/predictions/features');
        const data = await response.json();
        setFeatures(data.features || []);
      } catch (error) {
        console.error('Error fetching features:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchFeatures();
  }, []);

  if (loading) return <div className="mmd-loading">Loading...</div>;

  return (
    <div className="mmd-section">
      <h2>Features Used in Model</h2>

      {features.length === 0 ? (
        <div className="mmd-empty">
          <p>No features available.</p>
        </div>
      ) : (
        <div className="mmd-features-table">
          <div className="mmd-features-header">
            <div className="mmd-col-name">Feature Name</div>
            <div className="mmd-col-type">Type</div>
            <div className="mmd-col-source">Source</div>
            <div className="mmd-col-stats">Statistics</div>
          </div>

          {features.map((feature) => (
            <div key={feature.id} className="mmd-feature-row">
              <div className="mmd-col-name">
                <strong>{feature.name}</strong>
                <p>{feature.description}</p>
              </div>
              <div className="mmd-col-type">
                <span className="mmd-tag">{feature.type}</span>
              </div>
              <div className="mmd-col-source">
                <code>{feature.source}</code>
              </div>
              <div className="mmd-col-stats">
                <div className="mmd-stat-mini">
                  <span className="mmd-stat-label">Mean:</span>
                  <span>{feature.statistics?.mean?.toFixed(2) || '—'}</span>
                </div>
                <div className="mmd-stat-mini">
                  <span className="mmd-stat-label">Median:</span>
                  <span>{feature.statistics?.median?.toFixed(2) || '—'}</span>
                </div>
                <div className="mmd-stat-mini">
                  <span className="mmd-stat-label">Std:</span>
                  <span>{feature.statistics?.std?.toFixed(2) || '—'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const TrainModelModal: React.FC<{
  onClose: () => void;
  onSubmit: (data: any) => void;
}> = ({ onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    model_type: 'churn',
    algorithm: 'xgboost',
    training_start: '',
    training_end: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="mmd-modal-overlay" onClick={onClose}>
      <div className="mmd-modal" onClick={(e) => e.stopPropagation()}>
        <div className="mmd-modal-header">
          <h2>Train New Model</h2>
          <button className="mmd-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} className="mmd-form">
          <div className="mmd-form-group">
            <label>Model Name</label>
            <input
              type="text"
              placeholder="e.g., Churn Risk Model v2"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          <div className="mmd-form-row">
            <div className="mmd-form-group">
              <label>Model Type</label>
              <select
                value={formData.model_type}
                onChange={(e) => setFormData({...formData, model_type: e.target.value})}
              >
                <option value="churn">Churn Risk</option>
                <option value="opportunity">Opportunity</option>
                <option value="expansion">Expansion</option>
                <option value="health">Health Score</option>
              </select>
            </div>

            <div className="mmd-form-group">
              <label>Algorithm</label>
              <select
                value={formData.algorithm}
                onChange={(e) => setFormData({...formData, algorithm: e.target.value})}
              >
                <option value="logistic_regression">Logistic Regression</option>
                <option value="random_forest">Random Forest</option>
                <option value="xgboost">XGBoost</option>
              </select>
            </div>
          </div>

          <div className="mmd-form-row">
            <div className="mmd-form-group">
              <label>Training Start Date</label>
              <input
                type="datetime-local"
                value={formData.training_start}
                onChange={(e) => setFormData({...formData, training_start: e.target.value})}
                required
              />
            </div>

            <div className="mmd-form-group">
              <label>Training End Date</label>
              <input
                type="datetime-local"
                value={formData.training_end}
                onChange={(e) => setFormData({...formData, training_end: e.target.value})}
                required
              />
            </div>
          </div>

          <div className="mmd-modal-footer">
            <button type="button" className="mmd-btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="mmd-btn-primary">
              Start Training
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

export default ModelManagementDashboard;
