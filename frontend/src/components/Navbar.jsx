import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/dashboard" className="navbar-brand" onClick={closeMenu}>
          SnapCircle
        </Link>

        {/* Mobile hamburger button */}
        <button
          className={`navbar-toggle ${isMenuOpen ? "active" : ""}`}
          onClick={toggleMenu}
          aria-label="Toggle navigation menu"
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>

        {/* Desktop menu */}
        <div className="navbar-menu desktop-menu">
          <Link to="/dashboard" className="navbar-item">
            Dashboard
          </Link>
          <Link to="/create-event" className="navbar-item">
            Create Event
          </Link>
          <Link to="/join-event" className="navbar-item">
            Join Event
          </Link>
          <Link to="/profile" className="navbar-item">
            Profile
          </Link>
        </div>

        {/* Desktop user section */}
        <div className="navbar-user desktop-user">
          <span className="user-name">Hello, {user?.name}</span>
          <button onClick={handleLogout} className="btn btn-secondary">
            Logout
          </button>
        </div>

        {/* Mobile menu overlay */}
        <div className={`mobile-menu ${isMenuOpen ? "active" : ""}`}>
          <div className="mobile-menu-content">
            <div className="mobile-user-info">
              <span className="mobile-user-name">Hello, {user?.name}</span>
            </div>

            <div className="mobile-menu-items">
              <Link
                to="/dashboard"
                className="mobile-menu-item"
                onClick={closeMenu}
              >
                📊 Dashboard
              </Link>
              <Link
                to="/create-event"
                className="mobile-menu-item"
                onClick={closeMenu}
              >
                ➕ Create Event
              </Link>
              <Link
                to="/join-event"
                className="mobile-menu-item"
                onClick={closeMenu}
              >
                🔗 Join Event
              </Link>
              <Link
                to="/profile"
                className="mobile-menu-item"
                onClick={closeMenu}
              >
                👤 Profile
              </Link>
              <button
                onClick={() => {
                  handleLogout();
                  closeMenu();
                }}
                className="mobile-logout-btn"
              >
                🚪 Logout
              </button>
            </div>
          </div>
        </div>

        {/* Mobile menu backdrop */}
        {isMenuOpen && (
          <div className="mobile-menu-backdrop" onClick={closeMenu}></div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
