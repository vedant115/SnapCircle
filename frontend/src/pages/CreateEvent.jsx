import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { eventsAPI } from "../utils/api";

const CreateEvent = () => {
  const [formData, setFormData] = useState({
    event_name: "",
    event_date: "",
    description: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

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
      const response = await eventsAPI.create(formData);
      const event = response.data;
      console.log("✅ Event created:", event);

      // Redirect to the event management page using event code
      navigate(`/event/${event.event_code}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create event");
    } finally {
      setLoading(false);
    }
  };

  // Get today's date in YYYY-MM-DD format for min date
  const today = new Date().toISOString().split("T")[0];

  return (
    <div className="create-event-page">
      <div className="container">
        <div className="page-header">
          <h1>Create New Event</h1>
          <p>Set up your event and start collecting memories</p>
        </div>

        <div className="form-container">
          <form onSubmit={handleSubmit} className="event-form">
            {error && <div className="error">{error}</div>}

            <div className="form-group">
              <label htmlFor="event_name">Event Name *</label>
              <input
                type="text"
                id="event_name"
                name="event_name"
                value={formData.event_name}
                onChange={handleInputChange}
                required
                placeholder="e.g., Sarah's Birthday Party, Company Retreat 2024"
                maxLength="200"
              />
            </div>

            <div className="form-group">
              <label htmlFor="event_date">Event Date *</label>
              <input
                type="date"
                id="event_date"
                name="event_date"
                value={formData.event_date}
                onChange={handleInputChange}
                required
                min={today}
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description (Optional)</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Add any additional details about your event..."
                rows="4"
                maxLength="1000"
              />
              <small className="form-help">
                {formData.description.length}/1000 characters
              </small>
            </div>

            <div className="form-actions">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => navigate("/dashboard")}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? "Creating..." : "Create Event"}
              </button>
            </div>
          </form>

          <div className="event-preview">
            <h3>Event Preview</h3>
            <div className="preview-card">
              <h4>{formData.event_name || "Event Name"}</h4>
              <div className="preview-date">
                📅{" "}
                {formData.event_date
                  ? new Date(formData.event_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
                  : "Event Date"}
              </div>
              {formData.description && (
                <p className="preview-description">{formData.description}</p>
              )}
              <div className="preview-stats">
                <span>👥 0 guests</span>
                <span>📸 0 photos</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateEvent;
