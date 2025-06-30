import React, { useState, useRef } from "react";
import "./SelfieUpload.css";

const SelfieUpload = ({
  onFileSelect,
  selectedFile,
  error,
  disabled = false,
  required = true,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      onFileSelect(null, "Please select an image file");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      onFileSelect(null, "File size must be less than 10MB");
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target.result);
    };
    reader.readAsDataURL(file);

    onFileSelect(file, null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) {
      setDragOver(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const openFileDialog = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const clearFile = () => {
    setPreview(null);
    onFileSelect(null, null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="selfie-upload">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInputChange}
        style={{ display: "none" }}
        disabled={disabled}
      />

      <div className="form-group">
        <label>
          Profile Photo (Selfie){" "}
          {required && <span className="required">*</span>}
        </label>
        <p className="help-text">
          Upload a clear selfie for face recognition. Make sure your face is
          clearly visible and well-lit.
        </p>

        {preview ? (
          <div className="selfie-preview">
            <div className="preview-container">
              <img
                src={preview}
                alt="Selfie preview"
                className="preview-image"
              />
              <div className="preview-overlay">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={clearFile}
                  disabled={disabled}
                >
                  Change Photo
                </button>
              </div>
            </div>
            {selectedFile && (
              <div className="file-info">
                <small>
                  📁 {selectedFile.name} (
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </small>
              </div>
            )}
          </div>
        ) : (
          <div
            className={`selfie-dropzone ${dragOver ? "dragover" : ""} ${
              disabled ? "disabled" : ""
            } ${error ? "error" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={openFileDialog}
          >
            <div className="dropzone-content">
              <div className="upload-icon">🤳</div>
              <h4>Upload Your Selfie</h4>
              <p>Drag and drop your photo here, or click to select</p>
              <small>
                JPG, PNG, GIF • Max 10MB • Face must be clearly visible
              </small>
            </div>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
      </div>
    </div>
  );
};

export default SelfieUpload;
