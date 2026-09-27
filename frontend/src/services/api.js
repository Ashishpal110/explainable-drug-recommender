/**
 * API Service Layer for the Explainable Drug Recommendation and Safety Screening System.
 * Connects frontend views to FastAPI backend endpoints.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = `${BASE_URL}/api/v1`;

async function request(endpoint, options = {}) {
  const url = `${API_PREFIX}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // Ignore JSON parse error on non-JSON error response
      }
      throw new Error(errorDetail);
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      throw new Error('Unable to connect to backend server. Please verify the FastAPI backend is running on ' + BASE_URL);
    }
    throw err;
  }
}

/**
 * Health check and system readiness probe.
 */
export async function getHealth() {
  return request('/health');
}

/**
 * Generates personalized recommendations with deterministic safety auditing.
 * @param {Object} profile - { age, condition, symptoms, allergies, current_medications, weights }
 */
export async function getRecommendations(profile) {
  // Ensure required and optional list types are strictly formatted
  const payload = {
    age: Number(profile.age),
    condition: String(profile.condition || '').trim(),
    symptoms: Array.isArray(profile.symptoms) ? profile.symptoms : [],
    allergies: Array.isArray(profile.allergies) ? profile.allergies : [],
    current_medications: Array.isArray(profile.current_medications) ? profile.current_medications : [],
  };

  if (profile.weights && typeof profile.weights === 'object') {
    payload.weights = profile.weights;
  }

  return request('/recommend', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// Alias for getRecommendations
export const recommendPatient = getRecommendations;

/**
 * Evaluates patient review sentiment using the trained TF-IDF + Logistic Regression model.
 * @param {string} text - Review text
 */
export async function analyzeSentiment(text) {
  return request('/sentiment/analyze', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}

/**
 * Retrieves the catalog of indexed medical conditions.
 */
export async function getConditions() {
  return request('/conditions');
}

/**
 * Retrieves recognized allergen and pharmacological classes from the safety crosswalk.
 */
export async function getAllergies() {
  return request('/allergies');
}

/**
 * Paginated query of cataloged medications with optional condition/search filters.
 * @param {Object} params - { condition, search, limit, offset }
 */
export async function getDrugs(params = {}) {
  const query = new URLSearchParams();
  if (params.condition) query.append('condition', params.condition);
  if (params.search) query.append('search', params.search);
  if (params.limit !== undefined) query.append('limit', params.limit);
  if (params.offset !== undefined) query.append('offset', params.offset);

  const qs = query.toString();
  return request(`/drugs${qs ? `?${qs}` : ''}`);
}

/**
 * Retrieves detailed drug profile, indication mapping, and seeded safety rules.
 * @param {number|string} drugId
 */
export async function getDrugDetails(drugId) {
  return request(`/drugs/${drugId}`);
}

/**
 * Retrieves empirical evaluation metrics for the NLP model and recommender specifications.
 */
export async function getModelMetrics() {
  return request('/model/metrics');
}
