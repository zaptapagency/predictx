import React, { useState } from 'react';
import './App.css';

const App: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handlePredict = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/health');
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: String(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>UniversalPredict Platform</h1>
        <p>Make predictions with your LightGBM models</p>
      </header>

      <main>
        <section className="dashboard">
          <div className="card">
            <h2>System Status</h2>
            <form onSubmit={handlePredict}>
              <button type="submit" disabled={loading}>
                {loading ? 'Checking...' : 'Check Health'}
              </button>
            </form>

            {result && (
              <div className="result">
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>

          <div className="card">
            <h2>Make a Prediction</h2>
            <form>
              <div className="form-group">
                <label>Vertical:</label>
                <select defaultValue="saas">
                  <option value="saas">SaaS</option>
                  <option value="retail">Retail</option>
                  <option value="healthcare">Healthcare</option>
                </select>
              </div>

              <div className="form-group">
                <label>Prediction Type:</label>
                <input type="text" placeholder="e.g., churn, purchase" />
              </div>

              <button type="submit">Predict</button>
            </form>
          </div>

          <div className="card">
            <h2>Upload Data</h2>
            <input type="file" accept=".csv,.xlsx" />
            <button>Process Batch</button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
