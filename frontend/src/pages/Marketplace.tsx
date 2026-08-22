import React, { useState, useEffect } from 'react';
import '../styles/marketplace.css';

interface Playbook {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  use_case: string;
  industry: string;
  price_monthly: number;
  free: boolean;
  creator: { id: number; name: string; email: string };
  downloads: number;
  active_users: number;
  avg_rating: number;
  review_count: number;
  success_rate: number;
  typical_roi: number;
  setup_time_minutes: number;
  icon: string;
  thumbnail_url: string;
  published_at: string;
}

interface MarketplaceStats {
  total_playbooks: number;
  total_creators: number;
  total_purchases: number;
  total_revenue: number;
  top_playbook: { name: string; downloads: number } | null;
}

export default function Marketplace() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [stats, setStats] = useState<MarketplaceStats | null>(null);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedUseCase, setSelectedUseCase] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [sortBy, setSortBy] = useState('popular');

  const [page, setPage] = useState(0);
  const limit = 12;

  useEffect(() => {
    fetchMarketplaceData();
    fetchStats();
  }, [search, selectedCategory, selectedUseCase, selectedIndustry, sortBy, page]);

  async function fetchMarketplaceData() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('skip', String(page * limit));
      params.append('limit', String(limit));
      params.append('sort', sortBy);
      if (search) params.append('search', search);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedUseCase) params.append('use_case', selectedUseCase);
      if (selectedIndustry) params.append('industry', selectedIndustry);

      const response = await fetch(`/api/marketplace/playbooks?${params}`);
      const data = await response.json();
      setPlaybooks(data.playbooks);
    } catch (error) {
      console.error('Error fetching playbooks:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      const response = await fetch('/api/marketplace/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }

  const categories = [
    'churn', 'expansion', 'fraud', 'forecasting', 'lead-scoring',
    'pricing', 'upsell', 'support', 'product', 'retention'
  ];

  const useCases = [
    'churn-prediction', 'lead-scoring', 'fraud-detection', 'demand-forecasting',
    'price-optimization', 'expansion-opportunity', 'customer-health', 'support-escalation'
  ];

  const industries = [
    'SaaS', 'E-commerce', 'Fintech', 'Healthcare', 'Telecom',
    'Insurance', 'Retail', 'Manufacturing', 'Subscription', 'Enterprise'
  ];

  return (
    <div className="marketplace-container">
      {/* HEADER */}
      <div className="marketplace-header">
        <div className="header-content">
          <h1>🎯 ForecastX Playbook Marketplace</h1>
          <p>Discover proven playbooks from community creators • Sell your own • Earn 70% revenue share</p>

          {stats && (
            <div className="marketplace-stats">
              <div className="stat-card">
                <div className="stat-number">{stats.total_playbooks}+</div>
                <div className="stat-label">Playbooks</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.total_creators}+</div>
                <div className="stat-label">Creators</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">${stats.total_revenue.toLocaleString()}</div>
                <div className="stat-label">Creator Revenue</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{stats.total_purchases.toLocaleString()}+</div>
                <div className="stat-label">Active Subscriptions</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* SEARCH & FILTERS */}
      <div className="marketplace-controls">
        <input
          type="text"
          placeholder="Search playbooks..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          className="search-input"
        />

        <select
          value={sortBy}
          onChange={(e) => {
            setSortBy(e.target.value);
            setPage(0);
          }}
          className="sort-select"
        >
          <option value="popular">Popular</option>
          <option value="newest">Newest</option>
          <option value="highest-rated">Highest Rated</option>
          <option value="trending">Trending</option>
        </select>

        <button className="filter-toggle">⚙️ Filters</button>
      </div>

      <div className="marketplace-layout">
        {/* SIDEBAR FILTERS */}
        <div className="marketplace-sidebar">
          <div className="filter-section">
            <h3>Category</h3>
            <div className="filter-options">
              <label>
                <input
                  type="radio"
                  name="category"
                  value=""
                  checked={selectedCategory === ''}
                  onChange={() => {
                    setSelectedCategory('');
                    setPage(0);
                  }}
                />
                All Categories
              </label>
              {categories.map((cat) => (
                <label key={cat}>
                  <input
                    type="radio"
                    name="category"
                    value={cat}
                    checked={selectedCategory === cat}
                    onChange={() => {
                      setSelectedCategory(cat);
                      setPage(0);
                    }}
                  />
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </label>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <h3>Use Case</h3>
            <div className="filter-options">
              <label>
                <input
                  type="radio"
                  name="usecase"
                  value=""
                  checked={selectedUseCase === ''}
                  onChange={() => {
                    setSelectedUseCase('');
                    setPage(0);
                  }}
                />
                All Use Cases
              </label>
              {useCases.map((uc) => (
                <label key={uc}>
                  <input
                    type="radio"
                    name="usecase"
                    value={uc}
                    checked={selectedUseCase === uc}
                    onChange={() => {
                      setSelectedUseCase(uc);
                      setPage(0);
                    }}
                  />
                  {uc.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </label>
              ))}
            </div>
          </div>

          <div className="filter-section">
            <h3>Industry</h3>
            <div className="filter-options">
              <label>
                <input
                  type="radio"
                  name="industry"
                  value=""
                  checked={selectedIndustry === ''}
                  onChange={() => {
                    setSelectedIndustry('');
                    setPage(0);
                  }}
                />
                All Industries
              </label>
              {industries.map((ind) => (
                <label key={ind}>
                  <input
                    type="radio"
                    name="industry"
                    value={ind}
                    checked={selectedIndustry === ind}
                    onChange={() => {
                      setSelectedIndustry(ind);
                      setPage(0);
                    }}
                  />
                  {ind}
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* PLAYBOOKS GRID */}
        <div className="marketplace-content">
          {loading ? (
            <div className="loading">Loading playbooks...</div>
          ) : playbooks.length === 0 ? (
            <div className="no-results">
              <p>No playbooks found. Try adjusting your filters.</p>
            </div>
          ) : (
            <>
              <div className="playbooks-grid">
                {playbooks.map((playbook) => (
                  <a
                    key={playbook.id}
                    href={`/marketplace/${playbook.slug}`}
                    className="playbook-card"
                  >
                    <div className="playbook-header">
                      <div className="playbook-icon">{playbook.icon || '📋'}</div>
                      <div className="playbook-badge">{playbook.category}</div>
                    </div>

                    <h3>{playbook.name}</h3>
                    <p className="playbook-description">{playbook.description}</p>

                    <div className="playbook-meta">
                      <span className="use-case">{playbook.use_case}</span>
                      {playbook.industry && <span className="industry">{playbook.industry}</span>}
                    </div>

                    <div className="playbook-stats">
                      <div className="stat">
                        <div className="stat-icon">⭐</div>
                        <div className="stat-value">{playbook.avg_rating.toFixed(1)}</div>
                        <div className="stat-label">({playbook.review_count})</div>
                      </div>
                      <div className="stat">
                        <div className="stat-icon">📥</div>
                        <div className="stat-value">{playbook.downloads}</div>
                        <div className="stat-label">Downloads</div>
                      </div>
                      <div className="stat">
                        <div className="stat-icon">📈</div>
                        <div className="stat-value">{playbook.typical_roi?.toFixed(1)}x</div>
                        <div className="stat-label">ROI</div>
                      </div>
                    </div>

                    <div className="playbook-creator">
                      <span>by {playbook.creator.name}</span>
                    </div>

                    <div className="playbook-footer">
                      {playbook.free ? (
                        <button className="price-badge free">Free</button>
                      ) : (
                        <button className="price-badge">${playbook.price_monthly}/mo</button>
                      )}
                      <button className="view-btn">View Details →</button>
                    </div>
                  </a>
                ))}
              </div>

              {/* PAGINATION */}
              <div className="pagination">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="pagination-btn"
                >
                  ← Previous
                </button>
                <span className="page-info">Page {page + 1}</span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={playbooks.length < limit}
                  className="pagination-btn"
                >
                  Next →
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* CTA SECTION */}
      <div className="marketplace-cta">
        <div className="cta-content">
          <h2>Have a winning playbook? Share it with the world</h2>
          <p>Create your own playbook and earn 70% revenue share from every subscription</p>
          <a href="/create-playbook" className="cta-button">Publish Your Playbook</a>
        </div>
      </div>
    </div>
  );
}
