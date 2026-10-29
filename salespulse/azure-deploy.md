# SalesPulse AI — Azure Deployment Guide

Your Azure App Service `salespulse-ai-app` is successfully created and configured to pull a custom Docker container on port `8000`. This guide documents the remaining configuration steps to ensure secure, production-ready execution.

---

## 1. Configure App Service Environment Variables

SalesPulse AI requires two environment variables to run. You must configure these in the Azure Portal or via Azure CLI so they are securely injected into the container at runtime.

### Variables to set:
1. **`GEMINI_API_KEY`**: Your Google Gemini API Key.
2. **`SECRET_KEY`**: A secure random string used to sign JWT authentication tokens (e.g. `openssl rand -hex 32`).
3. **`CORS_ORIGINS`** (Optional): A comma-separated list of allowed CORS origins if you host the frontend on a different domain.

### How to set via Azure Portal:
1. Go to the Azure Portal and search for your App Service: **`salespulse-ai-app`**.
2. In the left navigation menu, under **Settings**, click on **Configuration** (or **Environment variables** in newer portals).
3. Click **+ New application setting**.
   - Name: `GEMINI_API_KEY`
   - Value: `<your-gemini-key>`
4. Click **+ New application setting**.
   - Name: `SECRET_KEY`
   - Value: `<your-secret-key>`
5. Click **Save** at the top of the page. This will restart the App Service container with the new variables active.

### How to set via Azure CLI:
```bash
az webapp config appsettings set \
  --name salespulse-ai-app \
  --resource-group salespulse-ut-rg \
  --settings GEMINI_API_KEY="your-gemini-key" SECRET_KEY="your-secret-key"
```

---

## 2. CI/CD Deployment Flow (GitHub Actions)

Your repository includes a Github Action pipeline at `.github/workflows/deploy.yml` that automatically builds and pushes the production container to GitHub Container Registry (GHCR).

### Verifying Registry Details in Azure
In your Azure App Service **Deployment Center**:
- **Registry Source**: `Private Registry` or `Custom`
- **Server URL**: `https://ghcr.io`
- **Image**: `amank326/salespulse-ai`
- **Tag**: `latest`
- **Port**: `8000`

If the container image is private, make sure you configure your registry credentials (username: GitHub Username, password/token: GitHub Personal Access Token with package read permissions) in the Azure Deployment Center so Azure can pull the image successfully.

---

## 3. Monitoring Container Logs
If you encounter any start-up issues or want to check model logs:
1. Go to your App Service in the Azure Portal.
2. Under **Monitoring** in the left menu, select **Log stream**.
3. You will see live standard output (stdout/stderr) from the FastAPI backend and Uvicorn server.
