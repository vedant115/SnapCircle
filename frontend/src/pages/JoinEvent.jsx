import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { eventsAPI, authAPI } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import SelfieUpload from "../components/SelfieUpload";

const JoinEvent = () => {
  const { eventCode: urlEventCode } = useParams();
  const [eventId, setEventId] = useState(urlEventCode || "");
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Auth form states
  const [showAuthForm, setShowAuthForm] = useState(false);
  const [authMode, setAuthMode] = useState("login"); // "login" or "register"
  const [authLoading, setAuthLoading] = useState(false);
  const [authData, setAuthData] = useState({
    email: "",
    password: "",
    name: "",
  });

  // Selfie upload states
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfieError, setSelfieError] = useState("");

  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (urlEventCode) {
      fetchEventDetails(urlEventCode);
    }
  }, [urlEventCode]);

  // Auto-join when user becomes authenticated
  useEffect(() => {
    if (isAuthenticated && event && urlEventCode) {
      handleAutoJoin();
    }
  }, [isAuthenticated, event]);

  const fetchEventDetails = async (id) => {
    if (!id) return;

    setLoading(true);
    setError("");

    try {
      // Fetch by event code using public endpoint (no auth required)
      const response = await eventsAPI.getByCodePublic(id.toUpperCase());
      setEvent(response.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError("Event not found. Please check the event code.");
      } else {
        setError("Failed to load event details.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAutoJoin = async () => {
    if (!event || joining) return;

    setJoining(true);
    setError("");

    try {
      await eventsAPI.join(event.event_code);
      setSuccess("Successfully joined the event! Redirecting...");

      // Redirect to event page after a short delay
      setTimeout(() => {
        navigate(`/event/${event.event_code}`);
      }, 1500);
    } catch (err) {
      if (
        err.response?.status === 400 &&
        err.response?.data?.detail?.includes("Already registered")
      ) {
        // User is already registered, just redirect
        setSuccess("You're already registered for this event! Redirecting...");
        setTimeout(() => {
          navigate(`/event/${event.event_code}`);
        }, 1500);
      } else if (
        err.response?.status === 400 &&
        err.response?.data?.detail?.includes("Cannot join your own event")
      ) {
        // User is the owner, redirect to event management
        setSuccess("This is your event! Redirecting to management page...");
        setTimeout(() => {
          navigate(`/event/${event.event_code}`);
        }, 1500);
      } else {
        setError(
          err.response?.data?.detail || "Failed to join event automatically."
        );
        setJoining(false);
      }
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setError("");
    setSelfieError("");

    try {
      if (authMode === "register") {
        // Check if selfie is required for registration
        if (!selfieFile) {
          setSelfieError("Please upload a selfie for face recognition");
          setAuthLoading(false);
          return;
        }

        // Use the new selfie registration endpoint
        await eventsAPI.registerWithSelfie(
          event.event_code,
          authData,
          selfieFile
        );

        setSuccess("Registration successful! Logging you in...");

        // Auto-login the newly registered user
        try {
          const loginResult = await login(authData.email, authData.password);
          if (loginResult.success) {
            setSuccess(
              "Registration and login successful! Redirecting to event..."
            );

            // Redirect to event page after successful login
            setTimeout(() => {
              navigate(`/event/${event.event_code}`);
            }, 1500);
          } else {
            setSuccess("Registration successful! Please login to continue.");
            setAuthMode("login");
            // Clear password for security
            setAuthData((prev) => ({ ...prev, password: "" }));
          }
        } catch (loginError) {
          console.error("Auto-login failed:", loginError);
          setSuccess("Registration successful! Please login to continue.");
          setAuthMode("login");
          // Clear password for security
          setAuthData((prev) => ({ ...prev, password: "" }));
        }
        return;
      }

      // Login for existing users
      const loginResult = await login(authData.email, authData.password);
      if (loginResult.success) {
        setShowAuthForm(false);
        setSuccess("Authentication successful! Joining event...");
      } else {
        setError(loginResult.error);
        setAuthLoading(false);
        return;
      }
    } catch (err) {
      console.error("Auth error:", err.response?.data);

      let errorMessage = `Failed to ${authMode}. Please try again.`;

      if (err.response?.data) {
        const errorData = err.response.data;

        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          // Handle validation errors array
          errorMessage = errorData.detail
            .map((error) => error.msg || error)
            .join(", ");
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      }

      setError(errorMessage);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleAuthInputChange = (e) => {
    setAuthData({
      ...authData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSelfieSelect = (file, error) => {
    setSelfieFile(file);
    setSelfieError(error || "");
  };

  const handleEventIdChange = (e) => {
    setEventId(e.target.value);
    setError("");
    setSuccess("");
  };

  const handleLookupEvent = () => {
    if (eventId.trim()) {
      fetchEventDetails(eventId.trim());
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="join-event-page">
      <div className="container">
        <div className="page-header">
          <h1>Join Event</h1>
          <p>
            {urlEventCode
              ? "You've been invited to join an event!"
              : "Enter an event ID or use a shared link to join an event"}
          </p>
        </div>

        {!urlEventCode && (
          <div className="join-form-container">
            <div className="event-lookup">
              <div className="form-group">
                <label htmlFor="eventId">Event Code</label>
                <div className="input-group">
                  <input
                    type="text"
                    id="eventId"
                    value={eventId}
                    onChange={handleEventIdChange}
                    placeholder="Enter event code (e.g., ABC123)"
                    maxLength="6"
                    style={{ textTransform: "uppercase" }}
                  />
                  <button
                    className="btn btn-primary"
                    onClick={handleLookupEvent}
                    disabled={!eventId.trim() || loading}
                  >
                    {loading ? "Looking up..." : "Find Event"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {error && <div className="error">{error}</div>}
        {success && <div className="success">{success}</div>}

        {event && (
          <div className="event-details">
            <h3>Event Details</h3>
            <div className="event-card">
              <h4>{event.event_name}</h4>
              <div className="event-date">
                📅 {formatDate(event.event_date)}
              </div>
              {event.description && (
                <p className="event-description">{event.description}</p>
              )}
              <div className="event-stats">
                <span>👥 {event.guest_count} guests</span>
                <span>📸 {event.photo_count} photos</span>
              </div>
              <div className="event-owner">
                <small>Hosted by {event.owner.name}</small>
              </div>

              <div className="join-actions">
                {isAuthenticated ? (
                  <div className="authenticated-state">
                    {joining ? (
                      <div className="joining-status">
                        <p>🎉 Joining event...</p>
                      </div>
                    ) : (
                      <button
                        className="btn btn-primary"
                        onClick={handleAutoJoin}
                      >
                        Join Event
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="auth-options">
                    {!showAuthForm ? (
                      <>
                        <p className="auth-prompt">
                          To join this event, please login or create an account:
                        </p>
                        <div className="auth-buttons">
                          <button
                            className="btn btn-primary"
                            onClick={() => {
                              setAuthMode("login");
                              setShowAuthForm(true);
                            }}
                          >
                            Login
                          </button>
                          <button
                            className="btn btn-secondary"
                            onClick={() => {
                              setAuthMode("register");
                              setShowAuthForm(true);
                            }}
                          >
                            Create Account
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="auth-form">
                        <h4>
                          {authMode === "login" ? "Login" : "Create Account"}
                        </h4>
                        <form onSubmit={handleAuth}>
                          {authMode === "register" && (
                            <>
                              <div className="form-group">
                                <label htmlFor="name">Full Name</label>
                                <input
                                  type="text"
                                  id="name"
                                  name="name"
                                  value={authData.name}
                                  onChange={handleAuthInputChange}
                                  required
                                  placeholder="Enter your full name"
                                />
                              </div>
                              <SelfieUpload
                                onFileSelect={handleSelfieSelect}
                                selectedFile={selfieFile}
                                error={selfieError}
                                disabled={authLoading}
                                required={true}
                              />
                            </>
                          )}
                          <div className="form-group">
                            <label htmlFor="email">Email</label>
                            <input
                              type="email"
                              id="email"
                              name="email"
                              value={authData.email}
                              onChange={handleAuthInputChange}
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
                              value={authData.password}
                              onChange={handleAuthInputChange}
                              required
                              placeholder="Enter your password"
                              minLength="6"
                            />
                          </div>
                          <div className="form-actions">
                            <button
                              type="submit"
                              className="btn btn-primary"
                              disabled={authLoading}
                            >
                              {authLoading
                                ? authMode === "login"
                                  ? "Logging in..."
                                  : "Creating account..."
                                : authMode === "login"
                                ? "Login & Join Event"
                                : "Register & Join Event"}
                            </button>
                            <button
                              type="button"
                              className="btn btn-secondary"
                              onClick={() => setShowAuthForm(false)}
                              disabled={authLoading}
                            >
                              Cancel
                            </button>
                          </div>
                          <p className="auth-switch">
                            {authMode === "login" ? (
                              <>
                                Don't have an account?{" "}
                                <button
                                  type="button"
                                  className="link-button"
                                  onClick={() => setAuthMode("register")}
                                >
                                  Create one here
                                </button>
                              </>
                            ) : (
                              <>
                                Already have an account?{" "}
                                <button
                                  type="button"
                                  className="link-button"
                                  onClick={() => setAuthMode("login")}
                                >
                                  Login here
                                </button>
                              </>
                            )}
                          </p>
                        </form>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {!urlEventCode && (
          <div className="join-help">
            <h4>How to join an event:</h4>
            <ul>
              <li>Get the event ID from the event organizer</li>
              <li>Enter the ID in the field above and click "Find Event"</li>
              <li>Review the event details and click "Join Event"</li>
              <li>You can also use a direct link shared by the organizer</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default JoinEvent;
