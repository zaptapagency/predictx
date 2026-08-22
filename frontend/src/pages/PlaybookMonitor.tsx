import React, { useState, useEffect } from 'react';
import '../styles/playbook-monitor.css';

interface PlaybookPerf {
  playbook_id: number;
  playbook_name: string;
  executions: number;
  success_rate: string;
  revenue_generated: string;
  revenue_per_execution: string;
  users_using: number;
  roi: string;
  trend: string;
  status: string;
  rank?: number;
  recommendation?: string;
  last_executed?: string;
  confidence_score?: number;
  [key: string]: any;
}

export default function PlaybookMonitor() {
  const [playbooks, setPlaybooks] = useState<PlaybookPerf[]>([]);
  const [topPerformers, setTopPerformers] = useState<PlaybookPerf[]>([]);
  const [underperformers, setUnderperformers] = useState<PlaybookPerf[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedPlaybook, setSelectedPlaybook] = useState<PlaybookPerf | null>(null);

  useEffect(() => {
    fetchPlaybookData();
  }, []);

  async function fetchPlaybookData() {
    setLoading(true);
    try {
      const [allRes, topRes, underRes] = await Promise.all([
        fetch('/api/playbook-monitor/performance?sort_by=revenue&limit=20'),
        fetch('/api/playbook-monitor/trending/top-performers?limit=5'),
        fetch('/api/playbook-monitor/trending/underperformers?limit=5')
      ]);

      const allData = await allRes.json();
      const topData = await topRes.json();
      const underData = await underRes.json();

      setPlaybooks(allData.playbooks || []);
      setTopPerformers(topData.top_performers || []);
      setUnderperformers(underData.underperformers || []);
    } catch (error) {
      console.error('Error fetching playbook data:', error);
    } finally {
      setLoading(false);
    }
  }

  const getTrendEmoji = (trend: string): string => {
    if (trend === 'improving') return '📈';
    if (trend === 'declining') return '📉';
    return '➡️';
  };

  const getHealthColor = (successRate: string): string => {
    const rate = parseFloat(successRate);
    if (rate >= 0.8) return '#10b981';
    if (rate >= 0.6) return '#fbbf24';
    return '#ef4444';
  };

  if (loading) return <div className="playbook-monitor"><div className="loading">Analyzing playbook performance...</div></div>;

  return (
    <div className="playbook-monitor">
      {/* HEADER */}
      <div className="monitor-header">
        <h1>📊 Playbook Monitor</h1>
        <p>Track performance and optimize your playbooks</p>
      </div>

      {/* TABS */}
      <div className="monitor-tabs">
        <button
          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          📋 All Playbooks ({playbooks.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'top' ? 'active' : ''}`}
          onClick={() => setActiveTab('top')}
        >
          🏆 Top Performers ({topPerformers.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'under' ? 'active' : ''}`}
          onClick={() => setActiveTab('under')}
        >
          ⚠️ Needs Improvement ({underperformers.length})
        </button>
      </div>

      {/* ALL PLAYBOOKS */}
      {activeTab === 'all' && (
        <div className="playbooks-section">
          <div className="playbooks-table">
            <div className="table-header">
              <div className="col-rank">Rank</div>
              <div className="col-name">Playbook</div>
              <div className="col-metric">Executions</div>
              <div className="col-metric">Success Rate</div>
              <div className="col-metric">Revenue</div>
              <div className="col-metric">ROI</div>
              <div className="col-metric">Users</div>
              <div className="col-trend">Trend</div>
            </div>

            {playbooks.map((pb, idx) => (
              <div
                key={pb.playbook_id}
                className="table-row"
                onClick={() => setSelectedPlaybook(pb)}
              >
                <div className="col-rank">{idx + 1}</div>
                <div className="col-name">
                  <div className="name">{pb.playbook_name}</div>
                  <div className="status">{pb.status}</div>
                </div>
                <div className="col-metric">{pb.executions.toLocaleString()}</div>
                <div className="col-metric">
                  <div
                    className="success-rate"
                    style={{ backgroundColor: getHealthColor(pb.success_rate) + '20' }}
                  >
                    {pb.success_rate}
                  </div>
                </div>
                <div className="col-metric revenue">{pb.revenue_generated}</div>
                <div className="col-metric">{pb.roi}</div>
                <div className="col-metric">{pb.users_using}</div>
                <div className="col-trend">{getTrendEmoji(pb.trend)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TOP PERFORMERS */}
      {activeTab === 'top' && (
        <div className="performers-section">
          <div className="performers-grid">
            {topPerformers.map((pb, idx) => (
              <div key={pb.playbook_id} className="performer-card top">
                <div className="rank-badge">#{pb.rank}</div>
                <div className="medal">
                  {idx === 0 && '🥇'}
                  {idx === 1 && '🥈'}
                  {idx === 2 && '🥉'}
                  {idx > 2 && '⭐'}
                </div>
                <h3>{pb.playbook_name}</h3>

                <div className="metrics">
                  <div className="metric">
                    <span className="label">Revenue Generated</span>
                    <span className="value">{pb.revenue_generated}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Executions</span>
                    <span className="value">{pb.executions}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Success Rate</span>
                    <span className="value">{pb.success_rate}</span>
                  </div>
                  <div className="metric">
                    <span className="label">ROI</span>
                    <span className="value">{pb.roi}</span>
                  </div>
                </div>

                <div className="recommendation">
                  {pb.recommendation}
                </div>

                <button className="btn-action">
                  📊 View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* UNDERPERFORMERS */}
      {activeTab === 'under' && (
        <div className="performers-section">
          <div className="performers-list">
            {underperformers.map((pb) => (
              <div key={pb.playbook_id} className="performer-item under">
                <div className="item-left">
                  <div className="icon">⚠️</div>
                  <div className="info">
                    <h3>{pb.playbook_name}</h3>
                    <div className="success-rate">
                      Success Rate: <strong>{pb.success_rate}</strong>
                    </div>
                    <div className="trend">
                      Trend: <strong>{pb.trend}</strong>
                    </div>
                  </div>
                </div>

                <div className="item-right">
                  <div className="executions">
                    {pb.executions} executions
                  </div>
                  <div className="recommendation">
                    {pb.recommendation}
                  </div>
                  <div className="actions">
                    <button className="btn-action">🔧 Review Config</button>
                    <button className="btn-action">❌ Deprecate</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DETAIL MODAL */}
      {selectedPlaybook && (
        <div className="detail-modal">
          <div className="modal-content">
            <button className="btn-close" onClick={() => setSelectedPlaybook(null)}>✕</button>

            <h2>{selectedPlaybook.playbook_name}</h2>

            <div className="detail-metrics">
              <div className="metric-card">
                <div className="label">Total Executions</div>
                <div className="value">{selectedPlaybook.executions}</div>
              </div>
              <div className="metric-card">
                <div className="label">Success Rate</div>
                <div className="value" style={{ color: getHealthColor(selectedPlaybook.success_rate) }}>
                  {selectedPlaybook.success_rate}
                </div>
              </div>
              <div className="metric-card">
                <div className="label">Revenue Generated</div>
                <div className="value">{selectedPlaybook.revenue_generated}</div>
              </div>
              <div className="metric-card">
                <div className="label">Revenue/Execution</div>
                <div className="value">{selectedPlaybook.revenue_per_execution}</div>
              </div>
              <div className="metric-card">
                <div className="label">ROI Multiplier</div>
                <div className="value">{selectedPlaybook.roi}</div>
              </div>
              <div className="metric-card">
                <div className="label">Users Using</div>
                <div className="value">{selectedPlaybook.users_using}</div>
              </div>
            </div>

            <div className="detail-actions">
              <button className="btn-action">📈 View Trend</button>
              <button className="btn-action">⚙️ Configure</button>
              <button className="btn-action">📊 Export Report</button>
            </div>
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="monitor-cta">
        <h2>🚀 Optimize your playbooks</h2>
        <p>Double down on winners, fix or deprecate underperformers</p>
        <a href="/dashboard/playbooks" className="cta-button">
          Manage Playbooks →
        </a>
      </div>
    </div>
  );
}
