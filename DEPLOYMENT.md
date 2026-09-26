# AegisFlow Deployment Guide

This guide explains how to take the containerized AegisFlow application and deploy it to a live cloud provider. You can choose to deploy either on a Virtual Machine (e.g., AWS EC2) or a PaaS (e.g., Render/Railway).

## Option A: Deploying on AWS EC2 (Recommended for full control)

1. **Launch an EC2 Instance**:
   - Go to the AWS Console, navigate to EC2, and launch a new instance (Ubuntu 22.04 LTS).
   - A `t2.medium` or `t3.medium` is recommended as Gemini analysis and MongoDB can consume some memory.
   - Configure the **Security Group** to allow inbound traffic on:
     - Port `22` (SSH)
     - Port `80` (HTTP - Optional)
     - Port `3000` (Frontend)
     - Port `8000` (Backend API)

2. **Connect to your EC2 Instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

3. **Install Docker & Docker Compose**:
   ```bash
   sudo apt update
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker ubuntu
   # Log out and log back in to apply docker group
   ```

4. **Clone your repository**:
   ```bash
   git clone https://github.com/your-username/aegisflow.git
   cd aegisflow
   ```

5. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```bash
   touch .env
   nano .env
   # Add your GEMINI_API_KEY, GITHUB_TOKEN, and JWT_SECRET here.
   ```

6. **Update the API URL for the Frontend**:
   Edit the `docker-compose.yml` file and update the `BACKEND_URL` under the `frontend` service so it points to your EC2 public IP:
   ```yaml
   environment:
     - BACKEND_URL=http://<your-ec2-public-ip>:8000
   ```

7. **Deploy the application**:
   ```bash
   docker-compose up -d --build
   ```
   
   Your frontend is now live at `http://<your-ec2-public-ip>:3000` and the backend is at `http://<your-ec2-public-ip>:8000`.

---

## Option B: Deploying on Render (Easiest, Managed PaaS)

Render is great because it automatically builds your Dockerfiles and provides free HTTPS.

1. **Push your code to GitHub**.
2. **Create a new PostgreSQL/MongoDB instance** (Render has Postgres, but for MongoDB you might want to use MongoDB Atlas - a free cloud database).
   - If using MongoDB Atlas, get the connection string and update the `MONGO_URI` environment variable.
3. **Deploy the Backend**:
   - In Render, create a new **Web Service**.
   - Connect your GitHub repository.
   - Choose `Docker` as the runtime.
   - Specify the `Dockerfile.backend` path.
   - Add your Environment Variables (`MONGO_URI`, `GEMINI_API_KEY`, `GITHUB_TOKEN`, `JWT_SECRET`).
   - Render will give you a live URL like `https://aegisflow-backend.onrender.com`.
4. **Deploy the Frontend**:
   - Create a second **Web Service** in Render.
   - Connect the same repository.
   - Choose `Docker` as the runtime, and specify `Dockerfile.frontend`.
   - Add the Environment Variable: `BACKEND_URL=https://aegisflow-backend.onrender.com`
   - Render will deploy the frontend to a live URL like `https://aegisflow-ui.onrender.com`.

---

## Verifying Deployment

Once deployed, visit your frontend URL (e.g., `http://<ec2-ip>:3000`). 
Ensure that:
1. You can register and log in.
2. Code scans execute properly.
3. The GitHub webhook integration works (if you configure your GitHub repo settings to point to `http://<ec2-ip>:8000/api/webhooks/github`).
