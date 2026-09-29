"""
AegisFlow - Main FastAPI Application
Phase 1 + Phase 2: Complete backend
"""
import os
import io
import json
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

# ── Internal imports ──────────────────────────────────────────────
from backend.database import init_db, scans_col, vulnerabilities_col, fixes_col, users_col, audit_logs_col, repo_scans_col
from backend.models.schemas import RegisterRequest, LoginRequest, AnalyzeRequest, GenerateFixRequest, UpdateProfileRequest, GithubScanRequest, ScheduleScanRequest, CreatePRRequest, AutonomousPipelineRequest
from backend.services.auth_service import register_user, login_user, decode_token, get_user_by_id, update_user_profile
from backend.agents.detection_agent import detect_vulnerabilities, get_risk_level, detect_language
from backend.agents.fix_agent import generate_fix, analyze_with_gemini, get_recommendation
from backend.services.download_service import generate_pdf_report, generate_markdown_report, generate_zip_download, get_file_extension, generate_repo_pdf_report
from backend.agents.github_agent import GithubAgent
from backend.services.scheduling_service import start_scheduler, shutdown_scheduler, schedule_new_scan, cancel_scheduled_scan
from backend.database import scheduled_scans_col

# ── App Setup ─────────────────────────────────────────────────────
app = FastAPI(
    title="AegisFlow API",
    description="AI-Powered Security Vulnerability Detection & Remediation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


# ── Auth Helper ───────────────────────────────────────────────────
def get_current_user(request: Request) -> Optional[dict]:
    auth_header = request.headers.get("Authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if not token:
        token = request.query_params.get("token")
        
    if not token:
        return None
        
    payload = decode_token(token)
    if not payload:
        return None
    return get_user_by_id(payload.get("user_id", ""))


def require_user(user: dict = Depends(get_current_user)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _str_id(doc: dict) -> dict:
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── Startup ───────────────────────────────────────────────────────
@app.middleware("http")
async def error_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"[ERROR] Error: {request.method} {request.url.path} — {str(e)}")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.on_event("startup")
async def startup():
    init_db()
    start_scheduler()
    print("\n" + "="*55)
    print("   AegisFlow Backend v2.0 — STARTED")
    print("="*55)
    print("[API]    http://127.0.0.1:8000")
    print("[Docs]   http://127.0.0.1:8000/docs")
    print("[Health] http://127.0.0.1:8000/api/health")
    print("[OK]     CORS Enabled for http://127.0.0.1:3000")
    print("="*55 + "\n")

@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()


# ── Health ────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "phases": ["Phase 1: MongoDB OK", "Phase 2: Gemini AI OK"]
    }


@app.get("/")
async def root():
    return {"message": "AegisFlow API v2.0", "docs": "/docs"}


# ═══════════════════════════════════════════════════════════════════
# WORKSPACE & RBAC ROUTES (Phase 8)
# ═══════════════════════════════════════════════════════════════════

from backend.models.schemas import CreateWorkspaceRequest, AddMemberRequest, UpdateRoleRequest
from backend.services.workspace_service import (
    create_workspace, get_workspaces_for_user, get_workspace_by_id,
    add_member_to_workspace, remove_member_from_workspace,
    update_member_role, get_workspace_members
)

@app.post("/api/workspaces")
async def api_create_workspace(req: CreateWorkspaceRequest, user: dict = Depends(require_user)):
    try:
        workspace = create_workspace(req.name, req.description, user["id"])
        return {"success": True, "workspace": workspace}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workspaces")
async def api_get_workspaces(user: dict = Depends(require_user)):
    try:
        workspaces = get_workspaces_for_user(user["id"])
        return {"success": True, "workspaces": workspaces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workspaces/{workspace_id}")
async def api_get_workspace(workspace_id: str, user: dict = Depends(require_user)):
    try:
        workspace = get_workspace_by_id(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        # Ensure user is a member
        is_member = any(m["user_id"] == user["id"] for m in workspace.get("members", []))
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a member of this workspace")
            
        members = get_workspace_members(workspace_id)
        workspace["members_detail"] = members
        return {"success": True, "workspace": workspace}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workspaces/{workspace_id}/members")
async def api_add_member(workspace_id: str, req: AddMemberRequest, user: dict = Depends(require_user)):
    try:
        add_member_to_workspace(workspace_id, req.username, req.role.value, user["id"])
        return {"success": True, "message": "Member added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/workspaces/{workspace_id}/members/{target_user_id}")
async def api_update_member_role(workspace_id: str, target_user_id: str, req: UpdateRoleRequest, user: dict = Depends(require_user)):
    try:
        update_member_role(workspace_id, target_user_id, req.role.value, user["id"])
        return {"success": True, "message": "Role updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/workspaces/{workspace_id}/members/{target_user_id}")
async def api_remove_member(workspace_id: str, target_user_id: str, user: dict = Depends(require_user)):
    try:
        remove_member_from_workspace(workspace_id, target_user_id, user["id"])
        return {"success": True, "message": "Member removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
async def register(req: RegisterRequest):
    try:
        print(f"[REGISTER] Registration attempt: {req.username}")
        user = register_user(req.model_dump())
        print(f"[OK] User registered: {req.username}")
        return {"success": True, "user": user, "message": "Account created! Please login."}
    except ValueError as e:
        print(f"[WARN] Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/auth/login")
async def login(req: LoginRequest):
    try:
        print(f"[LOGIN] Login attempt: {req.username}")
        result = login_user(req.username, req.password, req.rememberMe)
        print(f"[OK] Login successful: {req.username}")
        return result
    except ValueError as e:
        print(f"[ERROR] Login failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/api/auth/me")
async def get_me(user: dict = Depends(require_user)):
    # Add scan stats
    scan_count = scans_col().count_documents({"user_id": user["id"]})
    critical_count = scans_col().count_documents({
        "user_id": user["id"],
        "risk_level": "CRITICAL"
    })
    user["total_scans"] = scan_count
    user["critical_scans"] = critical_count
    return user


@app.put("/api/auth/profile")
async def update_profile(req: UpdateProfileRequest, user: dict = Depends(require_user)):
    try:
        updated = update_user_profile(user["id"], req.model_dump(exclude_none=True))
        return {"success": True, "user": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# ANALYSIS ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/analyze")
async def analyze_code(req: AnalyzeRequest, user: dict = Depends(require_user)):
    """Analyze code for vulnerabilities — Phase 2 Detection Agent"""
    try:
        # Detect language if auto
        lang = req.language.lower()
        if lang == "auto":
            lang = detect_language(req.filename or "", req.code)

        # Phase 2: Run detection
        vulns = detect_vulnerabilities(req.code, lang, req.filename or "")
        risk = get_risk_level(vulns)

        # Phase 2: Gemini analysis
        gemini_analysis = None
        if req.use_gemini:
            gemini_analysis = analyze_with_gemini(req.code, lang)

        # Phase 1: Save to MongoDB
        scan_doc = {
            "user_id": user["id"],
            "filename": req.filename or "unknown",
            "language": lang,
            "original_code": req.code,
            "vulnerabilities": vulns,
            "total_found": len(vulns),
            "risk_level": risk,
            "gemini_analysis": gemini_analysis,
            "fixed_code": None,
            "fix_applied": False,
            "created_at": datetime.utcnow(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if req.workspace_id:
            workspace = get_workspace_by_id(req.workspace_id)
            if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
            scan_doc["workspace_id"] = req.workspace_id

        result = scans_col().insert_one(scan_doc)
        scan_id = str(result.inserted_id)

        # Update user scan count
        users_col().update_one(
            {"_id": ObjectId(user["id"])},
            {"$inc": {"total_scans": 1}}
        )

        return {
            "scan_id": scan_id,
            "filename": req.filename or "unknown",
            "language": lang,
            "vulnerabilities": vulns,
            "total_found": len(vulns),
            "risk_level": risk,
            "gemini_analysis": gemini_analysis,
            "timestamp": scan_doc["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...),
    use_gemini: bool = Form(True),
    user: dict = Depends(require_user)
):
    """Upload and analyze a single file"""
    try:
        content = await file.read()
        code = content.decode("utf-8", errors="replace")
        lang = detect_language(file.filename or "", code)

        vulns = detect_vulnerabilities(code, lang, file.filename or "")
        risk = get_risk_level(vulns)
        gemini_analysis = analyze_with_gemini(code, lang) if use_gemini else None

        scan_doc = {
            "user_id": user["id"],
            "filename": file.filename,
            "language": lang,
            "original_code": code,
            "vulnerabilities": vulns,
            "total_found": len(vulns),
            "risk_level": risk,
            "gemini_analysis": gemini_analysis,
            "fixed_code": None,
            "fix_applied": False,
            "created_at": datetime.utcnow(),
            "timestamp": datetime.utcnow().isoformat()
        }
        result = scans_col().insert_one(scan_doc)
        users_col().update_one({"_id": ObjectId(user["id"])}, {"$inc": {"total_scans": 1}})

        return {
            "scan_id": str(result.inserted_id),
            "filename": file.filename,
            "language": lang,
            "vulnerabilities": vulns,
            "total_found": len(vulns),
            "risk_level": risk,
            "gemini_analysis": gemini_analysis,
            "timestamp": scan_doc["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload analysis failed: {str(e)}")


@app.post("/api/analyze/folder")
async def analyze_folder(
    files: List[UploadFile] = File(...),
    user: dict = Depends(require_user)
):
    """Upload and analyze entire folder"""
    results = []
    all_vulns = 0
    max_risk = "SAFE"
    risk_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "SAFE": 0}

    for file in files:
        try:
            content = await file.read()
            code = content.decode("utf-8", errors="replace")
            lang = detect_language(file.filename or "", code)
            vulns = detect_vulnerabilities(code, lang, file.filename or "")
            risk = get_risk_level(vulns)
            all_vulns += len(vulns)

            if risk_order.get(risk, 0) > risk_order.get(max_risk, 0):
                max_risk = risk

            scan_doc = {
                "user_id": user["id"],
                "filename": file.filename,
                "language": lang,
                "original_code": code,
                "vulnerabilities": vulns,
                "total_found": len(vulns),
                "risk_level": risk,
                "folder_scan": True,
                "fixed_code": None,
                "created_at": datetime.utcnow(),
                "timestamp": datetime.utcnow().isoformat()
            }
            result = scans_col().insert_one(scan_doc)
            results.append({
                "scan_id": str(result.inserted_id),
                "filename": file.filename,
                "language": lang,
                "total_found": len(vulns),
                "risk_level": risk,
                "vulnerabilities": vulns
            })
        except Exception as e:
            results.append({"filename": file.filename, "error": str(e)})

    users_col().update_one({"_id": ObjectId(user["id"])}, {"$inc": {"total_scans": len(results)}})

    return {
        "total_files": len(files),
        "total_vulnerabilities": all_vulns,
        "overall_risk": max_risk,
        "files": results
    }


@app.post("/api/fix")
async def generate_fix_endpoint(req: GenerateFixRequest, user: dict = Depends(require_user)):
    """Generate AI fix for vulnerabilities"""
    try:
        fix_result = generate_fix(req.code, req.vulnerabilities, req.language)
        recommendation = get_recommendation(fix_result["confidence"])

        # Save fix to MongoDB
        fix_doc = {
            "scan_id": req.scan_id,
            "user_id": user["id"],
            "original_code": req.code,
            "fixed_code": fix_result["fixed_code"],
            "explanation": fix_result["explanation"],
            "changes": fix_result["changes"],
            "confidence": fix_result["confidence"],
            "quality_score": fix_result["quality_score"],
            "recommendation": recommendation,
            "source": fix_result.get("source", "unknown"),
            "created_at": datetime.utcnow()
        }
        fixes_col().insert_one(fix_doc)

        # Update scan with fix
        if req.scan_id:
            try:
                scans_col().update_one(
                    {"_id": ObjectId(req.scan_id)},
                    {"$set": {"fixed_code": fix_result["fixed_code"], "fix_applied": True}}
                )
            except Exception:
                pass

        return {
            "scan_id": req.scan_id,
            "original_code": req.code,
            "fixed_code": fix_result["fixed_code"],
            "explanation": fix_result["explanation"],
            "changes": fix_result["changes"],
            "confidence": fix_result["confidence"],
            "quality_score": fix_result["quality_score"],
            "recommendation": recommendation,
            "source": fix_result.get("source", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fix generation failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════
# SCAN HISTORY ROUTES (Phase 1)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/scans")
async def get_scans(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    status: str = "",
    workspace_id: Optional[str] = None,
    user: dict = Depends(require_user)
):
    """Get paginated scan history for user or workspace"""
    if workspace_id:
        workspace = get_workspace_by_id(workspace_id)
        if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        query = {"workspace_id": workspace_id}
    else:
        query = {"user_id": user["id"], "workspace_id": {"$exists": False}}
        
    if search:
        query["filename"] = {"$regex": search, "$options": "i"}
    if status == "resolved":
        query["fix_applied"] = True
    elif status == "pending":
        query["fix_applied"] = {"$ne": True}

    total = scans_col().count_documents(query)
    skip = (page - 1) * limit
    scans = list(scans_col().find(query, {"original_code": 0, "fixed_code": 0})
                 .sort("created_at", -1).skip(skip).limit(limit))

    for s in scans:
        s["_id"] = str(s["_id"])

    return {"scans": scans, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str, user: dict = Depends(require_user)):
    """Get full scan details"""
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        # RBAC Check
        if scan.get("workspace_id"):
            workspace = get_workspace_by_id(scan["workspace_id"])
            if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
                raise HTTPException(status_code=403, detail="Access denied to this scan")
        elif scan.get("user_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this scan")
            
        scan["_id"] = str(scan["_id"])
        return scan
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")


@app.delete("/api/scans/{scan_id}")
async def delete_scan(scan_id: str, user: dict = Depends(require_user)):
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        if scan.get("workspace_id"):
            workspace = get_workspace_by_id(scan["workspace_id"])
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            # Only Admin or Security Engineer can delete workspace scans, or the user who created it
            user_role = next((m["role"] for m in workspace.get("members", []) if m["user_id"] == user["id"]), None)
            if not user_role or (user_role == "Developer" and scan.get("user_id") != user["id"]):
                raise HTTPException(status_code=403, detail="Not authorized to delete this scan")
        elif scan.get("user_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this scan")
            
        scans_col().delete_one({"_id": ObjectId(scan_id)})
        return {"success": True, "message": "Scan deleted"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Delete failed")


# ═══════════════════════════════════════════════════════════════════
# DASHBOARD & ANALYTICS ROUTES (Phase 1)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/dashboard")
async def get_dashboard(user: dict = Depends(require_user)):
    """Get dashboard stats from MongoDB"""
    uid = user["id"]
    col = scans_col()

    total = col.count_documents({"user_id": uid})
    critical = col.count_documents({"user_id": uid, "risk_level": "CRITICAL"})
    fixed = col.count_documents({"user_id": uid, "fix_applied": True})
    fix_rate = round((fixed / total * 100) if total > 0 else 0, 1)

    # Recent scans
    recent = list(col.find({"user_id": uid}, {"original_code": 0, "fixed_code": 0})
                  .sort("created_at", -1).limit(5))
    for s in recent:
        s["_id"] = str(s["_id"])

    # Vulnerability breakdown
    pipeline = [
        {"$match": {"user_id": uid}},
        {"$unwind": "$vulnerabilities"},
        {"$group": {"_id": "$vulnerabilities.severity", "count": {"$sum": 1}}}
    ]
    breakdown = {r["_id"]: r["count"] for r in col.aggregate(pipeline)}

    # Top vulnerability types
    type_pipeline = [
        {"$match": {"user_id": uid}},
        {"$unwind": "$vulnerabilities"},
        {"$group": {"_id": "$vulnerabilities.type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_types = [{"type": r["_id"], "count": r["count"]} for r in col.aggregate(type_pipeline)]

    return {
        "total_scans": total,
        "critical_issues": critical,
        "fix_success_rate": fix_rate,
        "avg_analysis_time": 2.3,
        "scans_this_week": col.count_documents({
            "user_id": uid,
            "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0)}
        }),
        "recent_scans": recent,
        "vulnerability_breakdown": breakdown,
        "top_vulnerability_types": top_types,
        "total_vulnerabilities": sum(breakdown.values())
    }


# ═══════════════════════════════════════════════════════════════════
# GITHUB SCAN ROUTES (Phase 3)
# ═══════════════════════════════════════════════════════════════════

@app.post("/api/analyze/github")
def analyze_github(req: GithubScanRequest, user: dict = Depends(require_user)):
    """Analyze an entire GitHub repository"""
    try:
        agent = GithubAgent(token=req.github_token)
        scan_results = agent.scan_repository(
            url=req.repo_url,
            branch=req.branch,
            max_files=req.max_files,
            use_gemini=req.use_gemini
        )
        
        # Save to database
        scan_results["user_id"] = user["id"]
        
        if req.workspace_id:
            workspace = get_workspace_by_id(req.workspace_id)
            if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
                raise HTTPException(status_code=403, detail="Access denied to workspace")
            scan_results["workspace_id"] = req.workspace_id

        result = repo_scans_col().insert_one(scan_results)
        scan_id = str(result.inserted_id)
        scan_results["repo_scan_id"] = scan_id
        
        # Remove ObjectId so FastAPI can serialize it
        if "_id" in scan_results:
            scan_results["_id"] = str(scan_results["_id"])
        
        # Remove original_code from response to keep it light
        for f in scan_results.get("files", []):
            f.pop("original_code", None)
            
        return scan_results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GitHub scan failed: {str(e)}")

@app.post("/api/analyze/github/schedule")
async def schedule_github_scan(req: ScheduleScanRequest, user: dict = Depends(require_user)):
    """Schedule automated daily/weekly scans for a GitHub repository"""
    try:
        job_id = schedule_new_scan(
            user_id=user["id"],
            repo_url=req.repo_url,
            branch=req.branch,
            schedule_type=req.schedule_type,
            alert_email=req.alert_email
        )
        return {"success": True, "job_id": job_id, "message": f"Successfully scheduled {req.schedule_type} scan for {req.repo_url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analyze/github/schedule/{job_id}")
async def cancel_github_scan(job_id: str, user: dict = Depends(require_user)):
    """Cancel a scheduled GitHub scan"""
    try:
        success = cancel_scheduled_scan(job_id, user["id"])
        if success:
            return {"success": True, "message": "Scheduled scan cancelled"}
        else:
            raise HTTPException(status_code=404, detail="Scheduled scan not found or access denied")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/github/schedule")
async def list_scheduled_scans(user: dict = Depends(require_user)):
    """List all scheduled scans for the current user"""
    try:
        jobs = list(scheduled_scans_col().find({"user_id": user["id"], "is_active": True}))
        for job in jobs:
            job["_id"] = str(job["_id"])
        return {"success": True, "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from backend.services.pr_service import create_remediation_pr

@app.post("/api/analyze/github/pr")
async def create_github_pr(req: CreatePRRequest, user: dict = Depends(require_user)):
    """Autonomous Stage 4: Create a GitHub PR with the fixed code."""
    try:
        pr_url = create_remediation_pr(
            github_token=req.github_token,
            repo_name=req.repo_name,
            file_path=req.file_path,
            fixed_code=req.fixed_code,
            vulnerability_details=req.vulnerability_details
        )
        if pr_url:
            return {"success": True, "pr_url": pr_url}
        else:
            raise HTTPException(status_code=400, detail="Failed to create PR. Ensure GITHUB_PAT is set.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from backend.agents.orchestrator import run_autonomous_pipeline

@app.post("/api/analyze/autonomous")
async def run_pipeline(req: AutonomousPipelineRequest, user: dict = Depends(require_user)):
    """Trigger the full LangGraph-based multi-agent self-healing pipeline."""
    try:
        payload = req.model_dump()
        if not payload.get("github_token"):
             payload["github_token"] = os.getenv("GITHUB_PAT")
             
        final_state = run_autonomous_pipeline(payload)
        return {
            "success": True,
            "vulnerabilities": final_state.get("vulnerabilities", []),
            "fixed_code": final_state.get("fixed_code"),
            "confidence": final_state.get("confidence"),
            "pr_url": final_state.get("pr_url"),
            "messages": final_state.get("messages", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/github-scans")
async def clear_github_scans(user: dict = Depends(require_user)):
    try:
        repo_scans_col().delete_many({})
        return {"success": True, "message": "All logs cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/github-scans")
async def get_github_scans(
    page: int = 1,
    limit: int = 10,
    search: str = "",
    workspace_id: Optional[str] = None,
    user: dict = Depends(require_user)
):
    """Get paginated github scan history for user or workspace"""
    if workspace_id:
        workspace = get_workspace_by_id(workspace_id)
        if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        query = {"workspace_id": workspace_id}
    else:
        query = {"user_id": user["id"], "workspace_id": {"$exists": False}}
        
    if search:
        query["repo_name"] = {"$regex": search, "$options": "i"}

    total = repo_scans_col().count_documents(query)
    skip = (page - 1) * limit
    scans = list(repo_scans_col().find(query, {"files": 0, "top_vulnerable_files": 0, "gemini_repo_analysis": 0})
                 .sort("created_at", -1).skip(skip).limit(limit))

    for s in scans:
        s["_id"] = str(s["_id"])
        s["repo_scan_id"] = s["_id"]

    return {"scans": scans, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@app.get("/api/github-scans/{scan_id}")
async def get_github_scan(scan_id: str, user: dict = Depends(require_user)):
    """Get full github scan details"""
    try:
        scan = repo_scans_col().find_one({"_id": ObjectId(scan_id)})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        # RBAC Check
        if scan.get("workspace_id"):
            workspace = get_workspace_by_id(scan["workspace_id"])
            if not workspace or not any(m["user_id"] == user["id"] for m in workspace.get("members", [])):
                raise HTTPException(status_code=403, detail="Access denied to this scan")
        elif scan.get("user_id") != user["id"]:
            raise HTTPException(status_code=403, detail="Access denied to this scan")
            
        scan["_id"] = str(scan["_id"])
        scan["repo_scan_id"] = scan["_id"]
        # Do not send full original code to frontend
        for f in scan.get("files", []):
            f.pop("original_code", None)
        return scan
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")


@app.get("/api/download/github/{scan_id}/pdf")
async def download_github_pdf(scan_id: str, user: dict = Depends(require_user)):
    """Download Github scan report as PDF"""
    try:
        scan = repo_scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        pdf = generate_repo_pdf_report(scan)
        repo_name_safe = scan.get("repo_name", "repo").replace("/", "_")
        fname = f"aegisflow_repo_report_{repo_name_safe}.pdf"
        return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/github/{scan_id}/fix")
async def generate_github_fixes(scan_id: str, user: dict = Depends(require_user)):
    """Generate fixes for all vulnerable files in a GitHub scan"""
    try:
        col = repo_scans_col()
        scan = col.find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        fixed_count = 0
        from backend.agents.fix_agent import generate_fix
        
        updated_files = []
        for file in scan.get("files", []):
            if file.get("total_found", 0) > 0 and file.get("original_code"):
                result = generate_fix(file["original_code"], file.get("vulnerabilities", []), file.get("language", "python"))
                file["fixed_code"] = result.get("fixed_code", "")
                if file["fixed_code"]:
                    fixed_count += file.get("total_found", 0)
            updated_files.append(file)
            
        # Update db
        col.update_one({"_id": ObjectId(scan_id)}, {"$set": {"files": updated_files}})
        return {"success": True, "fixed_count": fixed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/github/{scan_id}/markdown")
async def download_github_markdown(scan_id: str, user: dict = Depends(require_user)):
    """Download Github scan report as Markdown"""
    try:
        scan = repo_scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        from backend.services.download_service import generate_repo_markdown_report
        md = generate_repo_markdown_report(scan)
        repo_name_safe = scan.get("repo_name", "repo").replace("/", "_")
        fname = f"aegisflow_repo_report_{repo_name_safe}.md"
        return StreamingResponse(io.BytesIO(md), media_type="text/markdown",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/github/{scan_id}/zip")
async def download_github_zip(scan_id: str, user: dict = Depends(require_user)):
    """Download Github fixed code and reports as ZIP"""
    try:
        scan = repo_scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
            
        from backend.services.download_service import generate_repo_zip_download
        zip_bytes = generate_repo_zip_download(scan)
        repo_name_safe = scan.get("repo_name", "repo").replace("/", "_")
        fname = f"aegisflow_repo_fix_{repo_name_safe}.zip"
        return StreamingResponse(io.BytesIO(zip_bytes), media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# WEBHOOKS / CI-CD INTEGRATION (Phase 6)
# ═══════════════════════════════════════════════════════════════════

class RegisterWebhookRequest(BaseModel):
    repo_url: str
    github_token: str
    webhook_url: str

class OAuthSetupRequest(BaseModel):
    code: str
    repo_url: str

@app.post("/api/github/oauth-setup")
def github_oauth_setup(req: OAuthSetupRequest, user: dict = Depends(require_user)):
    try:
        import httpx
        import os
        from backend.agents.github_agent import parse_github_url
        
        # 1. Exchange code for access token
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        
        with httpx.Client() as client:
            resp = client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": req.code
                },
                headers={"Accept": "application/json"}
            )
            data = resp.json()
            
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to exchange GitHub OAuth code.")
            
        # 2. Setup Webhook
        agent = GithubAgent(token=access_token)
        parsed = parse_github_url(req.repo_url)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
            
        owner, repo_name = parsed
        webhook_url = os.getenv("AEGISFLOW_WEBHOOK_URL")
        if not webhook_url:
            raise HTTPException(status_code=500, detail="AEGISFLOW_WEBHOOK_URL not set in server.")
            
        result = agent.create_webhook(owner, repo_name, webhook_url)
        return {"success": True, "message": "GitHub Webhook successfully connected via OAuth!"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/register")
def register_webhook(req: RegisterWebhookRequest, user: dict = Depends(require_user)):
    try:
        agent = GithubAgent(token=req.github_token)
        from backend.agents.github_agent import parse_github_url
        parsed = parse_github_url(req.repo_url)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")
            
        owner, repo_name = parsed
        result = agent.create_webhook(owner, repo_name, req.webhook_url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook endpoint for GitHub Actions/Webhooks to trigger automated scans on push/PR"""
    try:
        payload = await request.json()
        
        # Check if it's a push or pull_request event
        if "repository" in payload:
            repo_url = payload["repository"]["html_url"]
            # Extract SHA and Branch for status check
            sha = None
            branch = "main"
            
            if "pull_request" in payload:
                sha = payload.get("pull_request", {}).get("head", {}).get("sha")
                branch = payload.get("pull_request", {}).get("head", {}).get("ref", "main")
            else:
                branch = payload.get("ref", "").split("/")[-1] if "ref" in payload else "main"
                if "after" in payload:
                    sha = payload.get("after")
                elif "head_commit" in payload and payload["head_commit"]:
                    sha = payload["head_commit"].get("id")

            def run_webhook_scan(url, br, commit_sha):
                try:
                    print(f"🔄 [WEBHOOK] Starting automated scan for {url} on branch {br}")
                    agent = GithubAgent()
                    
                    from backend.agents.github_agent import parse_github_url
                    parsed = parse_github_url(url)
                    owner, repo_name = parsed if parsed else (None, None)
                    
                    if commit_sha and owner and repo_name:
                        agent.update_commit_status(owner, repo_name, commit_sha, "pending", "AegisFlow scan is running...")

                    # Run a fast scan without Gemini to avoid rate limits on every commit
                    scan_results = agent.scan_repository(url=url, branch=br, max_files=100, use_gemini=False)
                    
                    # Associate with a system bot user for webhooks
                    scan_results["user_id"] = "github_ci_cd_bot"
                    scan_results["webhook_trigger"] = True
                    
                    result = repo_scans_col().insert_one(scan_results)
                    print(f"✅ [WEBHOOK] Scan finished for {url}. Overall Risk: {scan_results.get('overall_risk')}")
                    
                    if commit_sha and owner and repo_name:
                        risk = scan_results.get('overall_risk', 'SAFE')
                        if risk == "CRITICAL" or risk == "HIGH":
                            agent.update_commit_status(owner, repo_name, commit_sha, "failure", "Vulnerabilities detected! AegisFlow is generating a fix PR...")
                            
                            # TRIGGER AUTONOMOUS PIPELINE FOR EACH VULNERABLE FILE
                            from backend.agents.orchestrator import run_autonomous_pipeline
                            
                            # Group vulnerabilities by file
                            vulns_by_file = {}
                            for file_data in scan_results.get("files", []):
                                fpath = file_data.get("filename")
                                if fpath and file_data.get("vulnerabilities"):
                                    vulns_by_file[fpath] = {
                                        "code": file_data.get("original_code", ""),
                                        "language": file_data.get("language", ""),
                                        "vulns": file_data.get("vulnerabilities")
                                    }
                                    
                            # Limit to top 3 vulnerable files to prevent rate limits and excessive PRs
                            files_to_fix = list(vulns_by_file.items())[:3]
                            for fpath, data in files_to_fix:
                                payload = {
                                    "code": data["code"],
                                    "language": data["language"],
                                    "repo_name": f"{owner}/{repo_name}",
                                    "file_path": fpath,
                                    "github_token": os.getenv("GITHUB_PAT"),
                                    "scan_id": str(result.inserted_id)
                                }
                                print(f"🚀 [WEBHOOK] Triggering Self-Healing Pipeline for {fpath}")
                                final_state = run_autonomous_pipeline(payload)
                                pr_url = final_state.get("pr_url")
                                if pr_url:
                                    repo_scans_col().update_one(
                                        {"_id": result.inserted_id},
                                        {"$set": {"pr_url": pr_url, "overall_risk": "REMEDIATED"}}
                                    )
                                    agent.update_commit_status(owner, repo_name, commit_sha, "success", "AegisFlow fix PR created successfully!")
                                
                        else:
                            agent.update_commit_status(owner, repo_name, commit_sha, "success", f"Scan complete. Risk: {risk}")
                            
                except Exception as e:
                    print(f"❌ [WEBHOOK ERROR] Automated scan failed: {str(e)}")
                    try:
                        from backend.agents.github_agent import parse_github_url
                        parsed = parse_github_url(url)
                        owner, repo_name = parsed if parsed else (None, None)
                        if commit_sha and owner and repo_name:
                            agent = GithubAgent()
                            agent.update_commit_status(owner, repo_name, commit_sha, "error", "Scan failed due to an error.")
                    except:
                        pass

            # Queue the scan so we return 200 OK to GitHub immediately (avoiding timeouts)
            background_tasks.add_task(run_webhook_scan, repo_url, branch, sha)
            
            return {"success": True, "message": "Automated security scan queued", "repo": repo_url}
            
        return {"success": False, "message": "Ignored: Invalid GitHub webhook payload"}
    except Exception as e:
        print(f"❌ [WEBHOOK ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# DOWNLOAD ROUTES (Phase 2)
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/download/{scan_id}/pdf")
async def download_pdf(scan_id: str, user: dict = Depends(require_user)):
    """Download scan report as PDF"""
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan["_id"] = str(scan["_id"])
        scan["scan_id"] = scan["_id"]
        pdf = generate_pdf_report(scan)
        fname = f"aegisflow_report_{scan.get('filename', 'scan').replace('.', '_')}.pdf"
        return StreamingResponse(io.BytesIO(pdf), media_type="application/pdf",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{scan_id}/markdown")
async def download_markdown(scan_id: str, user: dict = Depends(require_user)):
    """Download scan report as Markdown"""
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan["_id"] = str(scan["_id"])
        scan["scan_id"] = scan["_id"]
        md = generate_markdown_report(scan)
        fname = f"aegisflow_report_{scan.get('filename', 'scan').replace('.', '_')}.md"
        return StreamingResponse(io.BytesIO(md), media_type="text/markdown",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{scan_id}/code")
async def download_fixed_code(scan_id: str, user: dict = Depends(require_user)):
    """Download fixed code file in original language"""
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        code = scan.get("fixed_code") or scan.get("original_code", "")
        lang = scan.get("language", "python")
        ext = get_file_extension(lang)
        base = scan.get("filename", "fixed_code")
        if "." in base:
            fname = base
        else:
            fname = f"fixed_{base}{ext}"

        return StreamingResponse(io.BytesIO(code.encode()),
                                 media_type="text/plain",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download/{scan_id}/zip")
async def download_zip(scan_id: str, user: dict = Depends(require_user)):
    """Download ZIP with fixed code + reports"""
    try:
        scan = scans_col().find_one({"_id": ObjectId(scan_id), "user_id": user["id"]})
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        scan["_id"] = str(scan["_id"])
        scan["scan_id"] = scan["_id"]

        files = [{
            "filename": scan.get("filename", "code"),
            "original_code": scan.get("original_code", ""),
            "fixed_code": scan.get("fixed_code", "")
        }]
        zip_data = generate_zip_download(scan, files)
        fname = f"aegisflow_{scan.get('filename', 'scan').replace('.', '_')}.zip"
        return StreamingResponse(io.BytesIO(zip_data), media_type="application/zip",
                                 headers={"Content-Disposition": f"attachment; filename={fname}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════
# AUDIT LOGS
# ═══════════════════════════════════════════════════════════════════

@app.get("/api/audit-logs")
async def get_audit_logs(user: dict = Depends(require_user)):
    logs = list(audit_logs_col().find({"user_id": user["id"]}).sort("timestamp", -1).limit(50))
    for l in logs:
        l["_id"] = str(l["_id"])
    return {"logs": logs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
