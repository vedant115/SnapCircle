import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { eventsAPI, photosAPI } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import PhotoUpload from "../components/PhotoUpload";
import PhotoGallery from "../components/PhotoGallery";
import { getPhotoUrl } from "../utils/photoUtils";
import "./EventPage.css";

const EventPage = () => {
  const { eventCode } = useParams();
  const [event, setEvent] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [guests, setGuests] = useState([]);
  const [qrCode, setQrCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  // Face processing states
  const [faceProcessing, setFaceProcessing] = useState(false);
  const [faceProcessingProgress, setFaceProcessingProgress] = useState(null);
  const [faceProcessingResults, setFaceProcessingResults] = useState(null);

  // My photos states
  const [myPhotos, setMyPhotos] = useState([]);
  const [myPhotosLoading, setMyPhotosLoading] = useState(false);

  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (eventCode) {
      fetchEventData();
    }
  }, [eventCode]);

  // Fetch event photos when event is loaded
  useEffect(() => {
    if (event?.event_code && user) {
      fetchEventPhotos();
    }
  }, [event?.event_code, user]);

  // Fetch my photos when switching to my-photos tab or when face processing completes
  useEffect(() => {
    if (
      activeTab === "my-photos" &&
      user?.selfie_image_path &&
      event?.event_code
    ) {
      fetchMyPhotos();
    }
  }, [
    activeTab,
    user?.selfie_image_path,
    event?.event_code,
    faceProcessingResults,
  ]);

  const fetchEventData = async () => {
    try {
      setLoading(true);
      console.log("🔄 Fetching event data for event code:", eventCode);

      // Fetch event by event code
      const eventResponse = await eventsAPI.getByCode(eventCode.toUpperCase());
      console.log("📅 Event data received:", eventResponse.data);
      console.log("📊 Photo count from API:", eventResponse.data.photo_count);
      console.log("👥 Guest count from API:", eventResponse.data.guest_count);
      console.log("👑 Is owner:", eventResponse.data.owner_id === user?.id);
      setEvent(eventResponse.data);

      // Check if user has full access (owner or registered)
      // If guest_count > 0 OR photo_count > 0, it means the user is registered
      // (backend only returns actual counts for registered users/owners)
      const hasFullAccess =
        eventResponse.data.guest_count > 0 ||
        eventResponse.data.photo_count > 0 ||
        eventResponse.data.owner_id === user?.id;

      console.log("🔐 Access check:", {
        guest_count: eventResponse.data.guest_count,
        photo_count: eventResponse.data.photo_count,
        is_owner: eventResponse.data.owner_id === user?.id,
        hasFullAccess: hasFullAccess,
      });

      // Only fetch photos if user has full access
      if (hasFullAccess) {
        try {
          const photosResponse = await photosAPI.getEventPhotos(eventCode);
          console.log("📸 Photos data received:", photosResponse.data);
          setPhotos(photosResponse.data);
        } catch (photoErr) {
          console.warn(
            "Could not fetch photos - user may not be registered:",
            photoErr
          );
          setPhotos([]);
        }
      } else {
        console.log("ℹ️ User has basic access only - not fetching photos");
        setPhotos([]);
      }

      // If user is owner, fetch additional data
      if (eventResponse.data.owner_id === user?.id) {
        console.log("👑 User is owner, fetching additional data...");
        try {
          // Use the event code for all API calls
          const eventCode = eventResponse.data.event_code;

          const guestsResponse = await eventsAPI.getGuests(eventCode);
          console.log("👥 Guests data received:", guestsResponse.data);
          setGuests(guestsResponse.data);

          const qrResponse = await eventsAPI.getQRCode(eventCode);
          console.log("📱 QR code received:", qrResponse.data);
          setQrCode(qrResponse.data.qr_code);
        } catch (err) {
          console.error("Error fetching owner data:", err);
        }
      }
    } catch (err) {
      setError("Failed to load event data");
      console.error("Error fetching event:", err);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoUpload = async (newPhotos) => {
    console.log("📸 Photo upload completed, updating state...");
    setPhotos((prevPhotos) => [...prevPhotos, ...newPhotos]);

    // Refresh event data to update photo count
    console.log("🔄 Refreshing event data to update photo count...");
    await fetchEventData();

    // Also refresh photos to ensure we have the latest list
    if (event?.event_code) {
      console.log("🔄 Refreshing photos list...");
      await fetchEventPhotos();
    }
  };

  const handleProcessImages = async () => {
    if (photos.length === 0) {
      alert("No photos to process");
      return;
    }

    const confirmProcess = window.confirm(
      `🔄 Process ${photos.length} photos for face recognition?\n\n` +
        `This will:\n` +
        `• Detect faces in all event photos\n` +
        `• Match faces with registered users\n` +
        `• Enable personalized photo viewing\n\n` +
        `Processing may take a few minutes depending on the number of photos.`
    );

    if (!confirmProcess) return;

    setFaceProcessing(true);
    setFaceProcessingProgress({
      current: 0,
      total: photos.length,
      status: "Starting face processing...",
    });
    setFaceProcessingResults(null);
    setError("");

    try {
      // Get all photo IDs
      const photoIds = photos.map((photo) => photo.id);

      // Update progress
      setFaceProcessingProgress({
        current: 0,
        total: photos.length,
        status: "Analyzing photos for faces...",
      });

      // Call the face processing API
      const response = await photosAPI.processFaces(photoIds);

      // Update progress to completion
      setFaceProcessingProgress({
        current: photos.length,
        total: photos.length,
        status: "Face processing completed!",
      });

      // Store results
      setFaceProcessingResults(response.data);

      // Show success message
      setTimeout(() => {
        setFaceProcessing(false);
        setFaceProcessingProgress(null);

        alert(
          `✅ Face processing completed!\n\n` +
            `📊 Results:\n` +
            `• Processed: ${response.data.processed_photos} photos\n` +
            `• Faces detected: ${response.data.total_faces_detected}\n` +
            `• Faces matched: ${response.data.total_faces_matched}\n\n` +
            `Users can now view their personalized photos!`
        );
      }, 1500);
    } catch (err) {
      console.error("Face processing error:", err);
      setError(
        err.response?.data?.detail ||
          "Failed to process faces. Please try again."
      );
      setFaceProcessing(false);
      setFaceProcessingProgress(null);
    }
  };

  const handleDeleteEvent = async () => {
    const confirmDelete = window.confirm(
      `⚠️ Are you sure you want to delete "${event.event_name}"?\n\nThis will permanently delete:\n• The event\n• All ${photos.length} photos\n• All guest registrations\n\nThis action cannot be undone.`
    );

    if (!confirmDelete) return;

    try {
      await eventsAPI.delete(event.event_code);
      alert("✅ Event deleted successfully!");
      navigate("/dashboard");
    } catch (err) {
      console.error("Error deleting event:", err);
      alert("❌ Failed to delete event. Please try again.");
    }
  };

  const handlePhotoDelete = async (photoId) => {
    console.log("🗑️ Photo deleted, updating state...");
    setPhotos((prevPhotos) =>
      prevPhotos.filter((photo) => photo.id !== photoId)
    );

    // Refresh event data to update photo count
    console.log("🔄 Refreshing event data to update photo count...");
    await fetchEventData();

    // Also refresh photos to ensure we have the latest list
    if (event?.event_code) {
      console.log("🔄 Refreshing photos list...");
      await fetchEventPhotos();
    }
  };

  const fetchEventPhotos = async () => {
    if (!event?.event_code) return;

    try {
      console.log("📸 Fetching photos for event:", event.event_code);
      const response = await photosAPI.getEventPhotos(event.event_code);
      console.log("📸 Photos received:", response.data);
      setPhotos(response.data);
    } catch (err) {
      console.error("Error fetching photos:", err);
      // Don't show error to user as this might be due to permissions
      // Just keep photos array empty
      setPhotos([]);
    }
  };

  const fetchMyPhotos = async () => {
    if (!user?.id || !event?.event_code) return;

    setMyPhotosLoading(true);
    try {
      // Fetch photos with face recognition data
      const response = await photosAPI.getEventPhotosWithFaces(
        event.event_code
      );

      // Filter photos where the current user appears
      const photosWithMe = response.data.filter(
        (photo) =>
          photo.faces &&
          photo.faces.some((face) => face.matched_user_id === user.id)
      );

      setMyPhotos(photosWithMe);
    } catch (err) {
      console.error("Error fetching my photos:", err);
      // If the endpoint doesn't exist or fails, show empty state
      setMyPhotos([]);
    } finally {
      setMyPhotosLoading(false);
    }
  };

  const handleJoinEvent = async () => {
    try {
      setLoading(true);
      await eventsAPI.join(event.event_code);
      alert("✅ Successfully joined the event!");
      // Refresh the page data to show full access
      await fetchEventData();
    } catch (err) {
      console.error("Error joining event:", err);
      if (
        err.response?.status === 400 &&
        err.response?.data?.detail?.includes("Already registered")
      ) {
        alert("✅ You're already registered for this event!");
        await fetchEventData();
      } else {
        alert("❌ Failed to join event. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveEvent = async () => {
    const confirmLeave = window.confirm(
      `⚠️ Are you sure you want to leave "${event.event_name}"?\n\nYou will no longer have access to event photos and updates.\n\nYou can rejoin later using the event code: ${event.event_code}`
    );

    if (!confirmLeave) return;

    try {
      await eventsAPI.leave(event.event_code);
      alert("✅ Successfully left the event!");
      navigate("/dashboard");
    } catch (err) {
      console.error("Error leaving event:", err);
      alert("❌ Failed to leave event. Please try again.");
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const isOwner = event?.owner_id === user?.id;
  const isGuest = !isOwner;

  // Check if user needs to join the event (has basic access but not registered)
  const needsToJoin =
    event && !isOwner && event.guest_count === 0 && event.photo_count === 0;

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">Loading event...</div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="error-page">
        <div className="container">
          <div className="error-content">
            <h2>Event Not Found</h2>
            <p>
              {error ||
                "The event you're looking for doesn't exist or you don't have access to it."}
            </p>
            <button
              className="btn btn-primary"
              onClick={() => navigate("/dashboard")}
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="event-page">
      <div className="container">
        <div className="event-header">
          <div className="event-info">
            <h1>{event.event_name}</h1>
            <div className="event-meta">
              <span className="event-date">
                📅 {formatDate(event.event_date)}
              </span>
              <span className="event-owner">
                {isOwner ? "👑 Your Event" : `🎉 Hosted by ${event.owner.name}`}
              </span>
            </div>
            {event.description && (
              <p className="event-description">{event.description}</p>
            )}
            <div className="event-stats">
              <span>👥 {event.guest_count} guests</span>
              <span>📸 {event.photo_count} photos</span>
            </div>
          </div>

          <div className="event-actions">
            <button
              className="btn btn-secondary"
              onClick={() => navigate("/dashboard")}
            >
              Back to Dashboard
            </button>
            {needsToJoin && (
              <button
                className="btn btn-primary"
                onClick={handleJoinEvent}
                disabled={loading}
                title="Join this event to access photos and features"
              >
                {loading ? "Joining..." : "🎉 Join Event"}
              </button>
            )}
            {isOwner && (
              <>
                <button
                  className="btn btn-primary"
                  onClick={handleProcessImages}
                  disabled={photos.length === 0 || faceProcessing}
                  title={
                    photos.length === 0
                      ? "No photos to process"
                      : faceProcessing
                      ? "Processing faces..."
                      : "Process all event images for face recognition"
                  }
                >
                  {faceProcessing ? "🔄 Processing..." : "🔄 Process Images"}
                </button>
                <button
                  className="btn btn-danger"
                  onClick={handleDeleteEvent}
                  title="Permanently delete this event and all photos"
                >
                  🗑️ Delete Event
                </button>
              </>
            )}
            {isGuest && !needsToJoin && (
              <button
                className="btn btn-danger"
                onClick={handleLeaveEvent}
                title="Leave this event and remove your registration"
              >
                🚪 Leave Event
              </button>
            )}
          </div>

          {/* Face Processing Progress Bar */}
          {faceProcessing && faceProcessingProgress && (
            <div className="face-processing-overlay">
              <div className="face-processing-modal">
                <div className="processing-header">
                  <h3>🔄 Processing Photos for Face Recognition</h3>
                  <p>{faceProcessingProgress.status}</p>
                </div>

                <div className="progress-container">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${
                          (faceProcessingProgress.current /
                            faceProcessingProgress.total) *
                          100
                        }%`,
                      }}
                    ></div>
                  </div>
                  <div className="progress-text">
                    {faceProcessingProgress.current} /{" "}
                    {faceProcessingProgress.total} photos
                  </div>
                </div>

                <div className="processing-info">
                  <div className="info-item">
                    <span className="info-icon">🔍</span>
                    <span>Detecting faces in photos</span>
                  </div>
                  <div className="info-item">
                    <span className="info-icon">🤖</span>
                    <span>Matching faces with registered users</span>
                  </div>
                  <div className="info-item">
                    <span className="info-icon">💾</span>
                    <span>Saving face recognition data</span>
                  </div>
                </div>

                <p className="processing-note">
                  Please don't close this page while processing is in progress.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="event-tabs">
          <button
            className={`tab ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>
          {isOwner && !needsToJoin && (
            <button
              className={`tab ${activeTab === "photos" ? "active" : ""}`}
              onClick={() => setActiveTab("photos")}
            >
              All Photos ({photos.length})
            </button>
          )}
          {isGuest && !needsToJoin && (
            <button
              className={`tab ${activeTab === "my-photos" ? "active" : ""}`}
              onClick={() => setActiveTab("my-photos")}
            >
              My Photos ({myPhotos.length})
            </button>
          )}
          {isOwner && !needsToJoin && (
            <>
              <button
                className={`tab ${activeTab === "guests" ? "active" : ""}`}
                onClick={() => setActiveTab("guests")}
              >
                Guests ({guests.length})
              </button>
              <button
                className={`tab ${activeTab === "share" ? "active" : ""}`}
                onClick={() => setActiveTab("share")}
              >
                Share Event
              </button>
            </>
          )}
        </div>

        <div className="tab-content">
          {activeTab === "overview" && (
            <div className="overview-tab">
              <div className="overview-grid">
                <div className="overview-card">
                  <h3>Event Details</h3>
                  <div className="detail-item">
                    <strong>Event Name:</strong> {event.event_name}
                  </div>
                  <div className="detail-item">
                    <strong>Date:</strong> {formatDate(event.event_date)}
                  </div>
                  <div className="detail-item">
                    <strong>Organizer:</strong> {event.owner.name}
                  </div>
                  {isOwner && (
                    <>
                      <div className="detail-item">
                        <strong>Created:</strong> {formatDate(event.created_at)}
                      </div>
                      <div className="detail-item">
                        <strong>Event Code:</strong> {event.event_code}
                      </div>
                    </>
                  )}
                  {event.description && (
                    <div className="detail-item">
                      <strong>Description:</strong>
                      <p>{event.description}</p>
                    </div>
                  )}
                </div>

                <div className="overview-card">
                  <h3>{isOwner ? "Event Statistics" : "Photo Statistics"}</h3>
                  <div className="stats-grid">
                    {isOwner && (
                      <div className="stat-item">
                        <div className="stat-number">{event.guest_count}</div>
                        <div className="stat-label">Guests</div>
                      </div>
                    )}
                    <div className="stat-item">
                      <div className="stat-number">{event.photo_count}</div>
                      <div className="stat-label">
                        {isOwner ? "Total Photos" : "Event Photos"}
                      </div>
                    </div>
                    {isGuest && (
                      <div className="stat-item">
                        <div className="stat-number">{myPhotos.length}</div>
                        <div className="stat-label">My Photos</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {photos.length > 0 && isOwner && (
                <div className="recent-photos">
                  <h3>Recent Photos</h3>
                  <div className="photo-preview">
                    {photos.slice(0, 6).map((photo) => (
                      <div key={photo.id} className="photo-thumbnail">
                        <img
                          src={getPhotoUrl(photo.image_path)}
                          alt="Event photo"
                        />
                      </div>
                    ))}
                  </div>
                  {photos.length > 6 && (
                    <button
                      className="btn btn-primary"
                      onClick={() => setActiveTab("photos")}
                    >
                      View All Photos
                    </button>
                  )}
                </div>
              )}

              {needsToJoin && (
                <div className="join-prompt">
                  <h3>Join This Event</h3>
                  <div className="join-message">
                    <div className="join-icon">🎉</div>
                    <h4>You're Almost There!</h4>
                    <p>
                      Click the "Join Event" button above to access photos,
                      participate in the event, and get personalized features.
                    </p>
                    <div className="join-benefits">
                      <div className="benefit-item">
                        <span className="benefit-icon">📸</span>
                        <span>Access event photos</span>
                      </div>
                      <div className="benefit-item">
                        <span className="benefit-icon">🤖</span>
                        <span>Get photos where you appear</span>
                      </div>
                      <div className="benefit-item">
                        <span className="benefit-icon">🔔</span>
                        <span>Receive event updates</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {isGuest && !needsToJoin && (
                <div className="guest-info">
                  <h3>Your Event Experience</h3>
                  <div className="guest-features">
                    <div className="feature-item">
                      <div className="feature-icon">📸</div>
                      <div className="feature-content">
                        <h4>Personal Photos</h4>
                        <p>
                          View photos where you appear (coming soon with face
                          recognition)
                        </p>
                      </div>
                    </div>
                    <div className="feature-item">
                      <div className="feature-icon">🎉</div>
                      <div className="feature-content">
                        <h4>Event Memories</h4>
                        <p>
                          Access your personalized collection of event moments
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "photos" && isOwner && (
            <div className="photos-tab">
              <div className="photos-header">
                <h3>Event Photos</h3>
              </div>

              <PhotoUpload
                eventId={eventCode}
                onUploadComplete={handlePhotoUpload}
                multiple={true}
                maxFiles={10}
              />

              <PhotoGallery
                photos={photos}
                eventOwnerId={event.owner_id}
                onPhotoDelete={handlePhotoDelete}
              />
            </div>
          )}

          {activeTab === "my-photos" && isGuest && (
            <div className="my-photos-tab">
              <div className="my-photos-header">
                <h3>My Photos</h3>
                <p>Photos where you appear in this event</p>
              </div>

              <div className="my-photos-content">
                {user?.selfie_image_path ? (
                  <div className="face-recognition-active">
                    <div className="status-message">
                      <span className="status-icon">✅</span>
                      <div>
                        <h4>Face Recognition Enabled</h4>
                        <p>
                          We'll automatically identify photos where you appear
                          once the event organizer processes the photos.
                        </p>
                      </div>
                    </div>

                    {myPhotosLoading ? (
                      <div className="waiting-message">
                        <div className="waiting-icon">🔄</div>
                        <h4>Loading Your Photos...</h4>
                        <p>Searching for photos where you appear...</p>
                      </div>
                    ) : myPhotos.length > 0 ? (
                      <div className="my-photos-gallery">
                        {myPhotos.map((photo) => {
                          const myFaces = photo.faces.filter(
                            (face) => face.matched_user_id === user.id
                          );
                          return (
                            <div key={photo.id} className="my-photo-item">
                              <img
                                src={getPhotoUrl(photo.image_path)}
                                alt="Photo where you appear"
                              />
                              <div className="my-photo-overlay">
                                <div className="face-count">
                                  {myFaces.length} face
                                  {myFaces.length !== 1 ? "s" : ""} matched
                                </div>
                                <div className="matched-indicator">
                                  ✅ You appear here
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : faceProcessingResults ? (
                      <div className="waiting-message">
                        <div className="waiting-icon">📷</div>
                        <h4>No Photos Found</h4>
                        <p>
                          Face recognition has been processed, but you don't
                          appear in any photos yet. Upload more photos or ask
                          others to upload photos from the event!
                        </p>

                        <div className="processing-results">
                          <h4>📊 Latest Processing Results</h4>
                          <div className="results-grid">
                            <div className="result-item">
                              <span className="result-number">
                                {faceProcessingResults.processed_photos}
                              </span>
                              <span className="result-label">
                                Photos Processed
                              </span>
                            </div>
                            <div className="result-item">
                              <span className="result-number">
                                {faceProcessingResults.total_faces_detected}
                              </span>
                              <span className="result-label">
                                Faces Detected
                              </span>
                            </div>
                            <div className="result-item">
                              <span className="result-number">
                                {faceProcessingResults.total_faces_matched}
                              </span>
                              <span className="result-label">
                                Faces Matched
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="waiting-message">
                        <div className="waiting-icon">⏳</div>
                        <h4>Waiting for Photo Processing</h4>
                        <p>
                          The event organizer needs to process the photos to
                          enable face recognition. Once processed, your photos
                          will appear here automatically.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="setup-face-recognition">
                    <div className="setup-icon">🤳</div>
                    <h4>Set Up Face Recognition</h4>
                    <p>
                      Upload a selfie to your profile to enable automatic photo
                      identification.
                    </p>
                    <button
                      className="btn btn-primary"
                      onClick={() => navigate("/profile")}
                    >
                      Upload Selfie
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {isOwner && activeTab === "guests" && (
            <div className="guests-tab">
              <h3>Event Guests</h3>
              {guests.length === 0 ? (
                <div className="empty-state">
                  <p>No guests have joined yet.</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => setActiveTab("share")}
                  >
                    Share Event Link
                  </button>
                </div>
              ) : (
                <div className="guests-list">
                  {guests.map((guest) => (
                    <div key={guest.id} className="guest-item">
                      <div className="guest-info">
                        <strong>{guest.name}</strong>
                        <span>{guest.email}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {isOwner && activeTab === "share" && (
            <div className="share-tab">
              <h3>Share Your Event</h3>
              <div className="share-options">
                <div className="share-option">
                  <h4>Event Code</h4>
                  <div className="share-item">
                    <input
                      type="text"
                      value={event.event_code}
                      readOnly
                      className="share-input"
                    />
                    <button className="btn btn-secondary">Copy</button>
                  </div>
                  <p>
                    Share this code with guests so they can join your event.
                  </p>
                </div>

                <div className="share-option">
                  <h4>Direct Link</h4>
                  <div className="share-item">
                    <input
                      type="text"
                      value={`http://localhost:3000/join/${event.event_code}`}
                      readOnly
                      className="share-input"
                    />
                    <button className="btn btn-secondary">Copy</button>
                  </div>
                  <p>Guests can click this link to join directly.</p>
                </div>

                {qrCode && (
                  <div className="share-option">
                    <h4>QR Code</h4>
                    <div className="qr-code-container">
                      <img src={qrCode} alt="Event QR Code" />
                      <p>Guests can scan this QR code to join the event.</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventPage;
