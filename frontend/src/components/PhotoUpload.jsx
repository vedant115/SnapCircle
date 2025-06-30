import React, { useState, useRef } from "react";
import { photosAPI } from "../utils/api";

const PhotoUpload = ({
  eventId,
  onUploadComplete,
  multiple = true,
  accept = "image/*",
  maxFiles = 10,
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [uploadProgress, setUploadProgress] = useState([]);

  const fileInputRef = useRef(null);

  const handleFileSelect = (files) => {
    const fileArray = Array.from(files);

    if (fileArray.length > maxFiles) {
      setError(`Maximum ${maxFiles} files allowed`);
      return;
    }

    // Validate file types
    const validFiles = fileArray.filter((file) => {
      if (!file.type.startsWith("image/")) {
        setError("Only image files are allowed");
        return false;
      }
      if (file.size > 10 * 1024 * 1024) {
        // 10MB limit
        setError("File size must be less than 10MB");
        return false;
      }
      return true;
    });

    if (validFiles.length !== fileArray.length) {
      return;
    }

    uploadFiles(validFiles);
  };

  const uploadFiles = async (files) => {
    setUploading(true);
    setError("");
    setUploadProgress(files.map(() => 0));

    console.log("📤 Starting upload for", files.length, "files");
    files.forEach((file, index) => {
      console.log(
        `📁 File ${index + 1}: ${file.name} (${file.size} bytes, ${file.type})`
      );
    });

    try {
      const response = await photosAPI.uploadEvent(eventId, files);
      console.log("✅ Upload successful:", response.data);

      if (onUploadComplete) {
        onUploadComplete(response.data);
      }

      setUploadProgress([]);
    } catch (err) {
      console.error("❌ Upload failed:", err);
      console.error("Error response:", err.response?.data);
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="photo-upload">
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInputChange}
        style={{ display: "none" }}
      />

      <div
        className={`file-upload ${dragOver ? "dragover" : ""} ${
          uploading ? "uploading" : ""
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        {uploading ? (
          <div className="upload-progress">
            <div className="upload-spinner">📤</div>
            <p>Uploading photos...</p>
          </div>
        ) : (
          <div className="upload-content">
            <div className="upload-icon">📸</div>
            <h4>Upload Photos</h4>
            <p>Drag and drop photos here, or click to select files</p>
            <small>
              {multiple ? `Up to ${maxFiles} files` : "1 file"} • Max 10MB each
              • JPG, PNG, GIF
            </small>
          </div>
        )}
      </div>

      {error && <div className="upload-error">{error}</div>}

      {uploadProgress.length > 0 && (
        <div className="upload-progress-list">
          {uploadProgress.map((progress, index) => (
            <div key={index} className="progress-item">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PhotoUpload;
