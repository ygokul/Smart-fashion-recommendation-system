import React from 'react';
import { useNavigate } from 'react-router-dom';
import { FiArrowRight, FiCheck, FiStar, FiUsers, FiShield } from 'react-icons/fi';
import { BsStars } from 'react-icons/bs';
import './LandingPage.css';

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-container">
      {/* Background Animation */}
      <div className="landing-bg-animation">
        <div className="bg-circle circle-1"></div>
        <div className="bg-circle circle-2"></div>
        <div className="bg-circle circle-3"></div>
      </div>

      {/* Navbar */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <BsStars className="nav-logo" />
          <span className="nav-title">SmartFit AI</span>
        </div>
        <div className="nav-actions">
          <button className="nav-login" onClick={() => navigate('/login')}>
            Login
          </button>
          <button className="nav-signup" onClick={() => navigate('/login')}>
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <BsStars className="badge-icon" />
            <span>AI-Powered Fashion Assistant</span>
          </div>
          <h1 className="hero-title">
            Discover Your Perfect Style with
            <span className="gradient-text"> AI Fashion Stylist</span>
          </h1>
          <p className="hero-description">
            Get personalized clothing recommendations, virtual try-ons, and style advice 
            powered by advanced artificial intelligence. Transform your wardrobe with SmartFit AI.
          </p>
          <div className="hero-cta">
            <button className="cta-primary" onClick={() => navigate('/login')}>
              Start Here
              <FiArrowRight className="cta-icon" />
            </button>
            <button className="cta-secondary" onClick={() => navigate('/login')}>
              Watch Demo
            </button>
          </div>
        </div>
        <div className="hero-image">
          <div className="image-placeholder">
            <div className="fashion-grid">
              <div className="grid-item item-1"></div>
              <div className="grid-item item-2"></div>
              <div className="grid-item item-3"></div>
              <div className="grid-item item-4"></div>
            </div>
          </div>
        </div>
      </section>


      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <p className="footer-tagline">Your Personal AI Fashion Stylist</p>
          </div>
          <div className="footer-links">
            <a href="#">Terms of Service</a>
            <a href="#">Privacy Policy</a>
            <a href="#">Contact Us</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2024 SmartFit AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;