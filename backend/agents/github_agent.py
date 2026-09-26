import httpx
import base64
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.agents.detection_agent import detect_vulnerabilities, get_risk_level, LANGUAGE_EXTENSIONS

def parse_github_url(url: str) -> Optional[tuple[str, str]]:
    """Extract owner and repo from a GitHub URL."""
    # Handle formats like https://github.com/owner/repo or github.com/owner/repo
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if match:
        owner = match.group(1)
        repo = match.group(2).replace(".git", "")
        return owner, repo
    return None

def is_supported_file(filename: str) -> bool:
    fname = filename.lower()
    for exts in LANGUAGE_EXTENSIONS.values():
        if any(fname.endswith(ext) for ext in exts):
            return True
    return False

def get_language_from_filename(filename: str) -> str:
    fname = filename.lower()
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if any(fname.endswith(ext) for ext in exts):
            return lang
    return "unknown"

import os

import os
from dotenv import load_dotenv

class GithubAgent:
    def __init__(self, token: Optional[str] = None):
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        
        # Ensure .env is loaded (uvicorn --reload might not watch .env file changes)
        from dotenv import load_dotenv
        load_dotenv()
        
        # Fallback to env var if no token provided
        final_token = token or os.getenv("GITHUB_TOKEN")
        print(f"[DEBUG] GithubAgent initialized. Provided token: '{token}'. final_token resolved to: '{final_token}'")
        
        if final_token:
            self.headers["Authorization"] = f"Bearer {final_token}"
            print("[DEBUG] Authorization header added.")
        else:
            print("[DEBUG] NO Authorization header added!")
            
        self.client = httpx.Client(headers=self.headers, timeout=30.0)

    def scan_repository(self, url: str, branch: str = "main", max_files: int = 100, use_gemini: bool = True) -> Dict[str, Any]:
        start_time = time.time()
        
        parsed = parse_github_url(url)
        if not parsed:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        owner, repo = parsed
        
        # 1. Fetch tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        response = self.client.get(tree_url)
        
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch repository tree: {response.text}")
            
        tree_data = response.json()
        if "tree" not in tree_data:
            raise ValueError("Invalid tree response from GitHub")
            
        # Filter files
        all_files = [item for item in tree_data["tree"] if item["type"] == "blob"]
        supported_files = [f for f in all_files if is_supported_file(f["path"])]
        
        total_skipped = len(all_files) - len(supported_files)
        files_to_scan = supported_files[:max_files]
        if len(supported_files) > max_files:
            total_skipped += (len(supported_files) - max_files)
            
        scan_results = []
        all_vulns = []
        vuln_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        
        # 2. Fetch contents and scan
        for file_item in files_to_scan:
            path = file_item["path"]
            lang = get_language_from_filename(path)
            
            content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
            file_resp = self.client.get(content_url)
            
            if file_resp.status_code != 200:
                continue
                
            file_data = file_resp.json()
            if "content" not in file_data:
                continue
                
            try:
                decoded_content = base64.b64decode(file_data["content"]).decode("utf-8")
            except Exception:
                continue # Skip binary or un-decodable files
                
            vulns = detect_vulnerabilities(decoded_content, lang, path)
            risk = get_risk_level(vulns)
            
            if vulns:
                for v in vulns:
                    sev = v.get("severity", "INFO")
                    if sev in vuln_summary:
                        vuln_summary[sev] += 1
                all_vulns.extend(vulns)
                
            scan_results.append({
                "filename": path,
                "language": lang,
                "vulnerabilities": vulns,
                "total_found": len(vulns),
                "risk_level": risk,
                "original_code": decoded_content # Keep it for fixes/reports if needed
            })
            
        # Calculate overall risk
        overall_risk = get_risk_level(all_vulns)
        
        # Sort files by risk (CRITICAL -> HIGH -> ...)
        risk_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "SAFE": 4}
        scan_results.sort(key=lambda x: risk_order.get(x["risk_level"], 5))
        
        top_vulnerable = [f for f in scan_results if f["total_found"] > 0][:5]
        
        # 3. Gemini repo summary
        gemini_summary = None
        if use_gemini and all_vulns:
            try:
                from backend.agents.fix_agent import analyze_with_gemini
                from backend.agents.fix_agent import genai, GEMINI_AVAILABLE
                if GEMINI_AVAILABLE and genai:
                    model = genai.GenerativeModel("gemini-3.8-flash")
                    repo_context = f"Repository: {owner}/{repo}\nOverall Risk: {overall_risk}\nTotal Vulns: {len(all_vulns)}\n"
                    repo_context += "Top Vulnerable Files:\n"
                    for tf in top_vulnerable:
                        repo_context += f"- {tf['filename']} ({tf['total_found']} vulns)\n"
                    
                    prompt = f"""You are a security expert. Analyze the security posture of this repository based on the scan summary.
Be concise. Provide an executive summary, main attack surfaces, and priority fix recommendations.

{repo_context}
"""
                    response = model.generate_content(prompt)
                    gemini_summary = response.text
            except Exception as e:
                print(f"Gemini repo analysis error: {e}")
                
        duration = time.time() - start_time
        
        return {
            "repo_url": url,
            "repo_name": f"{owner}/{repo}",
            "branch": branch,
            "total_files_scanned": len(scan_results),
            "total_files_skipped": total_skipped,
            "total_vulnerabilities": len(all_vulns),
            "overall_risk": overall_risk,
            "files": scan_results,
            "vulnerability_summary": vuln_summary,
            "top_vulnerable_files": [{"filename": f["filename"], "risk_level": f["risk_level"], "total_found": f["total_found"]} for f in top_vulnerable],
            "gemini_repo_analysis": gemini_summary,
            "scan_duration_seconds": round(duration, 2),
            "created_at": datetime.utcnow().isoformat()
        }

    def update_commit_status(self, owner: str, repo: str, sha: str, state: str, description: str, context: str = "AegisFlow Security Scan"):
        """Update the commit status on GitHub to block or pass PRs based on scan results."""
        if not self.headers.get("Authorization"):
            print("[WARN] No GitHub token provided, cannot update commit status.")
            return None
            
        url = f"https://api.github.com/repos/{owner}/{repo}/statuses/{sha}"
        payload = {
            "state": state,
            "description": description,
            "context": context
        }
        try:
            response = self.client.post(url, json=payload)
            if response.status_code != 201:
                print(f"[ERROR] Failed to update commit status: {response.text}")
            else:
                print(f"[INFO] Successfully updated commit status for {sha} to {state}.")
            return response
        except Exception as e:
            print(f"[ERROR] Exception while updating commit status: {e}")
            return None
