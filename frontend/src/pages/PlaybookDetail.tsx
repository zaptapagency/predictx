import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/playbook-detail.css';

interface PlaybookDetail {
  id: number;
  name: string;
  slug: string;
  description: string;
  category: string;
  use_case: string;
  industry: string;
  price_monthly: number;
  price_yearly: number | null;
  free: boolean;
  creator: { id: number; name: string };
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
  total_revenue: number;
  has_purchased: boolean;
  reviews: Review[];
  tags: string[];
  configuration: any;
}

interface Review {
  id: number;
  rating: number;
  title: string;
  review_text: string;
  user_name: string;
  ease_of_setup: number;
  would_recommend: boolean;
  helpful_count: number;
  created_at: string;
}

export default function PlaybookDetail() {
  const { slug } = useParams<{ slug: string }>();
  const [playbook, setPlaybook] = useState<PlaybookDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [licenseType, setLicenseType] = useState('monthly');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState('');

  useEffect(() => {
    fetchPlaybookDetail();
  }, [slug]);

  async function fetchPlaybookDetail() {
    if (!slug) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/marketplace/playbooks/${slug}`);
      const data = await response.json();
      setPlaybook(data);
    } catch (error) {
      console.error('Error fetching playbook:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handlePurchase() {
    if (!playbook) return;
    setPurchasing(true);
    try {
      const response = await fetch(`/api/marketplace/playbooks/${playbook.id}/purchase?license_type=${licenseType}`, {
        method: 'POST',
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Successfully subscribed! Check your dashboard to install.');
        fetchPlaybookDetail(); // Refresh to show purchased status
      }
    } catch (error) {
      console.error('Error purchasing playbook:', error);
      alert('❌ Purchase failed. Please try again.');
    } finally {
      setPurchasing(false);
    }
  }

  async function handleSubmitReview() {
    if (!playbook) return;
    try {
      const response = await fetch(`/api/marketplace/playbooks/${playbook.id}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: reviewRating,
          review_text: reviewText,
          would_recommend: reviewRating >= 4,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setShowReviewForm(false);
        setReviewText('');
        fetchPlaybookDetail(); // Refresh reviews
      }
    } catch (error) {
      console.error('Error submitting review:', error);
    }
  }

  if (loading) return <div className="playbook-detail-container"><div className="loading">Loading playbook...</div></div>;
  if (!playbook) return <div className="playbook-detail-container"><div className="error">Playbook not found</div></div>;

  return (
    <div className="playbook-detail-container">
      {/* HERO SECTION */}
      <div className="playbook-hero">
        <div className="hero-content">
          <div className="hero-icon">{playbook.icon || '📋'}</div>
          <div className="hero-info">
            <h1>{playbook.name}</h1>
            <p className="hero-description">{playbook.description}</p>
            <div className="hero-meta">
              <span className="meta-item">📊 {playbook.category}</span>
              <span className="meta-item">🎯 {playbook.use_case}</span>
              {playbook.industry && <span className="meta-item">🏭 {playbook.industry}</span>}
            </div>
          </div>
        </div>

        {/* SIDEBAR */}
        <div className="playbook-sidebar">
          <div className="pricing-card">
            <div className="rating">
              <div className="stars">⭐ {playbook.avg_rating.toFixed(1)}</div>
              <div className="review-count">({playbook.review_count} reviews)</div>
            </div>

            <div className="price-section">
              {playbook.free ? (
                <>
                  <div className="price">Free</div>
                  <p className="price-note">No credit card required</p>
                </>
              ) : (
                <>
                  <div className="price">${playbook.price_monthly}/month</div>
                  {playbook.price_yearly && (
                    <p className="price-note">or ${playbook.price_yearly}/year (save 25%)</p>
                  )}
                </>
              )}
            </div>

            {!playbook.has_purchased ? (
              <>
                {!playbook.free && (
                  <div className="license-selector">
                    <label>
                      <input
                        type="radio"
                        value="monthly"
                        checked={licenseType === 'monthly'}
                        onChange={(e) => setLicenseType(e.target.value)}
                      />
                      Monthly (${playbook.price_monthly})
                    </label>
                    {playbook.price_yearly && (
                      <label>
                        <input
                          type="radio"
                          value="yearly"
                          checked={licenseType === 'yearly'}
                          onChange={(e) => setLicenseType(e.target.value)}
                        />
                        Yearly (${playbook.price_yearly})
                      </label>
                    )}
                  </div>
                )}
                <button
                  onClick={handlePurchase}
                  disabled={purchasing}
                  className="purchase-btn"
                >
                  {purchasing ? '⏳ Processing...' : playbook.free ? '✅ Get Free' : '💳 Subscribe Now'}
                </button>
              </>
            ) : (
              <button className="purchase-btn purchased">✅ Already Subscribed</button>
            )}

            <div className="trust-badges">
              <div className="badge">💯 {playbook.success_rate ? `${(playbook.success_rate * 100).toFixed(0)}% Success` : 'Proven'}</div>
              <div className="badge">📈 {playbook.typical_roi?.toFixed(1)}x ROI</div>
              <div className="badge">⏱️ {playbook.setup_time_minutes} min setup</div>
            </div>
          </div>

          <div className="stats-card">
            <div className="stat">
              <div className="stat-label">Downloads</div>
              <div className="stat-value">{playbook.downloads.toLocaleString()}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Active Users</div>
              <div className="stat-value">{playbook.active_users.toLocaleString()}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Creator Revenue</div>
              <div className="stat-value">${playbook.total_revenue.toLocaleString()}</div>
            </div>
          </div>

          <div className="creator-card">
            <div className="creator-label">Created by</div>
            <div className="creator-name">{playbook.creator.name}</div>
            <button className="creator-view-btn">View Creator Profile</button>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="playbook-main">
        {/* FEATURES & BENEFITS */}
        <section className="section">
          <h2>✨ What This Playbook Does</h2>
          <div className="benefits-list">
            <div className="benefit">
              <div className="benefit-icon">🎯</div>
              <div className="benefit-text">
                <h4>Automated Predictions</h4>
                <p>Predicts {playbook.use_case} using machine learning on your data</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">⚡</div>
              <div className="benefit-text">
                <h4>Instant Actions</h4>
                <p>Automatically triggers workflows and alerts when predictions trigger</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">📊</div>
              <div className="benefit-text">
                <h4>Proven Results</h4>
                <p>{playbook.success_rate ? `${(playbook.success_rate * 100).toFixed(0)}% success rate` : 'Trusted by thousands'}</p>
              </div>
            </div>
            <div className="benefit">
              <div className="benefit-icon">🔧</div>
              <div className="benefit-text">
                <h4>Easy Setup</h4>
                <p>Takes just {playbook.setup_time_minutes} minutes to get started</p>
              </div>
            </div>
          </div>
        </section>

        {/* HOW IT WORKS */}
        <section className="section">
          <h2>📋 How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h4>Install Playbook</h4>
                <p>Subscribe and playbook is added to your dashboard instantly</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h4>Connect Data</h4>
                <p>Playbook automatically syncs with your data sources (Salesforce, Stripe, etc)</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h4>Run Predictions</h4>
                <p>Playbook executes and identifies targets for action</p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h4>Automate Actions</h4>
                <p>Automatically sends emails, alerts, and integrations with your tools</p>
              </div>
            </div>
          </div>
        </section>

        {/* REVIEWS */}
        <section className="section">
          <div className="reviews-header">
            <h2>⭐ Reviews & Ratings</h2>
            {playbook.has_purchased && (
              <button
                onClick={() => setShowReviewForm(!showReviewForm)}
                className="leave-review-btn"
              >
                {showReviewForm ? 'Cancel' : 'Leave Review'}
              </button>
            )}
          </div>

          {showReviewForm && (
            <div className="review-form">
              <div className="form-group">
                <label>Rating</label>
                <div className="rating-selector">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      className={`star ${n <= reviewRating ? 'active' : ''}`}
                      onClick={() => setReviewRating(n)}
                    >
                      ⭐
                    </button>
                  ))}
                </div>
              </div>
              <div className="form-group">
                <label>Your Review</label>
                <textarea
                  value={reviewText}
                  onChange={(e) => setReviewText(e.target.value)}
                  placeholder="Share your experience with this playbook..."
                  rows={4}
                />
              </div>
              <button onClick={handleSubmitReview} className="submit-review-btn">
                Submit Review
              </button>
            </div>
          )}

          <div className="reviews-list">
            {playbook.reviews.length === 0 ? (
              <p className="no-reviews">No reviews yet. Be the first to review!</p>
            ) : (
              playbook.reviews.map((review) => (
                <div key={review.id} className="review-card">
                  <div className="review-header">
                    <div className="review-rating">
                      {'⭐'.repeat(review.rating)}
                    </div>
                    <div className="review-author">{review.user_name}</div>
                  </div>
                  {review.title && <div className="review-title">{review.title}</div>}
                  <p className="review-text">{review.review_text}</p>
                  {review.would_recommend && <div className="review-recommend">✓ Would recommend</div>}
                  <div className="review-date">{new Date(review.created_at).toLocaleDateString()}</div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
