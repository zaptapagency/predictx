import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/landing.css';

const Landing: React.FC = () => {
  return (
    <div className="landing">
      {/* Navigation */}
      <nav className="navbar">
        <div className="container">
          <div className="logo">PredictX</div>
          <div className="nav-links">
            <Link to="/pricing">Pricing</Link>
            <Link to="/features">Features</Link>
            <Link to="/documentation">Documentation</Link>
            <Link to="/login" className="btn-primary">Sign In</Link>
            <Link to="/signup" className="btn-secondary">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1>Machine Learning Predictions Made Easy</h1>
            <p>Deploy LightGBM models with a single click. Scale to millions of predictions.</p>
            <div className="hero-buttons">
              <Link to="/signup" className="btn-large btn-primary">
                Start Free
              </Link>
              <Link to="/documentation" className="btn-large btn-outline">
                Learn More
              </Link>
            </div>
          </div>
          <div className="hero-image">
            <img src="/hero.png" alt="PredictX Platform" />
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <div className="container">
          <h2>Powerful Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Lightning Fast</h3>
              <p>Get predictions in milliseconds with our optimized API.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Enterprise Security</h3>
              <p>Bank-level encryption and compliance certifications.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Real-time Analytics</h3>
              <p>Monitor predictions and track usage in real-time.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🚀</div>
              <h3>Easy Integration</h3>
              <p>REST API and SDKs for popular languages.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">💰</div>
              <h3>Pay As You Go</h3>
              <p>No setup fees. Scale your costs with your usage.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔄</div>
              <h3>Continuous Updates</h3>
              <p>Update models without any downtime.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="pricing">
        <div className="container">
          <h2>Simple, Transparent Pricing</h2>
          <div className="pricing-cards">
            <div className="pricing-card">
              <h3>Free</h3>
              <div className="price">$0</div>
              <ul className="features-list">
                <li>✓ 100 predictions/month</li>
                <li>✓ 1,000 API calls/month</li>
                <li>✓ Community support</li>
              </ul>
              <Link to="/signup" className="btn-secondary">
                Get Started
              </Link>
            </div>
            <div className="pricing-card featured">
              <div className="badge">Popular</div>
              <h3>Pro</h3>
              <div className="price">$29<span>/month</span></div>
              <ul className="features-list">
                <li>✓ 10,000 predictions/month</li>
                <li>✓ 100,000 API calls/month</li>
                <li>✓ Email support</li>
                <li>✓ Usage analytics</li>
              </ul>
              <Link to="/signup" className="btn-primary">
                Start Free Trial
              </Link>
            </div>
            <div className="pricing-card">
              <h3>Enterprise</h3>
              <div className="price">Custom</div>
              <ul className="features-list">
                <li>✓ Unlimited predictions</li>
                <li>✓ Unlimited API calls</li>
                <li>✓ Priority support</li>
                <li>✓ Custom SLA</li>
              </ul>
              <a href="mailto:sales@predictx.com" className="btn-outline">
                Contact Sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta">
        <div className="container">
          <h2>Ready to get started?</h2>
          <p>Join thousands of companies using PredictX for their ML predictions.</p>
          <Link to="/signup" className="btn-large btn-primary">
            Create Free Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h4>PredictX</h4>
              <p>ML predictions made simple.</p>
            </div>
            <div className="footer-section">
              <h4>Product</h4>
              <Link to="/features">Features</Link>
              <Link to="/pricing">Pricing</Link>
              <Link to="/documentation">Documentation</Link>
            </div>
            <div className="footer-section">
              <h4>Company</h4>
              <a href="#about">About</a>
              <a href="#blog">Blog</a>
              <a href="#contact">Contact</a>
            </div>
            <div className="footer-section">
              <h4>Legal</h4>
              <a href="#privacy">Privacy Policy</a>
              <a href="#terms">Terms of Service</a>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2026 PredictX. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
