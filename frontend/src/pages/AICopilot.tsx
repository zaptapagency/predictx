import React, { useState, useEffect } from 'react';
import '../styles/ai-copilot.css';

interface Recommendation {
  id: number;
  title: string;
  description: string;
  reasoning: string;
  suggested_action: string;
  action_type: string;
  estimated_impact: string;
  success_probability: string;
  confidence: string;
  was_executed: boolean;
  created_at: string;
}

export default function AICopilot() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<Record<number, any>>({});

  useEffect(() => {
    fetchRecommendations();
  }, []);

  async function fetchRecommendations() {
    setLoading(true);
    try {
      const [recRes, insRes] = await Promise.all([
        fetch('/api/copilot/recommendations?limit=10'),
        fetch('/api/copilot/insights')
      ]);

      const recData = await recRes.json();
      const insData = await insRes.json();

      setRecommendations(recData.recommendations || []);
      setInsights(insData);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
    } finally {
      setLoading(false);
    }
  }

  async function executeRecommendation(id: number) {
    setExecutingId(id);
    try {
      const response = await fetch(`/api/copilot/${id}/execute`, { method: 'POST' });
      const data = await response.json();

      setRecommendations(
        recommendations.map(r => r.id === id ? { ...r, was_executed: true } : r)
      );
    } catch (error) {
      console.error('Error executing recommendation:', error);
    } finally {
      setExecutingId(null);
    }
  }

  async function dismissRecommendation(id: number) {
    try {
      await fetch(`/api/copilot/${id}/dismiss`, { method: 'POST' });
      setRecommendations(recommendations.filter(r => r.id !== id));
    } catch (error) {
      console.error('Error dismissing recommendation:', error);
    }
  }

  async function provideFeedback(id: number, wasHelpful: boolean, rating: number) {
    try {
      await fetch(`/api/copilot/${id}/feedback?was_helpful=${wasHelpful}&rating=${rating}`, {
        method: 'POST'
      });

      setFeedback({
        ...feedback,
        [id]: { wasHelpful, rating }
      });
    } catch (error) {
      console.error('Error providing feedback:', error);
    }
  }

  if (loading) return <div className="copilot"><div className="loading">AI Copilot is thinking...</div></div>;

  return (
    <div className="copilot">
      {/* HEADER */}
      <div className="copilot-header">
        <h1>🤖 AI Copilot</h1>
        <p>Smart recommendations powered by machine learning</p>
      </div>

      {/* INSIGHTS BANNER */}
      {insights && (
        <div className="insights-banner">
          <div className="insight-stat">
            <div className="label">Total Recommendations</div>
            <div className="value">{insights.total_recommendations}</div>
          </div>
          <div className="insight-stat">
            <div className="label">Executed</div>
            <div className="value">{insights.executed}</div>
          </div>
          <div className="insight-stat">
            <div className="label">Execution Rate</div>
            <div className="value">{insights.execution_rate}</div>
          </div>
          <div className="insight-stat">
            <div className="label">Impact Generated</div>
            <div className="value">{insights.estimated_impact}</div>
          </div>
        </div>
      )}

      {/* RECOMMENDATIONS */}
      <div className="recommendations-section">
        <h2>💡 Your Next Actions</h2>
        <div className="recommendations-list">
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className={`recommendation-card ${rec.was_executed ? 'executed' : ''}`}
            >
              {/* CARD HEADER */}
              <div className="card-header">
                <div className="header-left">
                  <h3>{rec.title}</h3>
                  {rec.was_executed && <span className="badge executed">✓ Executed</span>}
                </div>
                <div className="header-right">
                  <span className="action-type">{rec.action_type}</span>
                </div>
              </div>

              {/* CARD BODY */}
              <div className="card-body">
                <p className="description">{rec.description}</p>

                <div className="reasoning-section">
                  <div className="reasoning-label">Why this matters:</div>
                  <p className="reasoning">{rec.reasoning}</p>
                </div>

                <div className="action-suggestion">
                  <strong>Suggested Action:</strong>
                  <div className="action-text">{rec.suggested_action}</div>
                </div>

                <div className="metrics">
                  <div className="metric">
                    <span className="label">Estimated Impact</span>
                    <span className="value">{rec.estimated_impact}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Success Probability</span>
                    <span className="value">{rec.success_probability}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Confidence</span>
                    <span className="value">{rec.confidence}</span>
                  </div>
                </div>
              </div>

              {/* CARD FOOTER */}
              <div className="card-footer">
                {!rec.was_executed ? (
                  <>
                    <button
                      className="btn-execute"
                      onClick={() => executeRecommendation(rec.id)}
                      disabled={executingId === rec.id}
                    >
                      {executingId === rec.id ? '⏳ Executing...' : '✓ Execute'}
                    </button>
                    <button
                      className="btn-dismiss"
                      onClick={() => dismissRecommendation(rec.id)}
                    >
                      Dismiss
                    </button>
                  </>
                ) : (
                  <div className="feedback-section">
                    {!feedback[rec.id] ? (
                      <>
                        <span className="feedback-label">Was this helpful?</span>
                        <button
                          className="feedback-btn yes"
                          onClick={() => provideFeedback(rec.id, true, 5)}
                        >
                          👍 Yes
                        </button>
                        <button
                          className="feedback-btn no"
                          onClick={() => provideFeedback(rec.id, false, 2)}
                        >
                          👎 No
                        </button>
                      </>
                    ) : (
                      <span className="feedback-recorded">
                        ✓ Feedback recorded. Thank you!
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* EMPTY STATE */}
      {recommendations.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🤖</div>
          <h3>No recommendations at the moment</h3>
          <p>Your AI Copilot is analyzing your patterns. Check back soon!</p>
        </div>
      )}

      {/* CTA */}
      <div className="copilot-cta">
        <h2>🚀 Let the AI guide you</h2>
        <p>Each recommendation is personalized based on your success patterns</p>
        <a href="/dashboard/actions" className="cta-button">
          View Action Center →
        </a>
      </div>
    </div>
  );
}
