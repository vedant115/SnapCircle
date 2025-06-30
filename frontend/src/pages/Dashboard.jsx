import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { eventsAPI } from "../utils/api";

const Dashboard = () => {
  const { user } = useAuth();
  const [ownedEvents, setOwnedEvents] = useState([]);
  const [registeredEvents, setRegisteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const [ownedResponse, registeredResponse] = await Promise.all([
        eventsAPI.getOwned(),
        eventsAPI.getRegistered(),
      ]);

      setOwnedEvents(ownedResponse.data);
      setRegisteredEvents(registeredResponse.data);
    } catch (err) {
      setError("Failed to load events");
      console.error("Error fetching events:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h1>Welcome back, {user?.name}!</h1>
          <p>Manage your events and discover new photos</p>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="dashboard-actions">
          <div className="action-cards">
            <Link to="/create-event" className="action-card">
              <div className="action-icon">📅</div>
              <h3>Create Event</h3>
              <p>Start a new event and invite guests to share photos</p>
            </Link>

            <Link to="/join-event" className="action-card">
              <div className="action-icon">🎉</div>
              <h3>Join Event</h3>
              <p>Join an existing event using an event ID or link</p>
            </Link>
          </div>
        </div>

        <div className="events-section">
          <div className="events-grid">
            <div className="events-column">
              <h2>Events You Created ({ownedEvents.length})</h2>
              {ownedEvents.length === 0 ? (
                <div className="empty-state">
                  <p>You haven't created any events yet.</p>
                  <Link to="/create-event" className="btn btn-primary">
                    Create Your First Event
                  </Link>
                </div>
              ) : (
                <div className="events-list">
                  {ownedEvents.map((event) => (
                    <div key={event.id} className="event-card">
                      <h3>{event.event_name}</h3>
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
                      <div className="event-actions">
                        <Link
                          to={`/event/${event.event_code}`}
                          className="btn btn-primary"
                        >
                          Manage
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="events-column">
              <h2>Events You're Attending ({registeredEvents.length})</h2>
              {registeredEvents.length === 0 ? (
                <div className="empty-state">
                  <p>You're not attending any events yet.</p>
                  <Link to="/join-event" className="btn btn-primary">
                    Join an Event
                  </Link>
                </div>
              ) : (
                <div className="events-list">
                  {registeredEvents.map((event) => (
                    <div key={event.id} className="event-card">
                      <h3>{event.event_name}</h3>
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
                      <div className="event-actions">
                        <Link
                          to={`/event/${event.event_code}`}
                          className="btn btn-primary"
                        >
                          View
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
