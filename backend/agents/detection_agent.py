"""
AegisFlow - Detection Agent
Phase 3: 15-type vulnerability detection across 10 languages
"""
import re
import os
import uuid
import json
import docker
from typing import List, Dict, Any

VULNERABILITY_RULES = {
    "Hardcoded Credentials": {
        "patterns": [
            r'(api_key|apikey|api-key)\s*=\s*["\'][^"\']{8,}["\']',
            r'(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',
            r'(secret|secret_key)\s*=\s*["\'][^"\']{6,}["\']',
            r'(token|auth_token)\s*=\s*["\'][^"\']{8,}["\']',
            r'(access_key|private_key)\s*=\s*["\'][^"\']{8,}["\']',
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-798",
        "owasp": "A07:2021",
        "description": "Hardcoded credential found in source code. This exposes sensitive data.",
    },
    "SQL Injection": {
        "patterns": [
            r'(SELECT|INSERT|UPDATE|DELETE).*\+.*\b(user|input|request|param)\b',
            r'f["\'].*SELECT.*{.*}',
            r'["\']\s*\+\s*\w+\s*\+\s*["\'].*WHERE',
            r'execute\s*\(\s*["\'].*%s.*["\'],',
            r'format\s*\(.*SELECT|DELETE|UPDATE|INSERT',
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-89",
        "owasp": "A03:2021",
        "description": "SQL query constructed with user input. Use parameterized queries.",
    },
    "Code Execution": {
        "patterns": [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'subprocess\.call\s*\(.*shell\s*=\s*True',
            r'os\.system\s*\(',
            r'Runtime\.getRuntime\(\)\.exec\(',
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-94",
        "owasp": "A03:2021",
        "description": "Dynamic code execution detected. This allows arbitrary code execution.",
    },
    "XSS Vulnerability": {
        "patterns": [
            r'innerHTML\s*=',
            r'document\.write\s*\(',
            r'outerHTML\s*=',
            r'dangerouslySetInnerHTML',
            r'insertAdjacentHTML\s*\(',
        ],
        "severity": "HIGH",
        "cwe": "CWE-79",
        "owasp": "A03:2021",
        "description": "Unsanitized user input written to DOM. Use textContent or DOMPurify.",
    },
    "Insecure Deserialization": {
        "patterns": [
            r'pickle\.loads?\s*\(',
            r'pickle\.load\s*\(',
            r'ObjectInputStream\s*\(',
            r'yaml\.load\s*\([^,)]*\)',
            r'Marshal\.load\s*\(',
            r'JSON\.parse\s*\(.*eval',
        ],
        "severity": "CRITICAL",
        "cwe": "CWE-502",
        "owasp": "A08:2021",
        "description": "Insecure deserialization of untrusted data. Use safe alternatives.",
    },
    "Weak Cryptography": {
        "patterns": [
            r'\bmd5\b',
            r'hashlib\.md5\s*\(',
            r'hashlib\.sha1\s*\(',
            r'DES\.',
            r'RC4\.',
            r'MessageDigest\.getInstance\s*\(\s*["\']MD5["\']',
            r'MessageDigest\.getInstance\s*\(\s*["\']SHA-1["\']',
        ],
        "severity": "HIGH",
        "cwe": "CWE-327",
        "owasp": "A02:2021",
        "description": "Weak cryptographic algorithm detected. Use SHA-256 or stronger.",
    },
    "Hardcoded Database URL": {
        "patterns": [
            r'mongodb://[^"\']*:[^"\']*@',
            r'mysql://[^"\']{5,}',
            r'postgresql://[^"\']{5,}',
            r'(DB_URL|DATABASE_URL|MONGO_URI)\s*=\s*["\'][^"\']{10,}["\']',
            r'sqlite:///[^"\']{3,}',
        ],
        "severity": "HIGH",
        "cwe": "CWE-259",
        "owasp": "A07:2021",
        "description": "Database URL hardcoded. Use environment variables instead.",
    },
    "Missing Input Validation": {
        "patterns": [
            r'request\.(args|form|json|data)\[',
            r'request\.GET\[',
            r'request\.POST\[',
            r'\$_GET\[',
            r'\$_POST\[',
            r'\$_REQUEST\[',
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-20",
        "owasp": "A03:2021",
        "description": "User input used without validation or sanitization.",
    },
    "Insecure Random": {
        "patterns": [
            r'\brandom\.random\s*\(',
            r'\brandom\.randint\s*\(',
            r'Math\.random\s*\(',
            r'\brandom\.choice\s*\(',
            r'new\s+Random\s*\(',
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-338",
        "owasp": "A02:2021",
        "description": "Weak PRNG used for security purposes. Use secrets module or os.urandom().",
    },
    "Disabled HTTPS": {
        "patterns": [
            r'verify\s*=\s*False',
            r'http://(?!localhost|127\.0\.0\.1)',
            r'ssl_verify\s*=\s*False',
            r'rejectUnauthorized\s*:\s*false',
            r'InsecureRequestWarning',
        ],
        "severity": "HIGH",
        "cwe": "CWE-295",
        "owasp": "A02:2021",
        "description": "SSL/TLS verification disabled or HTTP used. Always use HTTPS.",
    },
    "Bare Exception": {
        "patterns": [
            r'except\s*:',
            r'catch\s*\(\s*Exception\s+\w+\s*\)\s*\{\s*\}',
            r'rescue\s*=>',
            r'catch\s*\(\s*\.\.\.\s*\)',
        ],
        "severity": "LOW",
        "cwe": "CWE-390",
        "owasp": "A05:2021",
        "description": "Bare exception handler swallows all errors. Use specific exceptions.",
    },
    "Sensitive Data in Storage": {
        "patterns": [
            r'localStorage\.setItem\s*\(["\'](?:password|token|secret|key)',
            r'sessionStorage\.setItem\s*\(["\'](?:password|token|secret)',
            r'cookie.*password',
            r'document\.cookie.*token',
        ],
        "severity": "HIGH",
        "cwe": "CWE-312",
        "owasp": "A02:2021",
        "description": "Sensitive data stored in browser storage. Use secure httpOnly cookies.",
    },
    "Missing CORS": {
        "patterns": [
            r'Access-Control-Allow-Origin["\']?\s*:\s*["\']?\*',
            r'allow_origins\s*=\s*\[\s*["\']\*["\']',
            r'cors\(\s*\)',
            r"'Access-Control-Allow-Origin',\s*'\\*'",
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-942",
        "owasp": "A05:2021",
        "description": "Overly permissive CORS policy. Restrict to specific trusted origins.",
    },
    "Weak Password Requirements": {
        "patterns": [
            r'password.{0,20}len\s*[<>]\s*[1-5]\b',
            r'MIN_PASSWORD_LENGTH\s*=\s*[1-5]\b',
            r'minlength\s*=\s*["\'][1-5]["\']',
            r'password\s*==\s*["\'](?:admin|password|123456|test)["\']',
        ],
        "severity": "MEDIUM",
        "cwe": "CWE-521",
        "owasp": "A07:2021",
        "description": "Weak password requirements detected. Enforce strong password policy.",
    },
    "Unencrypted Transmission": {
        "patterns": [
            r'socket\.connect\s*\(',
            r'smtplib\.SMTP\s*\(',
            r'ftplib\.FTP\s*\(',
            r'telnetlib\.',
            r'new\s+Socket\s*\(',
        ],
        "severity": "HIGH",
        "cwe": "CWE-319",
        "owasp": "A02:2021",
        "description": "Unencrypted data transmission detected. Use TLS/SSL.",
    },
}

# Pre-compile regex patterns for performance optimization
COMPILED_RULES = {}
for vuln_type, rule_data in VULNERABILITY_RULES.items():
    compiled_patterns = []
    for pattern in rule_data["patterns"]:
        try:
            compiled_patterns.append((pattern, re.compile(pattern, re.IGNORECASE)))
        except re.error:
            pass # Skip invalid regexes
    
    COMPILED_RULES[vuln_type] = {
        "compiled_patterns": compiled_patterns,
        "severity": rule_data["severity"],
        "cwe": rule_data["cwe"],
        "owasp": rule_data["owasp"],
        "description": rule_data["description"]
    }

LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "ruby": [".rb"],
    "php": [".php"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
    "swift": [".swift"],
}


def detect_language(filename: str, code: str = "") -> str:
    """Detect language from filename extension"""
    fname = filename.lower()
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if any(fname.endswith(ext) for ext in exts):
            return lang
    # Fallback: guess from code patterns
    if "def " in code and "import " in code:
        return "python"
    if "function " in code or "const " in code or "let " in code:
        return "javascript"
    if "public class " in code or "System.out" in code:
        return "java"
    if "func " in code and "package " in code:
        return "go"
    return "python"


def _run_external_scanners(code: str, filename: str) -> List[Dict[str, Any]]:
    """Runs Trivy and Trufflehog via Docker on the provided code."""
    findings = []
    
    # Fast exit if filename is not provided or it's a huge minified file
    if len(code) > 500000:
        return findings
        
    try:
        client = docker.from_env()
    except Exception as e:
        print(f"[DETECTION WARNING] Docker daemon not reachable for Trivy/Trufflehog: {e}")
        return findings
        
    temp_filename = f"scan_{uuid.uuid4().hex[:8]}_{os.path.basename(filename) if filename else 'temp.py'}"
    host_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp_sandbox"))
    os.makedirs(host_dir, exist_ok=True)
    temp_path = os.path.join(host_dir, temp_filename)
    
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        # 1. Run Trivy
        try:
            trivy_output = client.containers.run(
                image="aquasec/trivy:latest",
                command=f"fs --format json --scanners vuln,secret,misconfig /app/{temp_filename}",
                volumes={host_dir: {'bind': '/app', 'mode': 'ro'}},
                remove=True
            ).decode("utf-8")
            
            try:
                trivy_data = json.loads(trivy_output)
                results = trivy_data.get("Results", [])
                for result in results:
                    target_vulns = result.get("Vulnerabilities", []) + result.get("Secrets", []) + result.get("Misconfigurations", [])
                    for tv in target_vulns:
                        # Map Trivy severity
                        sev_map = {"CRITICAL": "CRITICAL", "HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW", "UNKNOWN": "INFO"}
                        findings.append({
                            "type": f"Trivy: {tv.get('VulnerabilityID', tv.get('Title', tv.get('Type', 'Issue')))}",
                            "severity": sev_map.get(tv.get("Severity", "MEDIUM"), "MEDIUM"),
                            "line": tv.get("StartLine", 1),
                            "description": tv.get("Description", tv.get("Message", "Detected by Trivy")),
                            "code_snippet": f"Found in {filename}",
                            "cwe_id": tv.get("CweIDs", [""])[0] if tv.get("CweIDs") else "",
                            "owasp_id": "",
                            "confidence": 0.95,
                            "confidence_level": "VERY_HIGH"
                        })
            except Exception as e:
                print(f"[TRIVY ERROR] JSON parse failed: {e}")
        except Exception as e:
            print(f"[TRIVY ERROR] Docker run failed: {e}")

        # 2. Run Trufflehog
        try:
            trufflehog_output = ""
            try:
                # Trufflehog returns non-zero if secrets are found
                trufflehog_output = client.containers.run(
                    image="trufflesecurity/trufflehog:latest",
                    command=f"filesystem --json /app/{temp_filename}",
                    volumes={host_dir: {'bind': '/app', 'mode': 'ro'}},
                    remove=True
                ).decode("utf-8")
            except docker.errors.ContainerError as ce:
                trufflehog_output = ce.stdout.decode("utf-8") if ce.stdout else ""
                
            for line in trufflehog_output.split("\n"):
                if not line.strip(): continue
                try:
                    th_data = json.loads(line)
                    if "DetectorName" in th_data:
                        findings.append({
                            "type": f"Hardcoded Credentials (Trufflehog: {th_data.get('DetectorName')})",
                            "severity": "CRITICAL",
                            "line": 1,
                            "description": f"Leaked secret of type {th_data.get('DetectorName')}",
                            "code_snippet": th_data.get("Raw", "")[:77] + "...",
                            "cwe_id": "CWE-798",
                            "owasp_id": "A07:2021",
                            "confidence": 0.95,
                            "confidence_level": "VERY_HIGH"
                        })
                except:
                    pass
        except Exception as e:
            print(f"[TRUFFLEHOG ERROR] Docker run failed: {e}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return findings


def detect_vulnerabilities(code: str, language: str = "python", filename: str = "") -> List[Dict[str, Any]]:
    """Run all 15 detection rules against the code with optimizations."""
    findings = []
    lines = code.split("\n")

    for vuln_type, rule in COMPILED_RULES.items():
        for raw_pattern, compiled_regex in rule["compiled_patterns"]:
            for i, line in enumerate(lines, 1):
                # Optimization: Skip extremely long lines to avoid ReDoS (minified files)
                if len(line) > 1000:
                    continue
                
                if compiled_regex.search(line):
                    # Avoid duplicates on same line
                    if not any(f["type"] == vuln_type and f["line"] == i for f in findings):
                        snippet = line.strip()
                        if len(snippet) > 80:
                            snippet = snippet[:77] + "..."
                        
                        confidence_score = _calc_confidence(line, filename)
                        
                        findings.append({
                            "type": vuln_type,
                            "severity": rule["severity"],
                            "line": i,
                            "description": rule["description"],
                            "code_snippet": snippet,
                            "cwe_id": rule["cwe"],
                            "owasp_id": rule["owasp"],
                            "confidence": confidence_score,
                            "confidence_level": _confidence_label(confidence_score),
                        })

    # Run External Scanners (Trivy & Trufflehog)
    external_findings = _run_external_scanners(code, filename)
    findings.extend(external_findings)

    # Sort: CRITICAL first
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    findings.sort(key=lambda x: severity_order.get(x["severity"], 5))

    return findings


def get_risk_level(vulnerabilities: List[Dict[str, Any]]) -> str:
    """Aggregate highest severity from findings."""
    if any(v["severity"] == "CRITICAL" for v in vulnerabilities):
        return "CRITICAL"
    if any(v["severity"] == "HIGH" for v in vulnerabilities):
        return "HIGH"
    if any(v["severity"] == "MEDIUM" for v in vulnerabilities):
        return "MEDIUM"
    if any(v["severity"] == "LOW" for v in vulnerabilities):
        return "LOW"
    return "SAFE"


def _calc_confidence(line: str, filename: str) -> float:
    """Calculate confidence score based on context of the line and filename."""
    base = 0.85
    
    # Adjust based on line contents
    if len(line.strip()) > 10:
        base += 0.05
    
    line_lower = line.lower()
    if "test" in line_lower or "example" in line_lower:
        base -= 0.15
    if "#" in line or "//" in line:
        base -= 0.10
        
    # Adjust based on filename (e.g. test files)
    if filename:
        fname_lower = filename.lower()
        if "test" in fname_lower or "spec" in fname_lower or "mock" in fname_lower:
            base -= 0.20
            
    return round(min(max(base, 0.5), 0.99), 2)


def _confidence_label(score: float) -> str:
    """Map numerical score to a categorical label."""
    if score >= 0.95:
        return "VERY_HIGH"
    if score >= 0.85:
        return "HIGH"
    if score >= 0.75:
        return "MODERATE"
    if score >= 0.65:
        return "LOW"
    return "VERY_LOW"
