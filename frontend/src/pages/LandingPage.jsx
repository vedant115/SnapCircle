import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LandingPage = () => {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, navigate]);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (isLogin) {
        // Login
        const result = await login(formData.email, formData.password);
        if (result.success) {
          setShowAuthModal(false);
          navigate("/dashboard");
        } else {
          setError(result.error);
        }
      } else {
        // Register
        if (formData.password !== formData.confirmPassword) {
          setError("Passwords do not match");
          setLoading(false);
          return;
        }

        const userData = {
          name: formData.name,
          email: formData.email,
          password: formData.password,
        };

        const result = await register(userData);
        if (result.success) {
          setShowAuthModal(false);
          navigate("/dashboard");
        } else {
          setError(result.error);
        }
      }
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
    setError("");
  };

  const openAuthModal = (loginMode = true) => {
    setIsLogin(loginMode);
    setShowAuthModal(true);
    setError("");
    setFormData({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
  };

  const closeAuthModal = () => {
    setShowAuthModal(false);
    setError("");
    setFormData({
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    });
  };

  return (
    <>
      <div className="new-landing-page">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <div className="hero-text">
              <h1 className="hero-title">
                <span className="brand-name">SnapCircle</span>
                <span className="hero-subtitle">
                  Share Memories, Create Connections
                </span>
              </h1>
              <p className="hero-description">
                The ultimate event photo sharing platform. Create events, invite
                guests, and let AI-powered face recognition automatically
                organize and share photos with the right people.
              </p>
              <div className="hero-buttons">
                <button
                  className="btn btn-primary btn-large"
                  onClick={() => openAuthModal(false)}
                >
                  Get Started Free
                </button>
                <button
                  className="btn btn-secondary btn-large"
                  onClick={() => openAuthModal(true)}
                >
                  Sign In
                </button>
              </div>
            </div>
            <div className="hero-visual">
              <div className="hero-icon">📸</div>
              <div className="floating-icons">
                <span className="float-icon">🎉</span>
                <span className="float-icon">👥</span>
                <span className="float-icon">🤳</span>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section">
          <div className="features-container">
            <h2 className="section-title">Why Choose SnapCircle?</h2>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🎯</div>
                <h3>Smart Face Recognition</h3>
                <p>
                  AI automatically identifies and organizes photos by people,
                  making it easy to find and share memories with the right
                  guests.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h3>Instant Event Creation</h3>
                <p>
                  Create events in seconds with unique QR codes and shareable
                  links. Guests can join and start uploading immediately.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🔒</div>
                <h3>Privacy First</h3>
                <p>
                  Your photos are secure and private. Only event participants
                  can access shared memories with role-based permissions.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">📱</div>
                <h3>Mobile Optimized</h3>
                <p>
                  Perfect experience on any device. Upload, view, and share
                  photos seamlessly from your phone or computer.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🎨</div>
                <h3>Beautiful Galleries</h3>
                <p>
                  Stunning photo galleries with easy navigation, filtering, and
                  download options for all your event memories.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">🚀</div>
                <h3>Lightning Fast</h3>
                <p>
                  Quick uploads, instant processing, and real-time updates
                  ensure your memories are shared without delay.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <div className="cta-content">
            <h2>Ready to Start Sharing?</h2>
            <p>
              Join thousands of users who trust SnapCircle for their event photo
              sharing needs.
            </p>
            <div className="cta-buttons">
              <button
                className="btn btn-primary btn-large"
                onClick={() => openAuthModal(false)}
              >
                Create Your First Event
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="auth-modal-overlay" onClick={closeAuthModal}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeAuthModal}>
              ✕
            </button>

            <div className="auth-form-container">
              <div className="auth-tabs">
                <button
                  className={`tab ${isLogin ? "active" : ""}`}
                  onClick={() => setIsLogin(true)}
                >
                  Login
                </button>
                <button
                  className={`tab ${!isLogin ? "active" : ""}`}
                  onClick={() => setIsLogin(false)}
                >
                  Register
                </button>
              </div>

              <form onSubmit={handleSubmit} className="auth-form">
                {error && <div className="error">{error}</div>}

                {!isLogin && (
                  <div className="form-group">
                    <label htmlFor="name">Full Name</label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                      placeholder="Enter your full name"
                    />
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    required
                    placeholder="Enter your email"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="password">Password</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                    placeholder="Enter your password"
                    minLength="6"
                  />
                </div>

                {!isLogin && (
                  <div className="form-group">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <input
                      type="password"
                      id="confirmPassword"
                      name="confirmPassword"
                      value={formData.confirmPassword}
                      onChange={handleInputChange}
                      required
                      placeholder="Confirm your password"
                      minLength="6"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-primary auth-submit"
                  disabled={loading}
                >
                  {loading ? "Please wait..." : isLogin ? "Login" : "Register"}
                </button>
              </form>

              <div className="auth-switch">
                <p>
                  {isLogin
                    ? "Don't have an account? "
                    : "Already have an account? "}
                  <button
                    type="button"
                    className="link-button"
                    onClick={toggleMode}
                  >
                    {isLogin ? "Register here" : "Login here"}
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default LandingPage;
