// Define the types that match the backend API response
export type Incident = {
  name: string;
  severity: string;
  updated_at: string;
};

export type Metrics = {

  active_incidents: number;
  people_at_risk: number;
  teams_deployed: number;
  teams_total: number;
  cases_resolved: number;
};

export type Zone = {
  id: string;
  name: string;
  latitude?: number;
  longitude?: number;
  risk_score: number;
  people_at_risk: number;
  status: string;
};

export type DashboardPayload = {
  incident: Incident;
  metrics: Metrics;
  zones: Zone[];
  ai_summary: string;
  weather?: {
    current_precipitation: number;
    condition: string;
    trend?: string | null;
    updated_at: string;
    source: string;
  } | null;
};

export type Role = "INCIDENT_COMMANDER" | "VOLUNTEER";

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  role: Role;
};

export type AuthPayload = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type UserManagementPayload = {
  users: Array<{
    id: string;
    name: string;
    email: string;
    role: string;
    created_at: string;
    volunteer_id?: string | null;
    volunteer_status?: string | null;
    volunteer_availability?: string | null;
    volunteer_skills?: string | null;
    volunteer_location?: string | null;
    assignment_count: number;
    active_assignment_count: number;
    completed_assignment_count: number;
    current_assignment?: string | null;
  }>;
  citizen_sos: Array<{
    report_id: string;
    emergency: string;
    location?: string | null;
    zone_name?: string | null;
    people: number;
    priority: string;
    status: string;
    created_at: string;
    response_status?: string | null;
  }>;
  activity: Array<{
    label: string;
    category: string;
    timestamp: string;
  }>;
};

const API_URL = import.meta.env.VITE_API_URL || "";
const TOKEN_STORAGE_KEY = "resq_ai_token";
const USER_STORAGE_KEY = "resq_ai_user";

// ---------- Auth token storage ----------

let authToken: string | null = localStorage.getItem(TOKEN_STORAGE_KEY);

function authHeaders(): Record<string, string> {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

function setSession(payload: AuthPayload) {
  authToken = payload.access_token;
  localStorage.setItem(TOKEN_STORAGE_KEY, payload.access_token);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(payload.user));
}

function clearSession() {
  authToken = null;
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

function getStoredUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

async function parseAuthError(response: Response): Promise<string> {
  const body = await response.json().catch(() => ({}));
  return body.detail || `HTTP error! status: ${response.status}`;
}

// Demo data fallback - matches the structure expected by the frontend
const demoDashboard: DashboardPayload = {
  incident: {
    name: "Bhopal Flood Response",
    severity: "critical",
    updated_at: new Date().toISOString(),
  },
  metrics: {
    active_incidents: 4,
    people_at_risk: 1284,
    teams_deployed: 18,
    teams_total: 24,
    cases_resolved: 96,
  },
  zones: [
    { id: "Z-01", name: "Riverside Colony", risk_score: 96, people_at_risk: 420, status: "Immediate evacuation" },
    { id: "Z-02", name: "Old Market Ward", risk_score: 81, people_at_risk: 185, status: "Rescue in progress" },
    { id: "Z-03", name: "Shanti Nagar", risk_score: 68, people_at_risk: 96, status: "Shelter activated" },
  ],
  ai_summary: "Heavy rainfall has caused the Kolar River to breach its eastern bank. Three zones show compounding flood risk, with an estimated 701 people requiring support within the next 2 hours.",
};

export const resqApi = {
  // ---------- Auth ----------

  isConfigured: (): boolean => Boolean(API_URL),

  getStoredUser,

  isAuthenticated: (): boolean => Boolean(authToken),

  logout: () => {
    clearSession();
  },

  login: async (email: string, password: string): Promise<AuthPayload> => {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) throw new Error(await parseAuthError(response));
    const data: AuthPayload = await response.json();
    setSession(data);
    return data;
  },

  register: async (name: string, email: string, password: string, role: Role): Promise<AuthPayload> => {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, role }),
    });
    if (!response.ok) throw new Error(await parseAuthError(response));
    const data: AuthPayload = await response.json();
    setSession(data);
    return data;
  },

  me: async (): Promise<AuthUser> => {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },

  // ---------- Dashboard / operations ----------

  dashboard: async (): Promise<DashboardPayload> => {
    if (!API_URL) return demoDashboard;

    try {
      const response = await fetch(`${API_URL}/api/dashboard`, {
        headers: { ...authHeaders() },
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.warn("Failed to fetch dashboard from API, using demo data:", error);
      return demoDashboard;
    }
  },

  assign: async (zoneId: string, action: string, reportId?: string): Promise<any> => {
    if (!API_URL) {
      // Simulate API call in demo mode
      console.log(`Demo: Assigned action "${action}" to zone ${zoneId}`);
      return;
    }

    const response = await fetch(`${API_URL}/api/actions/assign`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ zone_id: zoneId, action, report_id: reportId }),
    });

    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },


  actions: async () => {
    if (!API_URL) return [];
    const response = await fetch(`${API_URL}/api/actions`, {
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  },

    updateActionStatus: async (actionId: string, status: string) => {
    if (!API_URL) return null;
    const response = await fetch(`${API_URL}/api/actions/${actionId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },


  responsePlan: async (zoneId: string) => {
    if (!API_URL) {
      throw new Error("Backend API URL is not configured");
    }

    const response = await fetch(`${API_URL}/api/ai/response-plan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ zone_id: zoneId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  // Optional: reports endpoint if needed elsewhere
  reports: async () => {
    if (!API_URL) return [];

    try {
      const response = await fetch(`${API_URL}/api/reports`, {
        headers: { ...authHeaders() },
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.warn("Failed to fetch reports from API:", error);
      return [];
    }
  },

  createReport: async (report: {
    emergency: string;
    people: number;
    medical_emergency: boolean;
    location?: string;
    latitude?: number;
    longitude?: number;
    flood_severity: number;
    infrastructure_damage: number;
    weather_severity: number;
  }) => {
    if (!API_URL) {
      throw new Error("Backend API URL is not configured");
    }

    // Intentionally unauthenticated: citizens submitting an SOS should never
    // need an account. Auth headers are omitted here on purpose.
    const response = await fetch(`${API_URL}/api/reports`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(report),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },
  volunteers: async (): Promise<any[]> => {
    if (!API_URL) return [];

    const response = await fetch(`${API_URL}/api/volunteers`, {
      headers: { ...authHeaders() },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },
  users: async (): Promise<UserManagementPayload> => {
    const response = await fetch(`${API_URL}/api/users`, {
      headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },

  createVolunteer: async (volunteer: {
    name: string;
    skills?: string;
    location?: string;
  }): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(volunteer),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },

  updateVolunteer: async (
    id: string,
    updates: {
      status?: string;
      availability?: string;
      skills?: string;
      location?: string;
    }
  ): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteers/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  },
  publicShelters: async (): Promise<any[]> => {
    const response = await fetch(`${API_URL}/api/public/shelters`);
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  publicAlerts: async (): Promise<any[]> => {
    const response = await fetch(`${API_URL}/api/public/alerts`);
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  publicWeather: async (latitude: number, longitude: number): Promise<any> => {
    const response = await fetch(`${API_URL}/api/public/weather?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`);
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  trackReport: async (reportId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/api/public/reports/${encodeURIComponent(reportId)}`);
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  myAssignments: async (): Promise<any[]> => {
    const response = await fetch(`${API_URL}/api/volunteer/me/assignments`, { headers: { ...authHeaders() } });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  myWeather: async (): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteer/me/weather`, { headers: { ...authHeaders() } });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  completeAssignment: async (assignmentId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteer/me/assignments/${assignmentId}/complete`, { method: "PATCH", headers: { ...authHeaders() } });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  acceptAssignment: async (assignmentId: string): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteer/me/assignments/${assignmentId}/accept`, { method: "PATCH", headers: { ...authHeaders() } });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  assignVolunteer: async (volunteerId: string, actionId: string, instructions: string): Promise<any> => {
    const response = await fetch(`${API_URL}/api/volunteer-assignments`, { method: "POST", headers: { "Content-Type": "application/json", ...authHeaders() }, body: JSON.stringify({ volunteer_id: volunteerId, action_id: actionId, instructions }) });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
  volunteerAssignments: async (): Promise<any[]> => {
    const response = await fetch(`${API_URL}/api/volunteer-assignments`, { headers: { ...authHeaders() } });
    if (!response.ok) throw new Error(await parseAuthError(response));
    return await response.json();
  },
};
