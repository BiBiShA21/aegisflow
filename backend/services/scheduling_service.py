"""
AegisFlow - Scheduling Service
Handles automated background tasks using APScheduler.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from backend.database import scheduled_scans_col, repo_scans_col, get_client
from backend.services.alert_service import send_vulnerability_alert
from backend.agents.github_agent import GithubAgent
from bson import ObjectId

scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the APScheduler background task runner."""
    if not scheduler.running:
        scheduler.start()
        print("[SCHEDULER] APScheduler started.")
        # Load existing jobs from DB (if any)
        load_scheduled_jobs()

def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("[SCHEDULER] APScheduler shut down.")

def execute_scheduled_scan(job_id: str, repo_url: str, branch: str, user_id: str, email: str, use_gemini: bool = True):
    """The actual job function that runs the scan and sends alerts."""
    print(f"[SCHEDULER] Running scheduled scan for {repo_url} (Job {job_id})")
    try:
        agent = GithubAgent() # Or fetch user's stored token
        scan_results = agent.scan_repository(
            url=repo_url,
            branch=branch,
            max_files=100,
            use_gemini=use_gemini
        )
        
        scan_results["user_id"] = user_id
        scan_results["is_scheduled"] = True
        
        # Save to database
        result = repo_scans_col().insert_one(scan_results)
        scan_id = str(result.inserted_id)
        
        # If vulnerabilities found, send alert
        if scan_results.get("total_vulnerabilities", 0) > 0:
            link = f"http://127.0.0.1:3000/dashboard.html?scan={scan_id}" # Mock link
            send_vulnerability_alert(
                to_email=email,
                repo_name=scan_results.get("repo_name", repo_url),
                vulnerabilities_found=scan_results["total_vulnerabilities"],
                risk_level=scan_results.get("overall_risk", "UNKNOWN"),
                scan_link=link
            )
            
        print(f"[SCHEDULER] Scan completed for {repo_url}. Vulnerabilities: {scan_results.get('total_vulnerabilities')}")
    except Exception as e:
        print(f"[SCHEDULER ERROR] Failed to run scheduled scan for {repo_url}: {e}")


def load_scheduled_jobs():
    """Loads all scheduled jobs from the DB into the scheduler."""
    jobs = scheduled_scans_col().find({"is_active": True})
    for job in jobs:
        add_job_to_scheduler(job)

def add_job_to_scheduler(job_doc: dict):
    """Adds a single job to the APScheduler."""
    job_id = str(job_doc["_id"])
    
    # Remove if it already exists to avoid duplicates
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    schedule_type = job_doc.get("schedule_type", "daily") # 'daily' or 'weekly'
    
    if schedule_type == "daily":
        trigger = CronTrigger(hour=0, minute=0) # Run at midnight
    elif schedule_type == "weekly":
        trigger = CronTrigger(day_of_week="sun", hour=0, minute=0) # Run Sunday midnight
    else:
        # Fallback to daily
        trigger = CronTrigger(hour=0, minute=0)

    scheduler.add_job(
        func=execute_scheduled_scan,
        trigger=trigger,
        id=job_id,
        args=[
            job_id,
            job_doc["repo_url"],
            job_doc.get("branch", "main"),
            job_doc["user_id"],
            job_doc["alert_email"],
            job_doc.get("use_gemini", True)
        ],
        replace_existing=True
    )
    print(f"[SCHEDULER] Scheduled {schedule_type} scan for {job_doc['repo_url']}")

def schedule_new_scan(user_id: str, repo_url: str, branch: str, schedule_type: str, alert_email: str):
    """Creates a new scheduled scan in DB and adds to scheduler."""
    doc = {
        "user_id": user_id,
        "repo_url": repo_url,
        "branch": branch,
        "schedule_type": schedule_type,
        "alert_email": alert_email,
        "use_gemini": True,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    result = scheduled_scans_col().insert_one(doc)
    doc["_id"] = result.inserted_id
    
    add_job_to_scheduler(doc)
    return str(result.inserted_id)

def cancel_scheduled_scan(job_id: str, user_id: str):
    """Cancels an existing scheduled scan."""
    doc = scheduled_scans_col().find_one({"_id": ObjectId(job_id), "user_id": user_id})
    if doc:
        scheduled_scans_col().update_one({"_id": ObjectId(job_id)}, {"$set": {"is_active": False}})
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        return True
    return False
