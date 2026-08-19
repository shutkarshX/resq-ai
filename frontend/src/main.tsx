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
import { resqApi, type DashboardPayload } from "./api";

type Priority = "Critical" | "High" | "Medium";
type Zone = { id: string; name: string; risk: number; people: string; status: string; color: string; coords: [number, number]; };

const chartData = [
  { time: "08:00", reports: 18, resolved: 4 }, { time: "09:00", reports: 35, resolved: 13 },
  { time: "10:00", reports: 58, resolved: 25 }, { time: "11:00", reports: 84, resolved: 47 },
  { time: "12:00", reports: 102, resolved: 71 }, { time: "13:00", reports: 128, resolved: 96 },
];
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

function App() {
  const [active, setActive] = useState("Command Center");
  const [selectedZone, setSelectedZone] = useState<Zone>(zones[0]);
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [apiState, setApiState] = useState<"connecting" | "online" | "demo">("connecting");
  const [refreshing, setRefreshing] = useState(false);
  const [sosSubmitting, setSosSubmitting] = useState(false);
  const [sosEmergency, setSosEmergency] = useState("Flood");
  const [sosPeople, setSosPeople] = useState(1);
  const [sosMedical, setSosMedical] = useState(false);
  const [showSOS, setShowSOS] = useState(false);
  const [responsePlan, setResponsePlan] = useState<any>(null);
  const [showToast, setShowToast] = useState(false);
  const [search, setSearch] = useState("");
  const [mobileNav, setMobileNav] = useState(false);
  const [reports, setReports] = useState<any[]>([]);
  const [operations, setOperations] = useState<any[]>([]);
  const nav = [
    { label: "Command Center", icon: Target }, { label: "Live Map", icon: MapPinned },
    { label: "Reports & AI", icon: FileText }, { label: "Rescue Operations", icon: Route },
    { label: "Volunteers", icon: Users },
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
      coords: zones[index]?.coords || zones[0].coords,
    }));
  }, [dashboard]);
  const filteredZones = useMemo(() => liveZones.filter(z => z.name.toLowerCase().includes(search.toLowerCase())), [liveZones, search]);    const submitSOS = async () => {
  setSosSubmitting(true);

  try {
    await resqApi.createReport({
      emergency: sosEmergency,
      people: sosPeople,
      medical_emergency: sosMedical,
      location: `${selectedZone.name} area`,
      latitude: selectedZone.coords[0],
      longitude: selectedZone.coords[1],
      flood_severity: 20,
      infrastructure_damage: 0,
      weather_severity: 7,
    });

    setShowSOS(false);
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2600);

    const updatedReports = await resqApi.reports();
    setReports(updatedReports);
    await loadDashboard();
  } catch (error) {
    console.error("SOS submission failed:", error);
  } finally {
    setSosSubmitting(false);
  }
};

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
  useEffect(() => {
    loadDashboard();
    resqApi.reports().then(setReports).catch(() => setReports([]));
    resqApi.actions().then(setOperations).catch(() => setOperations([]));
    const timer = window.setInterval(loadDashboard, 30000);
    return () => window.clearInterval(timer);
  }, []);
  const assign = async (zoneId = selectedZone.id, action = "Dispatch nearest available rescue team") => {
    try { await resqApi.assign(zoneId, action); } catch { /* Keep demo interactions available offline. */ }
    setShowToast(true);
    setTimeout(() => setShowToast(false), 2600);
  };

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand"><div className="brand-mark"><Siren size={21} /></div><div><strong>RESQ<span>-AI</span></strong><small>Disaster Intelligence</small></div><button className="icon-btn mobile-close" onClick={() => setMobileNav(false)}><X size={19}/></button></div>
        <div className="live-pill"><span className="pulse"></span> LIVE INCIDENT <span className="pill-dot">●</span></div>
        <nav>{nav.map(({ label, icon: Icon }) => <button key={label} className={active === label ? "nav-item active" : "nav-item"} onClick={() => { setActive(label); setMobileNav(false); if (label === "Live Map") setTimeout(() => document.getElementById("live-map")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50); }}><Icon size={18}/><span>{label}</span>{label === "Reports & AI" && <b className="nav-count">12</b>}</button>)}</nav>
        <div className="sidebar-bottom">
          <button className="nav-item"><CircleHelp size={18}/><span>Help & playbook</span></button>
          <div className="user-card"><div className="avatar">AK</div><div><strong>Arjun Kumar</strong><small>Incident Commander</small></div><ChevronDown size={16}/></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setMobileNav(true)}><Menu size={21}/></button>
          <div className="breadcrumb"><span>Operations</span><b>/</b><strong>{active}</strong></div>
          <div className="top-actions"><div className="search-box"><Search size={16}/><input placeholder="Search reports, zones..." value={search} onChange={e => setSearch(e.target.value)} /></div><button className="icon-btn notification"><Bell size={18}/><i></i></button><button className="profile">AK</button></div>
        </header>
        <section className="content">
          <div className="page-heading"><div><div className="eyebrow"><span className="status-dot"></span> INCIDENT ACTIVE · UPDATED JUST NOW</div><h1>Command Center</h1><p>AI-assisted operational view for <strong>{dashboard?.incident.name || "Bhopal Flood Response"}</strong></p></div><div className="heading-actions"><span className={`connection-state ${apiState}`}><Wifi size={13}/> {apiState === "online" ? "Backend connected" : apiState === "demo" ? "Demo data" : "Connecting"}</span><button className="secondary-btn" onClick={loadDashboard}><RefreshCw size={16} className={refreshing ? "spin" : ""}/> Refresh</button><button className="danger-btn" onClick={() => setShowSOS(true)}><Siren size={16}/> Trigger Citizen SOS</button></div></div>

          <div className="metrics-grid">
            <Metric icon={<AlertTriangle/>} label="Active incidents" value={String(dashboard?.metrics.active_incidents ?? 0).padStart(2, "0")} trend="+2 today" tone="red" />
            <Metric icon={<Users/>} label="People at risk" value={(dashboard?.metrics.people_at_risk ?? 0).toLocaleString()} trend="−8% vs 1h" tone="amber" />
            <Metric icon={<HeartPulse/>} label="Rescue teams deployed" value={`${dashboard?.metrics.teams_deployed ?? 0} / ${dashboard?.metrics.teams_total ?? 0}`} trend="75% capacity" tone="blue" />
            <Metric icon={<ShieldCheck/>} label="Cases resolved" value={String(dashboard?.metrics.cases_resolved ?? 0)} trend="+24 this hour" tone="green" />
          </div>

          <div className="dashboard-grid">
            <section id="live-map" className="panel map-panel">
              <div className="panel-header"><div><div className="panel-kicker"><MapPinned size={14}/> GEOSPATIAL INTELLIGENCE</div><h2>Priority rescue zones</h2></div><div className="map-tools"><button className="tiny-btn active"><Crosshair size={14}/> Live</button><button className="tiny-btn"><Layers3 size={14}/></button></div></div>
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
                </div>
              ))}
            </div>
          </section>
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
                        {operation.zone_id}
                      </span>

                      <div className="action-copy">
                        <strong>{operation.action}</strong>
                        <small>
                          Team: {operation.team_id || "Pending assignment"}
                          {" · "}
                          Created: {new Date(operation.created_at).toLocaleString()}
                        </small>
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
          <div className="bottom-strip"><div className="strip-item"><CloudRain size={18}/><span><b>Weather alert</b> Rainfall intensity <strong>68 mm/hr</strong></span><em>+12%</em></div><div className="strip-item"><Thermometer size={18}/><span><b>River gauge</b> Kolar River level <strong>3.8m / 4.5m</strong></span><em className="amber-text">Rising</em></div><div className="strip-item"><MessageSquare size={18}/><span><b>Citizen network</b> <strong>128 live SOS reports</strong></span><em className="green-text">Connected</em></div><div className="strip-item"><Clock3 size={18}/><span><b>Last model refresh</b> 13:42:08 IST</span><em className="green-text">Live</em></div></div>
        </section>
      </main>
      {showSOS && <div className="modal-backdrop" onClick={() => setShowSOS(false)}><div className="sos-modal" onClick={e => e.stopPropagation()}><button className="modal-close" onClick={() => setShowSOS(false)}><X size={18}/></button><div className="sos-icon"><PhoneCall size={23}/></div><div className="panel-kicker red">CITIZEN SOS BROADCAST</div><h2>Start an emergency broadcast?</h2><p>This will open a public SOS intake channel and notify all nearby response teams. Use only for an active emergency.</p><div className="sos-field">
  <label>Emergency type</label>
  <select value={sosEmergency} onChange={e => setSosEmergency(e.target.value)}>
    <option value="Flood">Flood</option>
    <option value="Medical">Medical</option>
    <option value="Infrastructure">Infrastructure</option>
    <option value="Shelter">Shelter</option>
  </select>
</div><div className="sos-field">
  <label>People needing help</label>
  <input
    type="number"
    min="1"
    value={sosPeople}
    onChange={e => setSosPeople(Math.max(1, Number(e.target.value)))}
  />
</div><div className="sos-field">
  <label>
    <input
      type="checkbox"
      checked={sosMedical}
      onChange={e => setSosMedical(e.target.checked)}
    />
    Medical emergency
  </label>
</div><div className="sos-preview"><MapPinned size={17}/><span><b>Bhopal response area</b><small>GPS radius · 8 km</small></span></div><button className="danger-btn wide" onClick={submitSOS} disabled={sosSubmitting}>
  {sosSubmitting ? "Sending SOS..." : "Broadcast SOS channel"} <Siren size={16}/>
</button><button className="cancel-btn" onClick={() => setShowSOS(false)}>Cancel</button></div></div>}
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
      {showToast && <div className="toast"><ShieldCheck size={18}/><div><strong>Action queued</strong><span>Response team has been notified and assigned.</span></div><X size={15} onClick={() => setShowToast(false)}/></div>}
    </div>
  );
}

function Metric({ icon, label, value, trend, tone }: { icon: React.ReactNode; label: string; value: string; trend: string; tone: string }) {
  return <div className="metric-card"><div className={`metric-icon ${tone}`}>{icon}</div><div><span>{label}</span><strong>{value}</strong><small className={tone === "red" ? "bad" : tone === "green" ? "good" : ""}>{trend}</small></div><div className={`metric-spark ${tone}`}>↗</div></div>;
}
function Action({ n, title, detail, tag, onClick }: { n: string; title: string; detail: string; tag: Priority; onClick: () => void }) {
  return <div className="action-item"><span className="action-number">{n}</span><div className="action-copy"><strong>{title}</strong><small>{detail}</small><span className={`priority ${tag.toLowerCase()}`}>{tag}</span></div><button className="assign-btn" onClick={onClick}>Assign <ChevronDown size={14}/></button></div>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);




