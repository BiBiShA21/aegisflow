"""
AegisFlow - Sandbox Service
Executes AI-generated code in an isolated Docker container to validate syntax and safety.
"""
import os
import uuid
import docker
from typing import Dict, Any

def validate_code_in_sandbox(code: str, language: str = "python") -> Dict[str, Any]:
    """
    Spins up an isolated Docker container to validate the fixed code.
    Calculates a confidence bonus based on execution success.
    """
    # We support multiple languages now
    supported_langs = ["python", "py", "javascript", "js", "typescript", "ts", "java", "go"]
    if language.lower() not in supported_langs:
        return {
            "success": True, 
            "message": f"Sandbox validation not configured for language: {language}", 
            "confidence_bonus": 0.0
        }

    try:
        # Attempt to connect to the local Docker daemon
        client = docker.from_env()
    except Exception as e:
        print(f"[SANDBOX WARNING] Docker daemon not reachable. Is Docker Desktop running? Skipping validation.")
        return {
            "success": True, 
            "message": "Docker daemon unavailable. Sandbox skipped.", 
            "confidence_bonus": 0.0
        }

    # 1. Write the code to a temporary file locally
    temp_filename = f"sandbox_eval_{uuid.uuid4().hex[:8]}.py"
    # Put it in a 'temp_sandbox' folder in the backend directory
    host_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "temp_sandbox"))
    os.makedirs(host_dir, exist_ok=True)
    temp_path = os.path.join(host_dir, temp_filename)
    
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        print(f"[SANDBOX] Launching isolated container to test {temp_filename}...")
        
        # 2. Run the container securely based on language
        ext = ".py"
        image = "python:3.11-slim"
        command = f"python -m py_compile /app/{temp_filename}"
        
        if language.lower() in ["javascript", "js"]:
            ext = ".js"
            image = "node:18-slim"
            command = f"node --check /app/{temp_filename}"
        elif language.lower() in ["typescript", "ts"]:
            ext = ".ts"
            image = "node:18-slim"
            # Basic JS syntax check as fallback for TS since full compilation requires tsconfig
            command = f"node --check /app/{temp_filename}" 
        elif language.lower() == "java":
            ext = ".java"
            image = "openjdk:17-slim"
            command = f"javac /app/{temp_filename}"
        elif language.lower() == "go":
            ext = ".go"
            image = "golang:1.21-alpine"
            command = f"go run /app/{temp_filename}"
            
        # Update filename with correct extension
        new_filename = temp_filename.replace(".py", ext)
        new_path = temp_path.replace(".py", ext)
        os.rename(temp_path, new_path)
        temp_path = new_path
        temp_filename = new_filename
        
        container_output = client.containers.run(
            image=image,
            command=command,
            volumes={host_dir: {'bind': '/app', 'mode': 'ro'}},
            remove=True,
            mem_limit="256m",
            network_disabled=True
        )
        
        print("[SANDBOX] Code compilation successful. Sandbox validation PASSED.")
        return {
            "success": True,
            "message": "Sandbox validation passed successfully. Code is syntactically valid.",
            "confidence_bonus": 0.05
        }
        
    except docker.errors.ContainerError as e:
        # Container returned a non-zero exit code (e.g. SyntaxError)
        error_logs = e.stderr.decode("utf-8") if e.stderr else str(e)
        print(f"[SANDBOX ERROR] Code compilation failed: {error_logs}")
        return {
            "success": False,
            "message": f"Sandbox validation failed (Syntax Error):\n{error_logs}",
            "confidence_bonus": -0.30
        }
        
    except Exception as e:
        print(f"[SANDBOX ERROR] Unexpected execution error: {e}")
        return {
            "success": False,
            "message": f"Sandbox execution error: {str(e)}",
            "confidence_bonus": 0.0
        }
        
    finally:
        # 3. Cleanup the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
