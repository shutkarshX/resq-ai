import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import {
  AlertTriangle, Bell, Bot, ChevronDown, CircleHelp, Clock3, CloudRain,
  Crosshair, FileText, Flame, HeartPulse, Layers3, MapPinned, Menu, MessageSquare,
  Navigation, PhoneCall, Radio, Route, Search, ShieldCheck, Siren, Sparkles,
  Target, Thermometer, Users, X, Zap, Wifi, RefreshCw
} from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import "leaflet/dist/leaflet.css";
import "./styles.css";
import { resqApi, type DashboardPayload, type AuthUser, type Role } from "./api";

type Priority = "Critical" | "High" | "Medium";
type Zone = { id: string; name: string; risk: number; people: string; status: string; color: string; coords: [number, number]; };

const zones: Zone[] = [
  { id: "Z-01", name: "Riverside Colony", risk: 96, people: "420 at risk", status: "Immediate evacuation", color: "#ff5f5f", coords: [23.2599, 77.4126] },
  { id: "Z-02", name: "Old Market Ward", risk: 81, people: "185 at risk", status: "Rescue in progress", color: "#ffb547", coords: [23.2638, 77.4012] },
  { id: "Z-03", name: "Shanti Nagar", risk: 68, people: "96 at risk", status: "Shelter activated", color: "#ffd166", coords: [23.2471, 77.4168] },
];

function FlyTo({ position }: { position: [number, number] }) {
  const map = useMap();
  map.flyTo(position, 14, { duration: 0.8 });
  return null;
}

function Dashboard({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [active, setActive] = useState("Command Center");
  const [selectedZone, setSelectedZone] = useState<Zone>(zones[0]);
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [apiState, setApiState] = useState<"connecting" | "online" | "demo">("connecting");
  const [refreshing, setRefreshing] = useState(false);
  const [responsePlan, setResponsePlan] = useState<any>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("Operation updated.");
  const [search, setSearch] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [reports, setReports] = useState<any[]>([]);
  const [operations, setOperations] = useState<any[]>([]);
  const [volunteers, setVolunteers] = useState<any[]>([]);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [userManagement, setUserManagement] = useState<any>(null);
  const [selectedActionId, setSelectedActionId] = useState("");
  const [selectedVolunteerId, setSelectedVolunteerId] = useState("");
  const [assignmentInstructions, setAssignmentInstructions] = useState("");
  const [assigningVolunteer, setAssigningVolunteer] = useState(false);
  const initials = user.name.split(" ").map(p => p[0]).join("").slice(0, 2).toUpperCase();
  const roleLabel = user.role === "INCIDENT_COMMANDER" ? "Incident Commander" : "Volunteer";
  const nav = [
    { label: "Command Center", icon: Target }, { label: "Live Map", icon: MapPinned },
    { label: "Reports & AI", icon: FileText }, { label: "Rescue Operations", icon: Route },
    { label: "Volunteers", icon: Users }, { label: "User Management", icon: Users },
  ];
  const liveZones = useMemo<Zone[]>(() => {
    if (!dashboard?.zones?.length) return zones;
    return dashboard.zones.map((z, index) => ({
      id: z.id,
      name: z.name,
      risk: z.risk_score,
      people: `${z.people_at_risk} at risk`,
      status: z.status,
      color: z.risk_score > 90 ? "#ff5f5f" : z.risk_score > 75 ? "#ffb547" : "#ffd166",
      coords: z.latitude != null && z.longitude != null
        ? [z.latitude, z.longitude]
        : (zones.find(seedZone => seedZone.id === z.id)?.coords || zones[0].coords),
    }));
  }, [dashboard]);
  const filteredZones = useMemo(() => liveZones.filter(z => z.name.toLowerCase().includes(search.toLowerCase())), [liveZones, search]);
  const activeIncidentCount = dashboard?.metrics.active_incidents ?? 0;
  const hasActiveOperations = operations.some(operation => !["COMPLETED", "CANCELLED"].includes(operation.status));
  const operationalContext = activeIncidentCount === 1 && dashboard?.incident.name
    ? dashboard.incident.name
    : activeIncidentCount > 1 || hasActiveOperations
    ? "Active Response"
    : "Current Operations";
  const commanderWeatherLocation = dashboard?.zones?.[0]?.name;
  const commanderWeatherText = dashboard?.weather
    ? dashboard.weather.current_precipitation <= 0.05
      ? `${dashboard.weather.condition} · No rainfall · Stable`
      : `${dashboard.weather.condition} · Rainfall ${dashboard.weather.current_precipitation.toFixed(1)} mm · ${dashboard.weather.trend || "Current conditions"}`
    : "Weather data unavailable";
  const chartData = useMemo(() => {
    const now = new Date();
    const currentHour = new Date(now);
    currentHour.setMinutes(0, 0, 0);
    const buckets = Array.from({ length: 6 }, (_, index) => {
      const start = new Date(currentHour);
      start.setHours(currentHour.getHours() - (5 - index));
      return { start, time: start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false }), reports: 0, resolved: 0 };
    });
    const bucketFor = (value: string) => {
      const timestamp = new Date(value).getTime();
      return buckets.find(bucket => timestamp >= bucket.start.getTime() && timestamp < bucket.start.getTime() + 60 * 60 * 1000);
    };
    reports.forEach(report => {
      const bucket = bucketFor(report.created_at);
      if (bucket) bucket.reports += 1;
    });
    operations.forEach(operation => {
      if (operation.status !== "COMPLETED" || !operation.completed_at || (!operation.report_id && !operation.incident_id)) return;
      const bucket = bucketFor(operation.completed_at);
      if (bucket) bucket.resolved += 1;
    });
    return buckets.map(({ time, reports: incoming, resolved }) => ({ time, reports: incoming, resolved }));
  }, [reports, operations]);
  const activeSosCount = reports.filter(report => report.status !== "RESOLVED").length;

const loadDashboard = async () => {
    setRefreshing(true);
    try {
      const payload = await resqApi.dashboard();
      setDashboard(payload);
      setApiState("online");
    } catch {
      setApiState("demo");
    } finally {
      setRefreshing(false);
    }
  };
  const loadWorkflow = async () => {
    const [nextReports, nextOperations, nextVolunteers, nextAssignments, nextUserManagement] = await Promise.all([
      resqApi.reports(),
      resqApi.actions(),
      resqApi.volunteers(),
      resqApi.volunteerAssignments(),
      resqApi.users(),
    ]);
    setReports(nextReports);
    setOperations(nextOperations);
    setVolunteers(nextVolunteers);
    setAssignments(nextAssignments);
    setUserManagement(nextUserManagement);
  };

  useEffect(() => {
    loadDashboard();
    loadWorkflow().catch(() => undefined);
    const timer = window.setInterval(() => { void loadDashboard(); void loadWorkflow(); }, 30000);
    const workflowTimer = window.setInterval(() => { loadWorkflow().catch(() => undefined); }, 10000);
    return () => {
      window.clearInterval(timer);
      window.clearInterval(workflowTimer);
    };
  }, []);

  const submitVolunteerAssignment = async () => {
    if (!selectedActionId || !selectedVolunteerId || !assignmentInstructions.trim()) return;
    setAssigningVolunteer(true);
    try {
      await resqApi.assignVolunteer(selectedVolunteerId, selectedActionId, assignmentInstructions.trim());
      setAssignmentInstructions("");
      await loadWorkflow();
      setToastMessage("Volunteer assigned to the rescue operation.");
    } catch {
      setToastMessage("Failed to assign volunteer.");
    } finally {
      setAssigningVolunteer(false);
      setShowToast(true);
      setTimeout(() => setShowToast(false), 2600);
    }
  };
  const assign = async (zoneId = selectedZone.id, action = "Dispatch nearest available rescue team") => {
    try {
  await resqApi.assign(zoneId, action);
  setToastMessage(`${action} has been added to rescue operations.`);
} catch {
  setToastMessage("Failed to create rescue operation.");
}
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2600);
  };

  const mapPanel = (
    <section id="live-map" className="panel map-panel">
      <div className="panel-header"><div><div className="panel-kicker"><MapPinned size={14}/> GEOSPATIAL INTELLIGENCE</div><h2>Priority rescue zones</h2></div><div className="map-tools"><span className="tiny-btn active status-control"><Crosshair size={14}/> Live</span><span className="tiny-btn status-control"><Layers3 size={14}/></span></div></div>
      <div className="map-wrap">
        <MapContainer center={selectedZone.coords} zoom={13} zoomControl={false} scrollWheelZoom={false}>
          <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/>
          <FlyTo position={selectedZone.coords}/>
          {liveZones.map(z => <Marker key={z.id} position={z.coords}><Popup><strong>{z.name}</strong><br/>Risk score {z.risk}/100<br/>{z.status}</Popup></Marker>)}
        </MapContainer>
        <div className="map-legend"><div><i className="legend-critical"></i> Critical</div><div><i className="legend-high"></i> High risk</div><div><i className="legend-shelter"></i> Shelter</div></div>
        <div className="map-ai-callout"><Sparkles size={15}/><div><strong>AI insight</strong><span>Waterline expanding toward Riverside Colony</span></div></div>
      </div>
    </section>
  );

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand"><div className="brand-mark"><Siren size={21} /></div><div><strong>RESQ<span>-AI</span></strong><small>Disaster Intelligence</small></div><button className="icon-btn mobile-close" onClick={() => setMobileNav(false)}><X size={19}/></button></div>
        <div className="live-pill"><span className="pulse"></span> LIVE INCIDENT <span className="pill-dot">●</span></div>
        <nav>{nav.map(({ label, icon: Icon }) => <button key={label} className={active === label ? "nav-item active" : "nav-item"} onClick={() => { setActive(label); setMobileNav(false); }}><Icon size={18}/><span>{label}</span>{label === "Reports & AI" && <b className="nav-count">12</b>}</button>)}</nav>
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => { setActive("Help & Playbook"); setMobileNav(false); }}><CircleHelp size={18}/><span>Help & playbook</span></button>
          <div className="user-card"><div className="avatar">{initials}</div><div><strong>{user.name}</strong><small>{roleLabel}</small></div><button className="icon-btn" title="Log out" onClick={onLogout}><X size={16}/></button></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setMobileNav(true)}><Menu size={21}/></button>
          <div className="breadcrumb"><span>Operations</span><b>/</b><strong>{active}</strong></div>
          <div className="top-actions"><div className="search-box"><Search size={16}/><input placeholder="Search reports, zones..." value={search} onChange={e => setSearch(e.target.value)} /></div><span className="icon-btn notification status-control" aria-label="Notifications unavailable"><Bell size={18}/><i></i></span><span className="profile status-control" title={user.name}>{initials}</span></div>
        </header>
        <section className="content">
          <div className="page-heading"><div><div className="eyebrow"><span className="status-dot"></span> INCIDENT ACTIVE · UPDATED JUST NOW</div><h1>{active}</h1><p>AI-assisted operational view for <strong>{operationalContext}</strong></p></div><div className="heading-actions"><span className={`connection-state ${apiState}`}><Wifi size={13}/> {apiState === "online" ? "Backend connected" : apiState === "demo" ? "Demo data" : "Connecting"}</span><button className="secondary-btn" onClick={() => { void loadDashboard(); void loadWorkflow(); }}><RefreshCw size={16} className={refreshing ? "spin" : ""}/> Refresh</button></div></div>

          {active === "Command Center" && (
          <>
          <div className="metrics-grid">
            <Metric icon={<AlertTriangle/>} label="Active incidents" value={String(dashboard?.metrics.active_incidents ?? 0).padStart(2, "0")} trend="+2 today" tone="red" />
            <Metric icon={<Users/>} label="People at risk" value={(dashboard?.metrics.people_at_risk ?? 0).toLocaleString()} trend="−8% vs 1h" tone="amber" />
            <Metric icon={<HeartPulse/>} label="Rescue teams deployed" value={`${dashboard?.metrics.teams_deployed ?? 0} / ${dashboard?.metrics.teams_total ?? 0}`} trend="75% capacity" tone="blue" />
            <Metric icon={<ShieldCheck/>} label="Cases resolved" value={String(dashboard?.metrics.cases_resolved ?? 0)} trend="+24 this hour" tone="green" />
          </div>

          <div className="dashboard-grid">
            {mapPanel}

            <section className="panel engine-panel">
              <div className="panel-header"><div><div className="panel-kicker ai"><Bot size={14}/> RESQ-AI DECISION ENGINE</div><h2>Recommended next actions</h2></div><span className="confidence"><span></span> 94% confidence</span></div>
              <div className="ai-summary"><div className="ai-orb"><Sparkles size={19}/></div><div><strong>Situation summary</strong><p>{dashboard?.ai_summary || "Heavy rainfall has caused the Kolar River to breach its eastern bank. 3 zones show compounding flood risk, with an estimated 701 people requiring support within the next 2 hours."}</p></div></div>
              <div className="action-list">
                <Action n="01" title="Evacuate Riverside Colony" detail="Deploy 2 boats · open School 14 shelter" tag="Critical" onClick={() => assign("Z-01", "Evacuate Riverside Colony")}/>
                <Action n="02" title="Prioritize medical extraction" detail="12 SOS reports mention injuries or elderly" tag="High" onClick={() => assign("Z-01", "Prioritize medical extraction")}/>
                <Action n="03" title="Move supplies to Old Market Ward" detail="Road access likely to close in 45 minutes" tag="High" onClick={() => assign("Z-02", "Move supplies to Old Market Ward")}/>
              </div>
              <button className="full-btn" onClick={async () => {
  try {
    const plan = await resqApi.responsePlan(selectedZone.id);
    setResponsePlan(plan);
  } catch (error) {
    console.error("Failed to generate response plan:", error);
  }
}}>
  <Zap size={16}/> Generate full response plan
</button>
            </section>
          </div>

          <div className="lower-grid">
            <section className="panel zones-panel"><div className="panel-header"><div><div className="panel-kicker"><Target size={14}/> RISK PRIORITIZATION</div><h2>Zones requiring attention</h2></div><button className="text-btn" onClick={() => setActive("Live Map")}>View live map <Navigation size={14}/></button></div><div className="zone-list">{filteredZones.map(z => <button className={`zone-row ${selectedZone.id === z.id ? "selected" : ""}`} key={z.id} onClick={() => setSelectedZone(z)}><span className="risk-index" style={{"--risk": z.color} as React.CSSProperties}>{z.risk}</span><span className="zone-info"><strong>{z.name}</strong><small>{z.people} · {z.status}</small></span><span className="mini-bar"><i style={{width: `${z.risk}%`, background: z.color}}></i></span><ChevronDown size={16} className="row-chevron"/></button>)}</div></section>
            <section className="panel trend-panel"><div className="panel-header"><div><div className="panel-kicker"><Radio size={14}/> RESPONSE VELOCITY</div><h2>Reports vs resolved</h2></div><span className="time-chip">Last 6 hours</span></div><div className="chart-legend"><span><i className="blue-dot"></i> Incoming reports</span><span><i className="green-dot"></i> Resolved</span></div><ResponsiveContainer width="100%" height={210}><AreaChart data={chartData}><defs><linearGradient id="blueFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#4c8dff" stopOpacity=".28"/><stop offset="100%" stopColor="#4c8dff" stopOpacity="0"/></linearGradient></defs><CartesianGrid stroke="#e7edf5" vertical={false}/><XAxis dataKey="time" tickLine={false} axisLine={false} tick={{fontSize:11, fill:"#8995a8"}}/><YAxis tickLine={false} axisLine={false} tick={{fontSize:11, fill:"#8995a8"}}/><Tooltip/><Area type="monotone" dataKey="reports" stroke="#4c8dff" fill="url(#blueFill)" strokeWidth={2}/><Area type="monotone" dataKey="resolved" stroke="#31b981" fill="none" strokeWidth={2}/></AreaChart></ResponsiveContainer></section>
          </div>
          </>
          )}

          {active === "Live Map" && (
            <div className="dashboard-grid single-col">
              {mapPanel}
            </div>
          )}

          {active === "Reports & AI" && (
          <section id="reports-ai" className="panel engine-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker ai">
                  <Bot size={14}/> REPORTS & AI
                </div>
                <h2>Citizen SOS Reports</h2>
              </div>
              <span className="confidence">
                <span></span> {reports.length} live reports
              </span>
            </div>

            <div className="ai-summary">
              <div className="ai-orb">
                <Sparkles size={19}/>
              </div>
              <div>
                <strong>AI risk overview</strong>
                <p>
                  {reports.length
                    ? `${reports.filter(r => r.priority === "CRITICAL" || r.priority === "HIGH").length} high-priority reports require attention. ${reports.reduce((sum, r) => sum + (r.people || 0), 0)} people are represented across current citizen reports.`
                    : "Loading citizen SOS reports from the backend..."}
                </p>
              </div>
            </div>

            <div className="action-list">
              {reports.slice(0, 6).map((report) => (
                <div className="action-item" key={report.id}>
                  <span className="action-number">
                    {report.risk_score}
                  </span>

                  <div className="action-copy">
                    <strong>
                      {report.emergency} — {report.location || report.zone_id || "Unknown location"}
                    </strong>

                    <small>
                      {report.people} people · {report.status} · {report.source}
                      {report.medical_emergency ? " · Medical emergency" : ""}
                    </small>

                    <span className={`priority ${String(report.priority).toLowerCase()}`}>
                      {report.priority}
                    </span>
                  </div>
                  {!operations.some(operation => operation.report_id === report.id) && report.zone_id && (
                    <button
                      className="assign-btn"
                      onClick={async () => {
                        try {
                          await resqApi.assign(report.zone_id, `Respond to ${report.emergency}`, report.id);
                          await loadWorkflow();
                          setToastMessage("SOS triaged and added to rescue operations.");
                        } catch {
                          setToastMessage("Failed to create rescue operation for this SOS.");
                        }
                        setShowToast(true);
                        setTimeout(() => setShowToast(false), 2600);
                      }}
                    >
                      Create operation <Route size={14}/>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </section>
          )}
          {active === "Rescue Operations" && (
            <section id="rescue-operations" className="panel engine-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker ai">
                    <Route size={14}/> RESCUE OPERATIONS
                  </div>
                  <h2>Active response operations</h2>
                </div>
                <span className="confidence">
                  <span></span> {operations.length} operations
                </span>
              </div>

              <div className="action-list">
                {operations.length === 0 ? (
                  <div className="ai-summary">
                    <div className="ai-orb">
                      <ShieldCheck size={19}/>
                    </div>
                    <div>
                      <strong>No operations recorded</strong>
                      <p>
                        Assign a rescue action from the Command Center to create
                        an operation here.
                      </p>
                    </div>
                  </div>
                ) : (
                  operations.map((operation) => (
                    <div className="action-item" key={operation.id}>
                      <span className="action-number">
                        {liveZones.find(z => z.id === operation.zone_id)?.name || operation.zone_id}
                      </span>

                      <div className="action-copy">
                        <strong>{operation.action}</strong>
                        <small>
                          Team: {operation.team_id || "Pending assignment"}
                          {" · "}
                          Created: {new Date(operation.created_at).toLocaleString()}
                        </small>
                        {assignments.filter(assignment => assignment.action_id === operation.id).map(assignment => (
                          <p key={assignment.id}>
                            Volunteer: {assignment.volunteer_name} · {assignment.status}
                            <br />{assignment.instructions}
                          </p>
                        ))}
                        <span className={`priority ${String(operation.status).toLowerCase()}`}>
                          {operation.status.replace("_", " ")}
                        </span>
                      </div>

                      <button
  className="assign-btn"
  onClick={async () => {
    const nextStatus =
      operation.status === "QUEUED"
        ? "DEPLOYED"
        : operation.status === "DEPLOYED"
        ? "IN_PROGRESS"
        : operation.status === "IN_PROGRESS"
        ? "COMPLETED"
        : null;

    if (!nextStatus) return;

    try {
      const updated = await resqApi.updateActionStatus(
        operation.id,
        nextStatus
      );

      setOperations((current) =>
        current.map((item) =>
          item.id === operation.id ? updated : item
        )
      );
    } catch (error) {
      console.error("Failed to update operation:", error);
    }
  }}
>
  {operation.status === "QUEUED"
    ? "Deploy"
    : operation.status === "DEPLOYED"
    ? "Start"
    : operation.status === "IN_PROGRESS"
    ? "Complete"
    : "Done"}
  <ChevronDown size={14}/>
</button>
                    </div>
                  ))
                )}
              </div>
            </section>
          )}
{active === "Volunteers" && (
  <section className="panel engine-panel">
    <div className="panel-header">
      <div>
        <div className="panel-kicker ai">
          <Users size={14}/> VOLUNTEER NETWORK
        </div>
        <h2>Available volunteers</h2>
      </div>
      <span className="confidence">
        {volunteers.length} volunteers
      </span>
    </div>

    <div className="action-list">
      <div className="plan-section">
        <strong>Assign volunteer to an operation</strong>
        <div className="auth-form">
          <label>Rescue operation
            <select value={selectedActionId} onChange={e => setSelectedActionId(e.target.value)}>
              <option value="">Select an operation</option>
              {operations.filter(operation => operation.status !== "COMPLETED" && operation.status !== "CANCELLED").map(operation => (
                <option key={operation.id} value={operation.id}>{operation.action} · {operation.status}</option>
              ))}
            </select>
          </label>
          <label>Available volunteer
            <select value={selectedVolunteerId} onChange={e => setSelectedVolunteerId(e.target.value)}>
              <option value="">Select a volunteer</option>
              {volunteers.filter(volunteer => volunteer.status === "AVAILABLE").map(volunteer => (
                <option key={volunteer.id} value={volunteer.id}>
                  {volunteer.name} · {volunteer.skills || "Skills not specified"} · {volunteer.location || "Location not specified"} · {volunteer.availability}
                </option>
              ))}
            </select>
          </label>
          <label>Task instructions
            <input value={assignmentInstructions} onChange={e => setAssignmentInstructions(e.target.value)} placeholder="Provide a short task instruction" />
          </label>
          <button className="secondary-btn" type="button" disabled={assigningVolunteer || !selectedActionId || !selectedVolunteerId || !assignmentInstructions.trim()} onClick={submitVolunteerAssignment}>
            {assigningVolunteer ? "Assigning..." : "Assign volunteer"} <Users size={15}/>
          </button>
        </div>
      </div>
      {volunteers.length === 0 ? (
        <div className="ai-summary">
          <div className="ai-orb">
            <Users size={19}/>
          </div>
          <div>
            <strong>No volunteers registered</strong>
            <p>Volunteer records will appear here when registered.</p>
          </div>
        </div>
      ) : (
        volunteers.map((volunteer) => (
  <div
    className="action-item"
    key={volunteer.id}
  >
    <span className="action-number">
      <Users size={16}/>
    </span>

    <div className="action-copy">
      <strong>{volunteer.name}</strong>
      <small>
        {volunteer.skills || "Skills not specified"}
        {" · "}
        {volunteer.location || "Location not specified"}
      </small>
      <span
        className={`priority ${String(volunteer.status).toLowerCase()}`}
      >
        {volunteer.status}
      </span>
    </div>
  </div>
))
      )}
    </div>
  </section>
)}
          {active === "User Management" && (
            <section className="panel engine-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker ai"><Users size={14}/> USER MANAGEMENT</div>
                  <h2>Registered responder accounts</h2>
                </div>
                <span className="confidence">{userManagement?.users?.length ?? 0} users</span>
              </div>
              <div className="action-list">
                {(userManagement?.users ?? []).map((account: any) => (
                  <div className="action-item" key={account.id}>
                    <span className="action-number"><Users size={16}/></span>
                    <div className="action-copy">
                      <strong>{account.name}</strong>
                      <small>{account.email} · {account.role}</small>
                      {account.volunteer_id && <small>
                        Volunteer: {account.volunteer_status} · {account.volunteer_availability} · {account.volunteer_location || "Location not specified"}
                        {account.volunteer_skills ? ` · ${account.volunteer_skills}` : ""}
                      </small>}
                      <small>
                        {account.assignment_count} assigned · {account.completed_assignment_count} completed
                        {account.current_assignment ? ` · Current: ${account.current_assignment}` : ""}
                      </small>
                    </div>
                  </div>
                ))}
              </div>

              <div className="panel-header"><div><div className="panel-kicker"><Radio size={14}/> ACTIVITY</div><h2>Recent activity</h2></div></div>
              <div className="action-list">
                {(userManagement?.activity ?? []).slice(0, 12).map((event: any, index: number) => (
                  <div className="action-item" key={`${event.timestamp}-${index}`}>
                    <span className="action-number"><Clock3 size={16}/></span>
                    <div className="action-copy"><strong>{event.label}</strong><small>{new Date(event.timestamp).toLocaleString()} · {event.category}</small></div>
                  </div>
                ))}
              </div>

              <div className="panel-header"><div><div className="panel-kicker"><Siren size={14}/> CITIZEN SOS ACTIVITY</div><h2>Anonymous public reports</h2></div></div>
              <div className="action-list">
                {(userManagement?.citizen_sos ?? []).slice(0, 12).map((report: any) => (
                  <div className="action-item" key={report.report_id}>
                    <span className="action-number"><Siren size={16}/></span>
                    <div className="action-copy">
                      <strong>{report.report_id} · {report.emergency}</strong>
                      <small>{report.location || report.zone_name || "Location not specified"} · {report.people} people · {report.priority} · {report.status}</small>
                      <small>{new Date(report.created_at).toLocaleString()} · Response: {report.response_status || "Not assigned"}</small>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
          {active === "Help & Playbook" && (
            <section className="panel engine-panel">
              <div className="panel-header">
                <div>
                  <div className="panel-kicker"><CircleHelp size={14}/> HELP & PLAYBOOK</div>
                  <h2>Operational guidance</h2>
                </div>
              </div>
              <div className="action-list">
                <div className="ai-summary"><div className="ai-orb"><ShieldCheck size={19}/></div><div><strong>Review before dispatch</strong><p>Confirm the incident, zone, priority, and available response resources before assigning an operation.</p></div></div>
                <div className="ai-summary"><div className="ai-orb"><Route size={19}/></div><div><strong>Track the response</strong><p>Use Rescue Operations to move an action through deployment, active response, and completion.</p></div></div>
                <div className="ai-summary"><div className="ai-orb"><Users size={19}/></div><div><strong>Coordinate volunteers</strong><p>Assign volunteers through their existing operation, provide instructions, and monitor assignment status.</p></div></div>
              </div>
            </section>
          )}
          <div className="bottom-strip"><div className="strip-item"><CloudRain size={18}/><span><b>Weather alert</b>{commanderWeatherLocation && <small>{commanderWeatherLocation}</small>}<strong>{commanderWeatherText}</strong><small>Source: Open-Meteo</small></span><em>{dashboard?.weather && dashboard.weather.current_precipitation > 0.05 ? dashboard.weather.trend || "Current conditions" : "Stable"}</em></div><div className="strip-item"><MessageSquare size={18}/><span><b>Citizen network</b> <strong>{activeSosCount} active SOS reports</strong></span><em className="green-text">Connected</em></div><div className="strip-item"><Clock3 size={18}/><span><b>Last model refresh</b> 13:42:08 IST</span><em className="green-text">Live</em></div></div>
        </section>
      </main>
{responsePlan && (
  <div className="modal-backdrop" onClick={() => setResponsePlan(null)}>
    <div className="sos-modal response-plan-modal" onClick={e => e.stopPropagation()}>
      <button className="modal-close" onClick={() => setResponsePlan(null)}>
        <X size={18}/>
      </button>

      <div className="panel-kicker ai">
        <Sparkles size={14}/> AI RESPONSE PLAN
      </div>

      <h2>{responsePlan.zone}</h2>

      <div className="response-plan-meta">
        <span className="risk-badge">
          {responsePlan.priority}
        </span>
        <span>Risk score {responsePlan.risk_score}/100</span>
      </div>

      <div className="plan-section">
        <strong>Situation</strong>
        <p>{responsePlan.situation}</p>
      </div>

      <div className="plan-section">
        <strong>Recommended actions</strong>
        <ul>
          {responsePlan.recommended_actions.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="plan-section">
        <strong>Recommended teams</strong>
        <ul>
          {responsePlan.recommended_teams.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="plan-section">
        <strong>Resources</strong>
        <ul>
          {responsePlan.resources.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="plan-section">
        <strong>Evacuation considerations</strong>
        <ul>
          {responsePlan.evacuation_considerations.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="plan-section">
        <strong>Medical considerations</strong>
        <ul>
          {responsePlan.medical_considerations.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="advisory-notice">
        {responsePlan.advisory_notice}
      </div>

      <button className="cancel-btn" onClick={() => setResponsePlan(null)}>
        Close
      </button>
    </div>
  </div>
)}
      {showToast && <div className="toast"><ShieldCheck size={18}/><div><strong>Action queued</strong><span>{toastMessage}</span></div><X size={15} onClick={() => setShowToast(false)}/></div>}
    </div>
  );
}

function Metric({ icon, label, value, trend, tone }: { icon: React.ReactNode; label: string; value: string; trend: string; tone: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}>{icon}</div><div><span>{label}</span><strong>{value}</strong><small className={tone === "red" ? "bad" : tone === "green" ? "good" : ""}>{trend}</small></div><div className={`metric-spark ${tone}`}>↗</div></div>;
}
function Action({ n, title, detail, tag, onClick, disabled }: { n: string; title: string; detail: string; tag: Priority; onClick: () => void; disabled?: boolean }) {
  return <div className="action-item"><span className="action-number">{n}</span><div className="action-copy"><strong>{title}</strong><small>{detail}</small><span className={`priority ${tag.toLowerCase()}`}>{tag}</span></div><button className="assign-btn" onClick={onClick} disabled={disabled} title={disabled ? "Only Incident Commanders can assign operations" : undefined}>Assign <ChevronDown size={14}/></button></div>;
}

function Login({ onAuthed }: { onAuthed: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("commander@resq.ai");
  const [password, setPassword] = useState("commander123");
  const [role, setRole] = useState<Role>("VOLUNTEER");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const demoAccounts: { label: string; email: string; password: string }[] = [
    { label: "Incident Commander", email: "commander@resq.ai", password: "commander123" },
    { label: "Volunteer", email: "volunteer@resq.ai", password: "volunteer123" },
  ];

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const payload = mode === "login"
        ? await resqApi.login(email, password)
        : await resqApi.register(name, email, password, role);
      onAuthed(payload.user);
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand"><div className="brand-mark"><Siren size={21} /></div><div><strong>RESQ<span>-AI</span></strong><small>Disaster Intelligence</small></div></div>

        <div className="auth-tabs">
          <button type="button" className={mode === "login" ? "active" : ""} onClick={() => { setMode("login"); setError(""); }}>Sign in</button>
          <button type="button" className={mode === "register" ? "active" : ""} onClick={() => { setMode("register"); setError(""); }}>Register</button>
        </div>

        <form onSubmit={submit} className="auth-form">
          {mode === "register" && (
            <label>Full name
              <input value={name} onChange={e => setName(e.target.value)} required placeholder="Jane Doe" />
            </label>
          )}
          <label>Email
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@resq.ai" />
          </label>
          <label>Password
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} placeholder="••••••••" />
          </label>
          {mode === "register" && (
            <label>Role
              <select value={role} onChange={e => setRole(e.target.value as Role)}>
                <option value="VOLUNTEER">Volunteer</option>
                <option value="INCIDENT_COMMANDER">Incident Commander</option>
              </select>
            </label>
          )}

          {error && <div className="auth-error"><AlertTriangle size={14}/> {error}</div>}

          <button className="danger-btn wide" type="submit" disabled={busy}>
            {busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"} <Siren size={16}/>
          </button>
        </form>

        <div className="auth-demo">
          <small>Demo accounts</small>
          <div className="auth-demo-list">
            {demoAccounts.map(d => (
              <button type="button" key={d.label} onClick={() => { setMode("login"); setEmail(d.email); setPassword(d.password); setError(""); }}>
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PublicSOS({ onGoToLogin }: { onGoToLogin: () => void }) {
  const [emergency, setEmergency] = useState("Flood");
  const [people, setPeople] = useState(1);
  const [medical, setMedical] = useState(false);
  const [location, setLocation] = useState("");
  const [flood, setFlood] = useState(15);
  const [infra, setInfra] = useState(5);
  const [weather, setWeather] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const res = await resqApi.createReport({
        emergency,
        people,
        medical_emergency: medical,
        location: location || undefined,
        flood_severity: flood,
        infrastructure_damage: infra,
        weather_severity: weather,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Could not send SOS. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <div className="brand"><div className="brand-mark"><ShieldCheck size={21} /></div><div><strong>RESQ<span>-AI</span></strong><small>SOS received</small></div></div>
          <div className="plan-section">
            <strong>Your report has been logged</strong>
            <p>{result.message}</p>
          </div>
          <div className="response-plan-meta">
            <span className="risk-badge">{result.priority}</span>
            <span>Risk score {result.risk_score}/100</span>
          </div>
          <div className="advisory-notice">Report ID: {result.report_id}. Your emergency report has been received and is being reviewed.</div>
          <button className="danger-btn wide" onClick={() => setResult(null)}>Send another report</button>
          <button className="cancel-btn" onClick={onGoToLogin}>Responder / Admin login</button>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand"><div className="brand-mark"><Siren size={21} /></div><div><strong>RESQ<span>-AI</span></strong><small>Report an emergency</small></div></div>
        <form onSubmit={submit} className="auth-form">
          <label>Emergency type
            <select value={emergency} onChange={e => setEmergency(e.target.value)}>
              <option>Flood</option>
              <option>Fire</option>
              <option>Earthquake</option>
              <option>Landslide</option>
              <option>Other</option>
            </select>
          </label>
          <label>Number of people affected
            <input type="number" min={1} value={people} onChange={e => setPeople(Number(e.target.value))} required />
          </label>
          <label>Location (area / landmark)
            <input value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. Riverside Colony" />
          </label>
          <label><input type="checkbox" checked={medical} onChange={e => setMedical(e.target.checked)} style={{ marginRight: 8 }} />Medical emergency present</label>
          <label>Flood severity ({flood}/25)
            <input type="range" min={0} max={25} value={flood} onChange={e => setFlood(Number(e.target.value))} />
          </label>
          <label>Infrastructure damage ({infra}/15)
            <input type="range" min={0} max={15} value={infra} onChange={e => setInfra(Number(e.target.value))} />
          </label>
          <label>Weather severity ({weather}/10)
            <input type="range" min={0} max={10} value={weather} onChange={e => setWeather(Number(e.target.value))} />
          </label>

          {error && <div className="auth-error"><AlertTriangle size={14}/> {error}</div>}

          <button className="danger-btn wide" type="submit" disabled={busy}>
            {busy ? "Sending SOS..." : "Broadcast SOS"} <Siren size={16}/>
          </button>
        </form>
        <div className="auth-demo">
          <button type="button" className="cancel-btn" onClick={onGoToLogin}>Responder / Admin login</button>
        </div>
      </div>
    </div>
  );
}

function VolunteerDashboard({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [assignments, setAssignments] = useState<any[]>([]);
  const [weather, setWeather] = useState<any>(null);
  const [error, setError] = useState("");
  const [busyAssignment, setBusyAssignment] = useState("");
  const load = () => resqApi.myAssignments().then(setAssignments).catch((e) => setError(e.message));
  useEffect(() => { resqApi.myWeather().then(setWeather).catch(() => setWeather(null)); }, [assignments]);
  useEffect(() => {
    void load();
    const timer = window.setInterval(() => { void load(); }, 10000);
    return () => window.clearInterval(timer);
  }, []);
  const accept = async (assignmentId: string) => {
    setBusyAssignment(assignmentId);
    try { await resqApi.acceptAssignment(assignmentId); await load(); } catch (e: any) { setError(e.message); } finally { setBusyAssignment(""); }
  };
  const complete = async (assignmentId: string) => {
    setBusyAssignment(assignmentId);
    try { await resqApi.completeAssignment(assignmentId); await load(); } catch (e: any) { setError(e.message); } finally { setBusyAssignment(""); }
  };
  return <div className="auth-shell"><div className="auth-card"><div className="brand"><div className="brand-mark"><Users size={21}/></div><div><strong>RESQ<span>-AI</span></strong><small>Volunteer workspace</small></div></div><div className="plan-section"><strong>{user.name}</strong><p>Your assignments are provided by the Incident Commander. You cannot access command-center controls.</p></div><div className="plan-section"><strong>Weather in operational area</strong>{weather ? <><small>{weather.location_name}</small><small>{weather.condition} · Rainfall {weather.current_precipitation.toFixed(1)} mm · {weather.trend || "Current conditions"}</small><small>Source: {weather.source}</small></> : <small>Operational weather unavailable</small>}</div>{error && <div className="auth-error">{error}</div>}{assignments.length === 0 ? <div className="plan-section"><strong>No current assignment</strong><p>Remain available and wait for a coordinator instruction.</p></div> : assignments.map(a => <div className="action-item" key={a.id}><span className="action-number"><Route size={16}/></span><div className="action-copy"><strong>{a.action?.action}</strong><small>Zone: {a.action?.zone_id} · Operation: {a.action?.status}</small><p>{a.instructions}</p><span className={`priority ${String(a.status).toLowerCase()}`}>{a.status}</span></div>{a.status === "ASSIGNED" && <button className="assign-btn" disabled={busyAssignment === a.id} onClick={() => accept(a.id)}>{busyAssignment === a.id ? "Accepting..." : "Accept assignment"}</button>}{a.status === "IN_PROGRESS" && <button className="assign-btn" disabled={busyAssignment === a.id} onClick={() => complete(a.id)}>{busyAssignment === a.id ? "Completing..." : "Complete task"}</button>}</div>)}<button className="cancel-btn" onClick={onLogout}>Log out</button></div></div>;
}

function CitizenPortal({ onGoToLogin }: { onGoToLogin: () => void }) {
  const [page, setPage] = useState("Emergency Home");
  const [emergency, setEmergency] = useState("Flood"); const [people, setPeople] = useState(1); const [location, setLocation] = useState(""); const [locationMode, setLocationMode] = useState("GPS"); const [medical, setMedical] = useState(false);
  const [report, setReport] = useState<any>(null); const [reportId, setReportId] = useState(localStorage.getItem("resq_ai_last_report") || ""); const [tracking, setTracking] = useState<any>(null); const [shelters, setShelters] = useState<any[]>([]); const [alerts, setAlerts] = useState<any[]>([]); const [error, setError] = useState(""); const [latitude, setLatitude] = useState<number | undefined>(); const [longitude, setLongitude] = useState<number | undefined>(); const [locationError, setLocationError] = useState(false); const [gpsPlaceName, setGpsPlaceName] = useState(""); const [localWeather, setLocalWeather] = useState<any>(null);
  useEffect(() => { if (page === "Shelters / Safe Locations") resqApi.publicShelters().then(setShelters).catch(e => setError(e.message)); if (page === "Emergency Alerts") resqApi.publicAlerts().then(setAlerts).catch(e => setError(e.message)); }, [page]);
  const detectLocation = () => {
    setLocationError(false);
    if (!navigator.geolocation) {
      setLocationError(true);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      p => { setLatitude(p.coords.latitude); setLongitude(p.coords.longitude); setLocationError(false); },
      () => { setLatitude(undefined); setLongitude(undefined); setLocationError(true); },
    );
  };
  useEffect(() => { if ((page === "Send SOS" || page === "Emergency Home") && latitude == null && longitude == null) detectLocation(); }, [page, latitude, longitude]);
  useEffect(() => {
    if (locationMode !== "GPS" || latitude == null || longitude == null) {
      setGpsPlaceName("");
      return;
    }
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5000);
    fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}&zoom=18&addressdetails=1`, {
      headers: { "Accept-Language": "en" },
      signal: controller.signal,
    })
      .then(response => response.ok ? response.json() : null)
      .then(data => {
        if (!data || typeof data.display_name !== "string" || !data.display_name.trim()) return;
        setGpsPlaceName(data.display_name.trim());
      })
      .catch(() => undefined)
      .finally(() => window.clearTimeout(timeout));
    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [locationMode, latitude, longitude]);
  useEffect(() => {
    if (latitude == null || longitude == null) {
      setLocalWeather(null);
      return;
    }
    resqApi.publicWeather(latitude, longitude).then(setLocalWeather).catch(() => setLocalWeather(null));
  }, [latitude, longitude]);
  useEffect(() => {
    if (page !== "Track My SOS" || !reportId) return;
    const refreshTracking = () => resqApi.trackReport(reportId).then(setTracking).catch(e => setError(e.message));
    refreshTracking();
    const timer = window.setInterval(refreshTracking, 10000);
    return () => window.clearInterval(timer);
  }, [page, reportId]);
  const submit = async (e: React.FormEvent) => { e.preventDefault(); setError(""); try {
    const selectedZone = zones.find(zone => zone.id === locationMode);
    const reportLocation = selectedZone?.name || (locationMode === "GPS" && latitude != null && longitude != null ? "Current GPS location" : locationMode === "OTHER" ? location : undefined);
    const result = await resqApi.createReport({ emergency, people, medical_emergency: medical, location: reportLocation || undefined, latitude: selectedZone?.coords[0] ?? (locationMode === "GPS" ? latitude : undefined), longitude: selectedZone?.coords[1] ?? (locationMode === "GPS" ? longitude : undefined), flood_severity: emergency === "Flood" ? 15 : 5, infrastructure_damage: 5, weather_severity: 5 }); localStorage.setItem("resq_ai_last_report", result.report_id); setReportId(result.report_id); setReport(result); setTracking(await resqApi.trackReport(result.report_id)); setPage("Track My SOS");
  } catch (e: any) { setError(e.message); } };
  const nav = ["Emergency Home", "Send SOS", "Track My SOS", "Shelters / Safe Locations", "Emergency Alerts", "Emergency Help / Playbook"];
  if (page === "Emergency Home") return <div className="auth-shell"><div className="auth-card"><div className="brand"><div className="brand-mark"><Siren size={21}/></div><div><strong>RESQ<span>-AI</span></strong><small>Citizen emergency support</small></div></div><div className="auth-demo-list">{nav.map(item => <button key={item} type="button" onClick={() => setPage(item)}>{item}</button>)}</div><div className="plan-section"><strong>Emergency Home</strong><p>If you are in immediate danger, move to a safe location when possible and send an SOS. View current area alerts, nearby shelters, and simple emergency guidance here.</p></div><div className="plan-section"><strong>Weather in your area: </strong>{latitude != null && longitude != null ? <>{gpsPlaceName && <small>{gpsPlaceName} · </small>}{localWeather ? <small>{localWeather.condition} · Rainfall {localWeather.current_precipitation.toFixed(1)} mm · {localWeather.trend || "Current conditions"}</small> : <small>Weather data unavailable</small>}<small> Source: Open-Meteo</small></> : <small>Location unavailable</small>}</div><button className="danger-btn wide" onClick={() => setPage("Send SOS")}>Send SOS</button><button className="cancel-btn" onClick={onGoToLogin}>Responder / volunteer login</button></div></div>;
  if (page === "Send SOS") return <div className="auth-shell"><div className="auth-card"><div className="brand"><div className="brand-mark"><Siren size={21}/></div><div><strong>RESQ<span>-AI</span></strong><small>Citizen emergency support</small></div></div><div className="auth-demo-list">{nav.map(item => <button key={item} type="button" onClick={() => setPage(item)}>{item}</button>)}</div><div className="plan-section"><strong>Send SOS</strong></div>{error && <div className="auth-error">{error}</div>}<form onSubmit={submit} className="auth-form"><label>Emergency type<select value={emergency} onChange={e => setEmergency(e.target.value)}><option>Flood</option><option>Fire</option><option>Earthquake</option><option>Landslide</option><option>Medical</option></select></label><label>People affected<input type="number" min={1} value={people} onChange={e => setPeople(Number(e.target.value))}/></label><label>Location<select value={locationMode} onChange={e => setLocationMode(e.target.value)}><option value="GPS">Current GPS location</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.name}</option>)}<option value="OTHER">Other / enter manually</option></select></label>{locationMode === "GPS" && (latitude != null && longitude != null ? <div className="plan-section"><strong>Current location detected: </strong>{gpsPlaceName && <small>{gpsPlaceName}</small>}<small> Latitude {latitude.toFixed(5)} · Longitude {longitude.toFixed(5)}</small><small> This location will be included with your SOS. </small></div> : <div className="plan-section"><strong> Location unavailable </strong><small>GPS is unavailable or permission was denied. You can still send your SOS.</small><button type="button" className="secondary-btn" onClick={detectLocation}>Try again</button></div>)}{locationMode === "OTHER" && <label>Location / landmark<input value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. Riverside Colony" /></label>}<button className="danger-btn wide">Send SOS</button></form></div></div>;
  return <div className="auth-shell"><div className="auth-card"><div className="brand"><div className="brand-mark"><Siren size={21}/></div><div><strong>RESQ<span>-AI</span></strong><small>Citizen emergency support</small></div></div><div className="auth-demo-list">{nav.map(item => <button key={item} type="button" onClick={() => setPage(item)}>{item}</button>)}</div><div className="plan-section"><strong>{page}</strong></div>{error && <div className="auth-error">{error}</div>}{page === "Emergency Home" && <div className="plan-section"><p>If you are in immediate danger, move to a safe location when possible and send an SOS. View current area alerts, nearby shelters, and simple emergency guidance here.</p><button className="danger-btn wide" onClick={() => setPage("Send SOS")}>Send SOS</button></div>}{page === "Send SOS" && <form onSubmit={submit} className="auth-form"><label>Emergency type<select value={emergency} onChange={e => setEmergency(e.target.value)}><option>Flood</option><option>Fire</option><option>Earthquake</option><option>Landslide</option><option>Medical</option></select></label><label>People affected<input type="number" min={1} value={people} onChange={e => setPeople(Number(e.target.value))}/></label><label>Location<select value={locationMode} onChange={e => setLocationMode(e.target.value)}><option value="GPS">Current GPS location</option>{zones.map(zone => <option key={zone.id} value={zone.id}>{zone.name}</option>)}<option value="OTHER">Other / enter manually</option></select></label>{locationMode === "GPS" && (latitude != null && longitude != null ? <div className="plan-section"><strong>Current location detected</strong><small>Latitude {latitude.toFixed(5)} · Longitude {longitude.toFixed(5)}</small><small>This location will be included with your SOS.</small></div> : <div className="plan-section"><strong>Location unavailable</strong><small>GPS is unavailable or permission was denied. You can still send your SOS.</small><button type="button" className="secondary-btn" onClick={detectLocation}>Try again</button></div>)}{locationMode === "OTHER" && <label>Location / landmark<input value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. Riverside Colony" /></label>}<label><input type="checkbox" checked={medical} onChange={e => setMedical(e.target.checked)}/> Medical emergency</label><button className="danger-btn wide">Send SOS</button></form>}{page === "Track My SOS" && <div className="auth-form"><label>Report ID<input value={reportId} onChange={e => setReportId(e.target.value)}/></label><button className="secondary-btn" onClick={async () => { try { setTracking(await resqApi.trackReport(reportId)); } catch (e: any) { setError(e.message); } }}>Check status</button>{(tracking || report) && <div className="plan-section"><strong>{tracking?.status || "RECEIVED"}</strong><p>{tracking?.message || "Your emergency report has been received and is being reviewed."}</p><small>Report ID: {tracking?.report_id || report?.report_id}</small></div>}</div>}{page === "Shelters / Safe Locations" && shelters.map(s => <div className="action-item" key={s.id}><span className="action-number"><MapPinned size={16}/></span><div className="action-copy"><strong>{s.name}</strong><small>{s.location} · {s.status}</small><p>{s.available_capacity} spaces available of {s.capacity}</p></div></div>)}{page === "Emergency Alerts" && alerts.map(a => <div className="action-item" key={a.id}><span className="action-number">!</span><div className="action-copy"><strong>{a.title}</strong><small>{a.message}</small><span className={`priority ${a.severity.toLowerCase()}`}>{a.severity}</span></div></div>)}{page === "Emergency Help / Playbook" && <div className="plan-section"><ul><li>Move away from floodwater, damaged structures, and downed power lines.</li><li>Share your location and number of people needing help in an SOS.</li><li>Keep your phone charged, conserve battery, and follow official alerts.</li><li>Use listed shelters only when they are marked open.</li></ul></div>}<button className="cancel-btn" onClick={onGoToLogin}>Responder / volunteer login</button></div></div>;
}

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [view, setView] = useState<"sos" | "login">("sos");

  useEffect(() => {
    (async () => {
      if (!resqApi.isAuthenticated()) { setChecking(false); return; }
      try {
        const me = await resqApi.me();
        setUser(me);
      } catch {
        resqApi.logout();
      } finally {
        setChecking(false);
      }
    })();
  }, []);

  if (checking) {
    return <div className="auth-shell"><div className="auth-loading"><Siren size={24}/> Loading RESQ-AI...</div></div>;
  }

  if (user) {
    return user.role === "INCIDENT_COMMANDER" ? <Dashboard user={user} onLogout={() => { resqApi.logout(); setUser(null); setView("sos"); }} /> : <VolunteerDashboard user={user} onLogout={() => { resqApi.logout(); setUser(null); setView("sos"); }} />;
  }

  if (view === "login") {
    return <Login onAuthed={setUser} />;
  }

  return <CitizenPortal onGoToLogin={() => setView("login")} />;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
