import axios from "axios";

// Create axios instance with base configuration
const getBaseURL = () => {
  // In production, use the environment variable set by Render
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // In development, use localhost
  if (import.meta.env.DEV) {
    return "http://localhost:8000";
  }

  // Fallback for production if env var not set
  return window.location.origin.replace(/:\d+/, ":8000");
};

const api = axios.create({
  baseURL: getBaseURL(),
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("🔑 Token added to request:", token.substring(0, 20) + "...");
    } else {
      console.log("⚠️ No token found in localStorage");
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  login: (loginData) => api.post("/api/auth/login", loginData),
  register: (userData) => api.post("/api/auth/register", userData),
  getMe: () => api.get("/api/auth/me"),
  verify: () => api.get("/api/auth/verify"),
};

// Events API calls
export const eventsAPI = {
  create: (eventData) => api.post("/api/events/", eventData),
  getAll: () => api.get("/api/events/"),
  getOwned: () => api.get("/api/events/owned"),
  getRegistered: () => api.get("/api/events/registered"),
  getByCode: (eventCode) => api.get(`/api/events/${eventCode}`),
  getByCodePublic: (eventCode) => api.get(`/api/events/public/${eventCode}`),
  getByCodeLegacy: (eventCode) => api.get(`/api/events/code/${eventCode}`),
  join: (eventCode) => api.post(`/api/events/${eventCode}/join`),
  joinByCode: (eventCode) => api.post(`/api/events/code/${eventCode}/join`),
  registerWithSelfie: (eventCode, userData, selfieFile) => {
    const formData = new FormData();
    formData.append("name", userData.name);
    formData.append("email", userData.email);
    formData.append("password", userData.password);
    formData.append("selfie", selfieFile);
    return api.post(
      `/api/events/code/${eventCode}/register-with-selfie`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
  },
  leave: (eventCode) => api.delete(`/api/events/${eventCode}/leave`),
  getGuests: (eventCode) => api.get(`/api/events/${eventCode}/guests`),
  delete: (eventCode) => api.delete(`/api/events/${eventCode}`),
  getQRCode: (eventCode) => api.get(`/api/events/${eventCode}/qr-code`),
};

// Photos API calls
export const photosAPI = {
  uploadProfile: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/api/photos/profile", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteProfile: () => api.delete("/api/photos/profile"),
  uploadEvent: (eventIdentifier, files) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    return api.post(`/api/photos/events/${eventIdentifier}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getEventPhotos: (eventIdentifier) =>
    api.get(`/api/photos/events/${eventIdentifier}`),
  getEventPhotosWithFaces: (eventIdentifier) =>
    api.get(`/api/photos/events/${eventIdentifier}/with-faces`),
  processFaces: (photoIds) =>
    api.post("/api/photos/process-faces", { photo_ids: photoIds }),
  delete: (photoId) => api.delete(`/api/photos/${photoId}`),
  getUrl: (photoId) => api.get(`/api/photos/${photoId}/url`),
};

export default api;
