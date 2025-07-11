import React, { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { useAuth } from "../context/AuthContext";
import { photosAPI, authAPI } from "../utils/api";
import SelfieUpload from "../components/SelfieUpload";

const Profile = () => {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Selfie upload states
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfieError, setSelfieError] = useState("");

  const handleSelfieSelect = (file, error) => {
    setSelfieFile(file);
    setSelfieError(error || "");
    setError("");
    setSuccess("");
  };

  const handleSelfieUpload = async () => {
    if (!selfieFile) {
      setSelfieError("Please select a selfie to upload");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await photosAPI.uploadProfile(selfieFile);
      toast.success(
        "Profile photo uploaded successfully! Face recognition is now enabled for your account."
      );
      setSelfieFile(null);

      // Refresh user data to get updated profile
      if (refreshUser) {
        await refreshUser();
      }
    } catch (err) {
      console.error("Profile upload error:", err);
      const errorMessage =
        err.response?.data?.detail ||
        "Failed to upload profile photo. Please try again.";
      toast.error(errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="profile-page">
        <div className="container">
          <div className="error">Please log in to view your profile.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="container">
        <div className="page-header">
          <h1>My Profile</h1>
          <p>Manage your account settings and profile photo</p>
        </div>

        <div className="profile-content">
          <div className="profile-info">
            <h3>Account Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <label>Name:</label>
                <span>{user.name}</span>
              </div>
              <div className="info-item">
                <label>Email:</label>
                <span>{user.email}</span>
              </div>
              <div className="info-item">
                <label>Member since:</label>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <div className="info-item">
                <label>Face Recognition:</label>
                <span
                  className={user.selfie_image_path ? "enabled" : "disabled"}
                >
                  {user.selfie_image_path ? "✅ Enabled" : "❌ Not Set Up"}
                </span>
              </div>
            </div>
          </div>

          <div className="profile-photo-section">
            <div className="upload-section">
              <SelfieUpload
                onFileSelect={handleSelfieSelect}
                selectedFile={selfieFile}
                error={selfieError}
                disabled={loading}
                required={false}
              />

              {selfieFile && (
                <div className="upload-actions">
                  <button
                    className="btn btn-primary"
                    onClick={handleSelfieUpload}
                    disabled={loading}
                  >
                    {loading ? "Uploading..." : "Upload Profile Photo"}
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => {
                      setSelfieFile(null);
                      setSelfieError("");
                    }}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>

            <div className="privacy-note">
              <p>
                We don't store your actual face image, only the mathematical
                data (embeddings)
              </p>
            </div>

            {error && <div className="error">{error}</div>}
            {success && <div className="success">{success}</div>}
          </div>
        </div>
      </div>

      <style jsx>{`
        .profile-page {
          min-height: 100vh;
          background: #f5f5f5;
          padding: 2rem;
          overflow: hidden;
        }

        .container {
          height: 100%;
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
        }

        .page-header {
          margin-bottom: 2rem;
          text-align: center;
        }

        .profile-content {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 2rem;
          flex: 1;
          height: calc(100vh - 200px);
        }

        .profile-info,
        .profile-photo-section {
          background: white;
          border-radius: 8px;
          padding: 2rem;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          color: #333;
          overflow-y: auto;
        }

        .profile-info h3,
        .profile-photo-section h3 {
          color: #333;
          margin-bottom: 1rem;
          margin-top: 0;
        }

        .profile-photo-section h4 {
          color: #333;
        }

        .photo-status p {
          color: #666;
        }

        .info-grid {
          display: grid;
          gap: 1rem;
          margin-top: 1rem;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 0;
          border-bottom: 1px solid #eee;
        }

        .info-item:last-child {
          border-bottom: none;
        }

        .info-item label {
          font-weight: 600;
          color: #333;
        }

        .info-item span {
          color: #333;
        }

        .enabled {
          color: #27ae60;
          font-weight: 600;
        }

        .disabled {
          color: #e74c3c;
          font-weight: 600;
        }

        .section-description {
          color: #666;
          margin-bottom: 1.5rem;
          line-height: 1.5;
        }

        .current-photo {
          margin-bottom: 2rem;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 6px;
        }

        .photo-status {
          margin-top: 0.5rem;
        }

        .status-indicator {
          color: #27ae60;
          font-weight: 600;
        }

        .upload-actions {
          margin-top: 1rem;
          display: flex;
          gap: 1rem;
        }

        .privacy-note {
          margin-top: 1.5rem;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 6px;
          border-left: 4px solid #007bff;
        }

        .privacy-note p {
          margin: 0;
          color: #666;
          font-size: 0.9rem;
          font-style: italic;
        }

        .error {
          color: #e74c3c;
          background: #fdf2f2;
          padding: 1rem;
          border-radius: 6px;
          margin-top: 1rem;
        }

        .success {
          color: #27ae60;
          background: #f2fdf2;
          padding: 1rem;
          border-radius: 6px;
          margin-top: 1rem;
        }

        @media (max-width: 768px) {
          .profile-page {
            padding: 1rem;
          }

          .profile-content {
            grid-template-columns: 1fr;
            gap: 1rem;
            height: auto;
          }

          .profile-info,
          .profile-photo-section {
            padding: 1.5rem;
          }

          .upload-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default Profile;
