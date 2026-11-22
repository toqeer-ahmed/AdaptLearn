/**
 * AdaptLearn API Client
 *
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Handles bearer token authorization, JSON serialization, and error normalization.
 *
 * Requirements Traceability:
 * - NFR-04: Session bearer token authorization.
 * - NFR-14: Plain language error message handling.
 * - docs/api.md: Strict alignment with cross-module API contracts.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Standard HTTP request wrapper with authorization and error parsing.
 */
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('adaptlearn_token') || 'token-101-student';

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const config = {
    ...options,
    headers,
  };
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get('content-type');
    const isJson = contentType && contentType.includes('application/json');
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      // Extract detail string from FastAPI error structure
      let errorMessage = `HTTP Error ${response.status}`;
      if (data && typeof data === 'object') {
        if (data.detail) {
          errorMessage = typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail);
        } else if (data.error && data.error.message) {
          errorMessage = data.error.message;
        }
      }
      const error = new Error(errorMessage);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (err.status) {
      throw err;
    }
    // Network or connection failure
    const networkError = new Error(
      `Cannot connect to backend server at ${API_BASE_URL}. Ensure FastAPI is running on port 8000.`
    );
    networkError.status = 0;
    throw networkError;
  }
}

export const api = {
  // System Health (REQ-SYS-001)
  getHealth: () => request('/health'),

  // Module 3: Adaptive Engine (Toqeer) — LIVE
  getAdaptiveSettings: (courseId) =>
    request(`/api/v1/courses/${courseId}/adaptive-settings`),

  updateAdaptiveSettings: (courseId, payload) =>
    request(`/api/v1/courses/${courseId}/adaptive-settings`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),

  getRecommendations: (courseId, limit = 3) =>
    request(`/api/v1/courses/${courseId}/recommendations?limit=${limit}`),

  recalculateMastery: (courseId, payload) =>
    request(`/api/v1/courses/${courseId}/recalculate-mastery`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Module 5: Student Progress & History (Toqeer) — LIVE
  getCourseProgress: (courseId, studentId = null) => {
    const query = studentId ? `?student_id=${studentId}` : '';
    return request(`/api/v1/courses/${courseId}/progress${query}`);
  },

  getAttemptHistory: (courseId, page = 1, pageSize = 10, studentId = null) => {
    let query = `?page=${page}&page_size=${pageSize}`;
    if (studentId) {
      query += `&student_id=${studentId}`;
    }
    return request(`/api/v1/courses/${courseId}/attempts${query}`);
  },

  // Module 5: Instructor Analytics (Toqeer) — LIVE
  getMasteryDistribution: (courseId) =>
    request(`/api/v1/courses/${courseId}/analytics/mastery-distribution`),

  getStudentRoster: (courseId) =>
    request(`/api/v1/courses/${courseId}/analytics/student-roster`),

  getQuestionStats: (courseId) =>
    request(`/api/v1/courses/${courseId}/analytics/questions`),

  // Module 1: Auth & User Management (Hiba) — BLOCKED BY BACKEND
  login: async (email, password) => {
    return request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  register: async (payload) => {
    return request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Module 1: Course Management (Hiba) — BLOCKED BY BACKEND
  getCourses: () => request('/api/v1/courses'),
  enrollCourse: (courseId, courseCode) =>
    request(`/api/v1/courses/${courseId}/enroll`, {
      method: 'POST',
      body: JSON.stringify({ course_code: courseCode }),
    }),

  // Module 2: Quiz Management & Attempts (Mustajaab) — LIVE ON BACKEND
  getQuizzes: (courseId) => request(`/api/v1/courses/${courseId}/quizzes`),
  getQuiz: (quizId) => request(`/api/v1/quizzes/${quizId}`),
  createQuestion: (courseId, payload) =>
    request(`/api/v1/courses/${courseId}/questions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  createQuiz: (courseId, payload) =>
    request(`/api/v1/courses/${courseId}/quizzes`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  publishQuiz: (quizId, isPublished = true) =>
    request(`/api/v1/quizzes/${quizId}/publish?is_published=${isPublished}`, {
      method: 'POST',
    }),
  createPracticeQuiz: (courseId, topicId, questionCount = 5) =>
    request(`/api/v1/courses/${courseId}/topics/${topicId}/practice-quiz`, {
      method: 'POST',
      body: JSON.stringify({ question_count: questionCount }),
    }),
  submitQuizAttempt: (quizId, answers) =>
    request(`/api/v1/quizzes/${quizId}/attempts`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),
  getAttemptResult: (attemptId) => request(`/api/v1/attempts/${attemptId}`),
};
