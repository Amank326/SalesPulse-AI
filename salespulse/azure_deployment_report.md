# SalesPulse AI — Azure Deployment Analysis & Guide

This report analyzes your Azure App Service configuration based on the provided screenshots and details the steps required to synchronize your container registry and configure environment variables.

---

## 1. Container Registry Cross-Check

In your screenshots, there is a mismatch between the **Properties** and the **Deployment Center** configurations:

| Component | Registry Configuration in Screenshot | Location |
| :--- | :--- | :--- |
| **Properties Tab** (Active) | `ghcr.io/amank326/salespulse-ai:latest` | GitHub Container Registry (GHCR) |
| **Deployment Center** | `amank326/salespulse-ai:latest` | Docker Hub (or other default registry) |

### Action Required:
If you pushed your container image to **Docker Hub** (`amank326/salespulse-ai`), you must ensure the App Service registry type in the Deployment Center matches. 

If you are using **GitHub Container Registry (GHCR)** (which is configured in your `.github/workflows/deploy.yml` CI/CD pipeline):
1. In the **Deployment Center**, verify that the server URL is set to `https://ghcr.io`.
2. The image name must be `amank326/salespulse-ai` and the tag `latest`.
3. If your GitHub package is private, make sure to add your GitHub credentials in the Deployment Center so Azure has pull access.

---

## 2. Configuration Settings (Environment Variables)

Your backend requires two environment variables to run. If these are not configured, the container will run but Gemini features will fail.

### Variables to set:
1. `GEMINI_API_KEY`: Your Google Gemini API Key.
2. `SECRET_KEY`: A secure random token for JWT signing.

### How to set these variables:
Since the account containing the App Service (`aman.cloud2025@gmail.com`) requires multi-factor authentication (MFA), the easiest way is to run this command in your local terminal where you can complete the browser-based MFA challenge:

```bash
# 1. Log in to Azure
az login --tenant 58206954-6b3d-4267-9486-a557321920b1

# 2. Select the correct subscription
az account set --subscription ce176ab4-0474-47f5-bfe2-72e93937970f

# 3. Configure the App settings
az webapp config appsettings set \
  --name salespulse-ai-app \
  --resource-group salespulse-ut-rg \
  --settings GEMINI_API_KEY="<your-gemini-api-key>" SECRET_KEY="<generate-a-secure-random-key>"
```

Alternatively, you can add them directly in the Azure Portal:
1. Search for **`salespulse-ai-app`** in the portal.
2. In the left-hand navigation, under **Settings**, click on **Environment variables** (or **Configuration**).
3. Under **Application settings**, click **+ Add** (or **New application setting**).
   - Name: `GEMINI_API_KEY`
   - Value: `<your-gemini-key>`
4. Repeat for `SECRET_KEY`.
5. Click **Apply** or **Save** at the bottom/top.

---

## 3. Installing the VS Code Azure Extension

To manage this App Service directly from VS Code:
1. Open **VS Code**.
2. Click on the **Extensions** icon on the left sidebar (or press `Ctrl+Shift+X`).
3. Search for: **`Azure App Service`** (published by Microsoft).
4. Click **Install**.
5. Once installed, click on the **Azure** icon that appears in the sidebar.
6. Click **Sign in to Azure...** and select the account **`aman.cloud2025@gmail.com`**.
7. You will see your subscription (`Azure for Students`) and App Service (`salespulse-ai-app`) listed. You can right-click it to upload files, stream logs, or restart the container.
