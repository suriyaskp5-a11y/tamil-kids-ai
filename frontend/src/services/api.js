const API_HOST = import.meta.env.VITE_API_BASE_URL || '';
const BASE_URL = `${API_HOST}/api/v1`;

export const api = {
  getToken: () => localStorage.getItem('tamil_kids_token'),
  setToken: (token) => localStorage.setItem('tamil_kids_token', token),
  clearToken: () => localStorage.removeItem('tamil_kids_token'),

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.clearToken();
      // Optional redirect or event
    }

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Request failed with status ${res.status}`);
    }

    return res.json();
  },

  // Auth
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    if (!res.ok) throw new Error('Invalid username or password');
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  },

  async getMe() {
    return this.request('/auth/me');
  },

  // Health & Summary
  async getHealth() {
    return this.request('/health/');
  },

  async getSummary() {
    return this.request('/dashboard/summary');
  },

  // Topics
  async getTopics() {
    return this.request('/topics/');
  },

  async generateTopic() {
    return this.request('/topics/generate', { method: 'POST' });
  },

  // Stories
  async getStories() {
    return this.request('/stories/');
  },

  async generateStory(topicId) {
    return this.request(`/stories/generate/${topicId}`, { method: 'POST' });
  },

  // Jobs
  async getJobs() {
    return this.request('/jobs/');
  },

  async triggerJob(topicId = null) {
    const url = topicId ? `/jobs/trigger?topic_id=${topicId}` : '/jobs/trigger';
    return this.request(url, { method: 'POST' });
  },

  // Settings
  async getSettings() {
    return this.request('/settings/');
  },

  async updateSetting(key, value) {
    return this.request('/settings/', {
      method: 'PUT',
      body: JSON.stringify({ key, value }),
    });
  }
};
