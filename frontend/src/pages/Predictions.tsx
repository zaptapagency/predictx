import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/predictions.css';

interface PredictionResult {
  id: number;
  model_name: string;
  input_data: Record<string, number>;
  prediction: number;
  confidence: number;
  latency_ms: number;
  created_at: string;
}

const Predictions: React.FC = () => {
  const navigate = useNavigate();
  const models = ['house_price', 'churn_prediction', 'fraud_detection'];
  const [selectedModel, setSelectedModel] = useState('house_price');
  const [inputData, setInputData] = useState<Record<string, number>>({});
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [history, setHistory] = useState<PredictionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState('predict');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login');
      return;
    }

    fetchHistory();
  }, [navigate]);

  const fetchHistory = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    try {
      const response = await fetch('/api/predictions/history', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setHistory(await response.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getModelFeatures = (model: string): string[] => {
    const features: Record<string, string[]> = {
      house_price: ['square_feet', 'bedrooms', 'bathrooms', 'age', 'location_score'],
      churn_prediction: ['tenure_months', 'monthly_charges', 'total_charges', 'contract_type'],
      fraud_detection: ['transaction_amount', 'merchant_type', 'card_present', 'velocity_score'],
    };
    return features[model] || [];
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const model = e.target.value;
    setSelectedModel(model);
    setInputData({});
    setResult(null);
    const features = getModelFeatures(model);
    const newData: Record<string, number> = {};
    features.forEach(f => (newData[f] = 0));
    setInputData(newData);
  };

  const handleInputChange = (feature: string, value: number) => {
    setInputData(prev => ({
      ...prev,
      [feature]: value,
    }));
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    if (!token) return;

    setLoading(true);
    try {
      const response = await fetch('/api/predictions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          model: selectedModel,
          data: inputData,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        await fetchHistory();
      } else {
        alert('Prediction failed');
      }
    } catch (err) {
      alert('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    const csv = [
      ['Model', 'Prediction', 'Confidence', 'Latency (ms)', 'Date'],
      ...history.map(h => [
        h.model_name,
        h.prediction.toFixed(4),
        (h.confidence * 100).toFixed(2) + '%',
        h.latency_ms,
        new Date(h.created_at).toLocaleString(),
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `predictions_${Date.now()}.csv`;
    a.click();
  };

  const features = getModelFeatures(selectedModel);

  return (
    <div className="predictions">
      <div className="predictions-header">
        <h1>Make Predictions</h1>
        <div className="header-actions">
          <button className={`tab-btn ${tab === 'predict' ? 'active' : ''}`} onClick={() => setTab('predict')}>
            Predict
          </button>
          <button className={`tab-btn ${tab === 'history' ? 'active' : ''}`} onClick={() => setTab('history')}>
            History
          </button>
        </div>
      </div>

      {tab === 'predict' && (
        <section className="predict-section">
          <div className="predict-container">
            <div className="model-selector">
              <h2>Select Model</h2>
              <select value={selectedModel} onChange={handleModelChange} className="model-select">
                {models.map(model => (
                  <option key={model} value={model}>
                    {model.replace(/_/g, ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            <form onSubmit={handlePredict} className="predict-form">
              <h2>Input Features</h2>
              <div className="features-grid">
                {features.map(feature => (
                  <div key={feature} className="feature-input">
                    <label>{feature.replace(/_/g, ' ').toUpperCase()}</label>
                    <input
                      type="number"
                      step="0.1"
                      value={inputData[feature] || 0}
                      onChange={e => handleInputChange(feature, parseFloat(e.target.value))}
                      placeholder="Enter value"
                    />
                  </div>
                ))}
              </div>

              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Making Prediction...' : 'Get Prediction'}
              </button>
            </form>

            {result && (
              <div className="result-card">
                <h2>Prediction Result</h2>
                <div className="result-content">
                  <div className="result-item">
                    <span className="label">Model</span>
                    <span className="value">{result.model_name.replace(/_/g, ' ').toUpperCase()}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">Prediction</span>
                    <span className="value prediction">{result.prediction.toFixed(4)}</span>
                  </div>
                  <div className="result-item">
                    <span className="label">Confidence</span>
                    <span className="value confidence">{(result.confidence * 100).toFixed(2)}%</span>
                  </div>
                  <div className="result-item">
                    <span className="label">Latency</span>
                    <span className="value">{result.latency_ms}ms</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {tab === 'history' && (
        <section className="history-section">
          <div className="history-header">
            <h2>Prediction History</h2>
            {history.length > 0 && (
              <button onClick={handleExportCSV} className="btn-secondary">
                📥 Export CSV
              </button>
            )}
          </div>

          {history.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Prediction</th>
                  <th>Confidence</th>
                  <th>Latency (ms)</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map(item => (
                  <tr key={item.id}>
                    <td>{item.model_name.replace(/_/g, ' ').toUpperCase()}</td>
                    <td>
                      <code>{item.prediction.toFixed(4)}</code>
                    </td>
                    <td>
                      <span className="confidence-badge">{(item.confidence * 100).toFixed(2)}%</span>
                    </td>
                    <td>{item.latency_ms}ms</td>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="empty-state">No predictions yet. Make your first prediction above!</p>
          )}
        </section>
      )}
    </div>
  );
};

export default Predictions;
