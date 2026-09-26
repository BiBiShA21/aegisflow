"""
AegisFlow - Pydantic Schemas for all API models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ConfidenceLevel(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


# ─── AUTH SCHEMAS ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    organization: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    github_username: Optional[str] = ""
    occupation: Optional[str] = "Developer"


class LoginRequest(BaseModel):
    username: str
    password: str
    rememberMe: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    github_username: Optional[str] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None


# ─── SCAN SCHEMAS ──────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str = Field(default="python")
    filename: Optional[str] = "unknown"
    use_gemini: bool = True
    workspace_id: Optional[str] = None


class VulnerabilityResult(BaseModel):
    type: str
    severity: SeverityLevel
    line: Optional[int] = None
    description: str
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_id: Optional[str] = None
    confidence: float = 0.0
    confidence_level: Optional[str] = None


class AnalyzeResponse(BaseModel):
    scan_id: str
    filename: str
    language: str
    vulnerabilities: List[VulnerabilityResult]
    total_found: int
    risk_level: SeverityLevel
    gemini_analysis: Optional[str] = None
    timestamp: str


class GenerateFixRequest(BaseModel):
    scan_id: str
    code: str
    language: str
    vulnerabilities: List[Dict[str, Any]]


class FixResponse(BaseModel):
    scan_id: str
    original_code: str
    fixed_code: str
    explanation: str
    changes: List[str]
    confidence: float
    quality_score: float
    recommendation: str


# ─── DASHBOARD SCHEMAS ─────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_scans: int
    critical_issues: int
    fix_success_rate: float
    avg_analysis_time: float
    scans_this_week: int
    change_percent: float


# ─── DOWNLOAD SCHEMAS ──────────────────────────────────────────────

class DownloadRequest(BaseModel):
    scan_id: str
    format: str  # "pdf", "md", "zip", "original"
    include_fixes: bool = True


# ─── GITHUB SCAN SCHEMAS ───────────────────────────────────────────

class GithubScanRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    github_token: Optional[str] = None
    use_gemini: bool = True
    max_files: int = 100
    workspace_id: Optional[str] = None


class RepoScanResponse(BaseModel):
    repo_scan_id: str
    repo_name: str
    branch: str
    total_files_scanned: int
    total_vulnerabilities: int
    overall_risk: SeverityLevel
    files: List[Dict[str, Any]]
    gemini_repo_analysis: Optional[str] = None
    scan_duration_seconds: float
    timestamp: str

# ─── WORKSPACE SCHEMAS ─────────────────────────────────────────────

class WorkspaceRole(str, Enum):
    ADMIN = "Admin"
    SECURITY_ENGINEER = "Security Engineer"
    DEVELOPER = "Developer"

class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = ""

class AddMemberRequest(BaseModel):
    username: str
    role: WorkspaceRole = WorkspaceRole.DEVELOPER

class UpdateRoleRequest(BaseModel):
    role: WorkspaceRole

