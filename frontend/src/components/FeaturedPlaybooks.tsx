import React, { useState, useEffect } from 'react';
import '../styles/featured-playbooks.css';

interface FeaturedPlaybook {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  use_case: string;
  industry: string;
  price_monthly: number;
  price_yearly: number;
  free: boolean;
  icon: string;
  success_rate: number;
  typical_roi: number;
  setup_time_minutes: number;
  avg_rating: number;
  review_count: number;
  downloads: number;
  tags: string[];
}

export default function FeaturedPlaybooks() {
  const [playbooks, setPlaybooks] = useState<FeaturedPlaybook[]>([]);
  const [loading, setLoading] = useState(true);

  const featured = [
    'churn-prevention-high-value',
    'lead-scoring-conversion',
    'expansion-opportunity',
    'fraud-detection-realtime',
    'demand-forecasting-inventory',
  ];

  useEffect(() => {
    fetchFeaturedPlaybooks();
  }, []);

  async function fetchFeaturedPlaybooks() {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/marketplace/playbooks?sort=popular&limit=10`
      );
      const data = await response.json();

      // Filter to featured only
      const filteredPlaybooks = data.playbooks.filter((p: FeaturedPlaybook) =>
        featured.includes(p.slug)
      );

      setPlaybooks(filteredPlaybooks);
    } catch (error) {
      console.error('Error fetching featured playbooks:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="featured-loading">Loading featured playbooks...</div>;

  return (
    <section className="featured-playbooks-section">
      <div className="featured-header">
        <h2>✨ Featured Playbook Templates</h2>
        <p>Pre-built, proven playbooks you can start using in minutes</p>
      </div>

      <div className="featured-grid">
        {playbooks.map((playbook) => (
          <div key={playbook.id} className="featured-card">
            {/* HEADER */}
            <div className="featured-card-header">
              <div className="icon">{playbook.icon}</div>
              <div className="badges">
                <span className="badge featured-badge">⭐ Featured</span>
                <span className="badge category-badge">{playbook.category}</span>
              </div>
            </div>

            {/* TITLE & DESCRIPTION */}
            <h3>{playbook.name}</h3>
            <p className="description">{playbook.description}</p>

            {/* QUICK STATS */}
            <div className="quick-stats">
              <div className="stat">
                <div className="label">Success Rate</div>
                <div className="value">{(playbook.success_rate * 100).toFixed(0)}%</div>
              </div>
              <div className="stat">
                <div className="label">Typical ROI</div>
                <div className="value">{playbook.typical_roi.toFixed(1)}x</div>
              </div>
              <div className="stat">
                <div className="label">Setup Time</div>
                <div className="value">{playbook.setup_time_minutes}m</div>
              </div>
            </div>

            {/* META INFO */}
            <div className="meta-info">
              <div className="rating">
                ⭐ {playbook.avg_rating.toFixed(1)} ({playbook.review_count} reviews)
              </div>
              <div className="downloads">
                📥 {playbook.downloads.toLocaleString()} installs
              </div>
            </div>

            {/* USE CASE & INDUSTRY */}
            <div className="use-case-industry">
              <span className="use-case">{playbook.use_case}</span>
              <span className="industry">{playbook.industry}</span>
            </div>

            {/* TAGS */}
            <div className="tags">
              {playbook.tags?.slice(0, 3).map((tag) => (
                <span key={tag} className="tag">
                  #{tag}
                </span>
              ))}
            </div>

            {/* CTA */}
            <div className="featured-card-footer">
              <div className="price">
                {playbook.free ? (
                  <span className="free-badge">Free</span>
                ) : (
                  <span className="price-badge">
                    ${playbook.price_monthly}/mo
                  </span>
                )}
              </div>
              <a href={`/marketplace/${playbook.slug}`} className="view-cta">
                View Details →
              </a>
            </div>
          </div>
        ))}
      </div>

      {/* CTA SECTION */}
      <div className="featured-cta">
        <h3>Need a custom playbook?</h3>
        <p>Create your own using the Playbook Builder</p>
        <a href="/create-playbook" className="cta-button">
          Build Custom Playbook
        </a>
      </div>
    </section>
  );
}
