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
  risk_score: number;
  people_at_risk: number;
  status: string;
};

export type DashboardPayload = {
  incident: Incident;
  metrics: Metrics;
  zones: Zone[];
  ai_summary: string;
};

const API_URL = import.meta.env.VITE_API_URL || "";

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
  dashboard: async (): Promise<DashboardPayload> => {
    if (!API_URL) return demoDashboard;

    try {
      const response = await fetch(`${API_URL}/api/dashboard`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.warn("Failed to fetch dashboard from API, using demo data:", error);
      return demoDashboard;
    }
  },

  assign: async (zoneId: string, action: string): Promise<void> => {
    if (!API_URL) {
      // Simulate API call in demo mode
      console.log(`Demo: Assigned action "${action}" to zone ${zoneId}`);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/actions/assign`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ zone_id: zoneId, action }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      console.log("Assignment successful:", result);
    } catch (error) {
      console.error("Failed to assign action:", error);
      // In demo mode, we still show the toast even if API fails
      throw error;
    }
  },


  actions: async () => {
    if (!API_URL) return [];
    const response = await fetch(`${API_URL}/api/actions`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  },

    updateActionStatus: async (actionId: string, status: string) => {
    if (!API_URL) return null;
    const response = await fetch(`${API_URL}/api/actions/${actionId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
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
      const response = await fetch(`${API_URL}/api/reports`);
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
    location: string;
    latitude: number;
    longitude: number;
    flood_severity: number;
    infrastructure_damage: number;
    weather_severity: number;
  }) => {
    if (!API_URL) {
      throw new Error("Backend API URL is not configured");
    }

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
};
