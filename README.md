# AegisFlow: Autonomous Multi-Agent DevSecOps Pipeline

**Final Year Major Project**  
**SNDT Women's University, Mumbai**  
**Program:** B.Tech Computer Science  

---

## 1. Abstract
AegisFlow is an autonomous, multi-agent security vulnerability detection and remediation platform. Designed to integrate smoothly into a DevSecOps pipeline, it automates the process of identifying vulnerabilities in code, evaluating risk via confidence scoring, and proposing concrete remediation steps using generative AI (Google Gemini). This project demonstrates the application of Large Language Models (LLMs) and multi-agent architectures in software security.

## 2. Project Architecture & Features
The system employs a client-server architecture with an intelligent backend capable of static code analysis and automated patching:
- **Vulnerability Detection Agent:** Identifies 15 distinct types of security vulnerabilities (e.g., SQL Injection, Insecure Deserialization, Hardcoded Secrets) across multiple programming languages.
- **Remediation Agent:** Utilizes Google Gemini AI to generate context-aware fixes and present them in a side-by-side diff format.
- **Confidence Scoring System:** Calculates quantitative severity metrics to help prioritize critical risks.
- **Reporting & Exporting:** Generates comprehensive PDF, Markdown, and ZIP reports of the scan results.
- **Dashboard & Analytics:** A centralized user interface built with Chart.js for tracking scan history and system usage.

## 3. Technology Stack
- **Backend:** Python 3.11+, FastAPI (for high-performance asynchronous API endpoints)
- **Frontend:** HTML, CSS, JavaScript (Vanilla JS with Chart.js)
- **Database:** MongoDB (LocalNoSQL storage for user data and scan history)
- **AI Integration:** Google Gemini API (for vulnerability analysis and code remediation)
- **Authentication:** JWT (JSON Web Tokens) for secure session management

## 4. Setup and Installation

### Prerequisites
- Python 3.11 or higher
- MongoDB Community Server running on `localhost:27017`
- A Google Gemini API Key (accessible via Google AI Studio)

### Backend Configuration
1. Open a terminal and navigate to the project root directory.
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the environment variables in a `.env` file at the root of the project:
   ```env
   MONGO_URI=mongodb://localhost:27017/aegisflow
   DB_NAME=aegisflow
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=aegisflow_secure_key
   ```
5. Start the backend server:
   ```bash
   python -m uvicorn backend.app:app --reload --port 8000
   ```

### Frontend Configuration
1. Open a separate terminal window and navigate to the `frontend` directory.
2. Start a local HTTP server:
   ```bash
   cd frontend
   python -m http.server 3000 --bind 127.0.0.1
   ```
3. Access the application by opening `http://127.0.0.1:3000/login.html` in a web browser.

## 5. API Reference
The application provides a robust set of RESTful endpoints. Comprehensive, interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs` when the backend is running.

**Key Endpoints:**
- `/api/auth/register` (POST) - User registration
- `/api/auth/login` (POST) - JWT token generation
- `/api/analyze` (POST) - Submits code snippets for vulnerability scanning
- `/api/fix` (POST) - Generates remediation code
- `/api/scans` (GET) - Retrieves historical scan data

## 6. Project Team
This project was developed by:
- **Bhavishya** (Roll No: 54)
- **Gauri** (Roll No: 67)
- **Khushi** (Roll No: 77)

---
*Developed as part of the B.Tech Computer Science curriculum. For academic evaluation purposes only.*
