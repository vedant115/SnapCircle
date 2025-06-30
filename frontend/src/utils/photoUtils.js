/**
 * Utility functions for handling photo URLs in SnapCircle
 * Supports both local storage and AWS S3 cloud storage
 */

/**
 * Get the correct URL for a photo based on storage type
 * @param {string} imagePath - The image path from the API (presigned URL or local URL)
 * @param {string} baseUrl - Base URL for local storage (default: http://localhost:8000)
 * @returns {string} The complete URL to access the photo
 */
export const getPhotoUrl = (imagePath, baseUrl = "http://localhost:8000") => {
  if (!imagePath) {
    return "";
  }

  // The backend now returns presigned URLs for S3 and proper URLs for local storage
  // If it's already a full URL (S3 presigned or local), use it directly
  if (imagePath.startsWith("http")) {
    return imagePath;
  }

  // For relative paths (legacy local storage), construct local URL
  return `${baseUrl}/uploads/${imagePath}`;
};

/**
 * Check if the current setup is using S3 storage
 * @param {string} imagePath - Sample image path to check
 * @returns {boolean} True if using S3, false if using local storage
 */
export const isUsingS3Storage = (imagePath) => {
  return imagePath && imagePath.startsWith("http");
};

/**
 * Extract filename from image path (works for both local and S3)
 * @param {string} imagePath - The image path
 * @returns {string} The filename
 */
export const getFilenameFromPath = (imagePath) => {
  if (!imagePath) return "";

  // For S3 URLs, extract from the URL
  if (imagePath.startsWith("http")) {
    const url = new URL(imagePath);
    const pathParts = url.pathname.split("/");
    return pathParts[pathParts.length - 1];
  }

  // For local paths, extract from the path
  const pathParts = imagePath.split(/[/\\]/);
  return pathParts[pathParts.length - 1];
};

/**
 * Get storage type indicator for debugging
 * @param {string} imagePath - The image path
 * @returns {string} Storage type ("S3" or "Local")
 */
export const getStorageType = (imagePath) => {
  return isUsingS3Storage(imagePath) ? "S3" : "Local";
};
