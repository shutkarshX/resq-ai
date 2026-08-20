"""Pydantic schemas for request validation and response shaping.

Kept deliberately close to what the frontend already expects (see api.ts)
so /api/dashboard and /api/actions/assign need zero frontend changes.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


# ---------- Health ----------

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str
    timestamp: str


# ---------- Zones ----------

class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    latitude: float
    longitude: float
    risk_score: int
    people_at_risk: int
    status: str
    color: str


class ZoneDetailOut(ZoneOut):
    active_incidents: int = 0
    active_teams: int = 0
    recent_reports: int = 0


# ---------- Dashboard (matches frontend's DashboardPayload in api.ts) ----------

class IncidentSummary(BaseModel):
    name: str
    severity: str
    updated_at: str


class MetricsOut(BaseModel):
    active_incidents: int
    people_at_risk: int
    teams_deployed: int
    teams_total: int
    cases_resolved: int


class WeatherOut(BaseModel):
    current_precipitation: float
    condition: str
    trend: Optional[str] = None
    updated_at: str
    source: str


class WeatherLocationOut(WeatherOut):
    location_name: Optional[str] = None


class DashboardOut(BaseModel):
    incident: IncidentSummary
    metrics: MetricsOut
    zones: List[ZoneOut]
    ai_summary: str
    weather: Optional[WeatherOut] = None


# ---------- Reports / SOS ----------

class SOSReportIn(BaseModel):
    emergency: str = Field(..., min_length=1)
    people: int = Field(..., ge=0)
    medical_emergency: bool = False
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    flood_severity: int = Field(0, ge=0, le=25)
    infrastructure_damage: int = Field(0, ge=0, le=15)
    weather_severity: int = Field(0, ge=0, le=10)


class SOSReportAccepted(BaseModel):
    accepted: bool
    report_id: str
    incident_id: Optional[str] = None
    zone_id: Optional[str] = None
    risk_score: int
    priority: str
    message: str


class PublicSOSStatusOut(BaseModel):
    report_id: str
    emergency: str
    location: Optional[str] = None
    priority: str
    status: str
    created_at: datetime
    message: str
    response_status: Optional[str] = None
    response_summary: Optional[str] = None


class SOSReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    emergency: str
    people: int
    medical_emergency: bool
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    flood_severity: int
    infrastructure_damage: int
    weather_severity: int
    risk_score: int
    priority: str
    status: str
    zone_id: Optional[str] = None
    incident_id: Optional[str] = None
    source: str
    summary: Optional[str] = None
    created_at: datetime


# ---------- Incidents ----------

class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    emergency_type: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    people_at_risk: int
    medical_emergency: bool
    risk_score: int
    priority: str
    status: str
    zone_id: Optional[str] = None
    created_at: datetime


# ---------- Teams ----------

class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    team_type: str
    members: int
    status: str
    current_zone_id: Optional[str] = None


class TeamCreateIn(BaseModel):
    name: str
    team_type: str
    members: int = Field(4, ge=1)


# ---------- Actions / Dispatch ----------

class ActionAssignIn(BaseModel):
    zone_id: str
    action: str
    team_id: Optional[str] = None
    assignee: Optional[str] = None  # accepted for backward-compat w/ old frontend calls
    report_id: Optional[str] = None


class ActionAssignOut(BaseModel):
    accepted: bool
    action_id: str
    team_id: Optional[str] = None
    zone_id: str
    incident_id: Optional[str] = None
    status: str
    message: str
    queued_at: str


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    zone_id: str
    team_id: Optional[str] = None
    report_id: Optional[str] = None
    incident_id: Optional[str] = None
    action: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ActionStatusUpdateIn(BaseModel):
    status: str = Field(..., pattern="^(QUEUED|DEPLOYED|IN_PROGRESS|COMPLETED|CANCELLED)$")


# ---------- AI ----------

class AIAnalyzeIn(BaseModel):
    incident_id: Optional[str] = None
    emergency: str
    people: int = 0
    medical_emergency: bool = False
    weather: Optional[str] = None
    area: Optional[str] = None
    risk_score: Optional[int] = None
    priority: Optional[str] = None


class AIAnalyzeOut(BaseModel):
    success: bool
    situation: str
    recommendations: List[str]
    potential_risks: List[str]
    required_resources: List[str]
    confidence: float
    advisory_notice: str = (
        "This is AI decision-support only. No real-world dispatch, evacuation, "
        "or emergency contact has occurred. A human operator must review and "
        "execute all actions."
    )


class ResponsePlanIn(BaseModel):
    zone_id: str


class ResponsePlanOut(BaseModel):
    zone: str
    zone_id: str
    risk_score: int
    priority: str
    situation: str
    recommended_actions: List[str]
    recommended_teams: List[str]
    resources: List[str]
    evacuation_considerations: List[str]
    medical_considerations: List[str]
    advisory_notice: str = (
        "This is AI decision-support only. No real-world dispatch, evacuation, "
        "or emergency contact has occurred. A human operator must review and "
        "execute all actions."
    )


# ---------- Volunteers ----------

class VolunteerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: Optional[str] = None
    name: str
    skills: Optional[str] = None
    availability: str
    location: Optional[str] = None
    status: str


class VolunteerCreateIn(BaseModel):
    name: str
    skills: Optional[str] = None
    location: Optional[str] = None


class VolunteerUpdateIn(BaseModel):
    status: Optional[str] = Field(None, pattern="^(AVAILABLE|ASSIGNED|OFFLINE)$")
    availability: Optional[str] = Field(None, pattern="^(AVAILABLE|ASSIGNED|OFFLINE)$")
    skills: Optional[str] = None
    location: Optional[str] = None


class VolunteerAssignmentCreateIn(BaseModel):
    volunteer_id: str
    action_id: str
    instructions: str = Field(..., min_length=1)


class VolunteerAssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    action_id: str
    instructions: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    action: ActionOut


class CommanderVolunteerAssignmentOut(VolunteerAssignmentOut):
    volunteer_id: str
    volunteer_name: str
    volunteer_skills: Optional[str] = None
    volunteer_location: Optional[str] = None


class ShelterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    capacity: int
    available_capacity: int


class CitizenAlertOut(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    zone_name: Optional[str] = None


# ---------- Auth ----------

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str


class UserManagementOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
    volunteer_id: Optional[str] = None
    volunteer_status: Optional[str] = None
    volunteer_availability: Optional[str] = None
    volunteer_skills: Optional[str] = None
    volunteer_location: Optional[str] = None
    assignment_count: int
    active_assignment_count: int
    completed_assignment_count: int
    current_assignment: Optional[str] = None


class CitizenActivityOut(BaseModel):
    report_id: str
    emergency: str
    location: Optional[str] = None
    zone_name: Optional[str] = None
    people: int
    priority: str
    status: str
    created_at: datetime
    response_status: Optional[str] = None


class ActivityEventOut(BaseModel):
    label: str
    category: str
    timestamp: datetime


class UserManagementPayload(BaseModel):
    users: list[UserManagementOut]
    citizen_sos: list[CitizenActivityOut]
    activity: list[ActivityEventOut]


class RegisterIn(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(INCIDENT_COMMANDER|VOLUNTEER)$")


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Search ----------

class SearchResults(BaseModel):
    zones: List[ZoneOut]
    incidents: List[IncidentOut]
    reports: List[SOSReportOut]
    teams: List[TeamOut]
