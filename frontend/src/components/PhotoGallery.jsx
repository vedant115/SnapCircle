import React, { useState } from "react";
import { photosAPI } from "../utils/api";
import { useAuth } from "../context/AuthContext";
import { getPhotoUrl } from "../utils/photoUtils";

const PhotoGallery = ({ photos, eventOwnerId, onPhotoDelete }) => {
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const { user } = useAuth();

  const openPhotoModal = (photo) => {
    setSelectedPhoto(photo);
  };

  const closePhotoModal = () => {
    setSelectedPhoto(null);
  };

  const handleDeletePhoto = async (photoId) => {
    if (!window.confirm("Are you sure you want to delete this photo?")) {
      return;
    }

    setDeleting(photoId);
    try {
      await photosAPI.delete(photoId);
      if (onPhotoDelete) {
        onPhotoDelete(photoId);
      }
      if (selectedPhoto?.id === photoId) {
        closePhotoModal();
      }
    } catch (err) {
      alert("Failed to delete photo");
    } finally {
      setDeleting(null);
    }
  };

  const canDeletePhoto = (photo) => {
    return photo.uploaded_by === user?.id || eventOwnerId === user?.id;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (photos.length === 0) {
    return (
      <div className="empty-gallery">
        <div className="empty-icon">📸</div>
        <h3>No photos yet</h3>
        <p>Be the first to share a photo from this event!</p>
      </div>
    );
  }

  return (
    <>
      <div className="photo-gallery">
        {photos.map((photo) => (
          <div key={photo.id} className="photo-item">
            <img
              src={getPhotoUrl(photo.image_path)}
              alt="Event photo"
              onClick={() => openPhotoModal(photo)}
            />
            <div className="photo-overlay">
              <button
                className="btn btn-secondary"
                onClick={() => openPhotoModal(photo)}
              >
                View
              </button>
              {canDeletePhoto(photo) && (
                <button
                  className="btn btn-danger"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeletePhoto(photo.id);
                  }}
                  disabled={deleting === photo.id}
                >
                  {deleting === photo.id ? "..." : "Delete"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {selectedPhoto && (
        <div className="photo-modal" onClick={closePhotoModal}>
          <div
            className="photo-modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-close" onClick={closePhotoModal}>
              ×
            </button>

            <div className="modal-image">
              <img
                src={getPhotoUrl(selectedPhoto.image_path)}
                alt="Event photo"
              />
            </div>

            <div className="modal-info">
              <div className="photo-meta">
                <p>
                  <strong>Uploaded:</strong>{" "}
                  {formatDate(selectedPhoto.uploaded_at)}
                </p>
                {selectedPhoto.original_filename && (
                  <p>
                    <strong>Filename:</strong> {selectedPhoto.original_filename}
                  </p>
                )}
                {selectedPhoto.file_size && (
                  <p>
                    <strong>Size:</strong>{" "}
                    {(selectedPhoto.file_size / 1024 / 1024).toFixed(2)} MB
                  </p>
                )}
              </div>

              <div className="modal-actions">
                <a
                  href={getPhotoUrl(selectedPhoto.image_path)}
                  download={selectedPhoto.original_filename}
                  className="btn btn-primary"
                >
                  Download
                </a>
                {canDeletePhoto(selectedPhoto) && (
                  <button
                    className="btn btn-danger"
                    onClick={() => handleDeletePhoto(selectedPhoto.id)}
                    disabled={deleting === selectedPhoto.id}
                  >
                    {deleting === selectedPhoto.id ? "Deleting..." : "Delete"}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PhotoGallery;
