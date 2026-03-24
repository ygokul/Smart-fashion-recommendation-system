const explicitBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export function getApiBaseUrl() {
  if (explicitBaseUrl) {
    return explicitBaseUrl.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    return window.location.origin;
  }

  return "http://127.0.0.1:8000";
}
