import React, { useState, useRef, useEffect } from "react";
import "./SelfieUpload.css";

const SelfieUpload = ({
  onFileSelect,
  selectedFile,
  error,
  disabled = false,
  required = true,
}) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [preview, setPreview] = useState(null);
  const [stream, setStream] = useState(null);
  const [cameraError, setCameraError] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Cleanup camera stream when component unmounts
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      setCameraError("");
      setIsCapturing(true);

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user", // Front camera for selfies
        },
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setCameraError(
        "Unable to access camera. Please check your camera permissions."
      );
      setIsCapturing(false);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setIsCapturing(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob(
      (blob) => {
        if (blob) {
          // Create a File object from the blob
          const file = new File([blob], `selfie-${Date.now()}.jpg`, {
            type: "image/jpeg",
          });

          // Create preview URL
          const previewUrl = URL.createObjectURL(blob);
          setPreview(previewUrl);

          // Stop camera and notify parent
          stopCamera();
          onFileSelect(file, null);
        }
      },
      "image/jpeg",
      0.9
    );
  };

  const retakePhoto = () => {
    setPreview(null);
    onFileSelect(null, null);
    if (preview) {
      URL.revokeObjectURL(preview);
    }
  };

  return (
    <div className="selfie-upload">
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div className="form-group">
        <label>
          Profile Photo (Selfie){" "}
          {required && <span className="required">*</span>}
        </label>
        <p className="help-text">
          Take a clear selfie using your camera for face recognition. Make sure
          your face is clearly visible and well-lit.
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
                  onClick={retakePhoto}
                  disabled={disabled}
                >
                  Retake Photo
                </button>
              </div>
            </div>
            {selectedFile && (
              <div className="file-info">
                <small>
                  📸 Selfie captured (
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </small>
              </div>
            )}
          </div>
        ) : isCapturing ? (
          <div className="camera-container">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="camera-video"
            />
            <div className="camera-controls">
              <button
                type="button"
                className="btn btn-primary capture-btn"
                onClick={capturePhoto}
                disabled={disabled}
              >
                📸 Capture Selfie
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={stopCamera}
                disabled={disabled}
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div
            className={`selfie-camera-trigger ${disabled ? "disabled" : ""} ${
              error || cameraError ? "error" : ""
            }`}
          >
            <div className="camera-content">
              <div className="camera-icon">📷</div>
              <h4>Take Your Selfie</h4>
              <p>
                Click the button below to open your camera and take a selfie
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={startCamera}
                disabled={disabled}
              >
                📸 Open Camera
              </button>
            </div>
          </div>
        )}

        {(error || cameraError) && (
          <div className="error-message">{error || cameraError}</div>
        )}
      </div>
    </div>
  );
};

export default SelfieUpload;
