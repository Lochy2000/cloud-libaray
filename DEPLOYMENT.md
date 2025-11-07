# CI/CD Deployment Setup Guide

This guide explains how to set up automated deployment from GitHub to your Google Compute Engine (GCE) instance.

## Overview

The CI/CD pipeline automatically:
1. Runs tests when you push to the `main` branch
2. If tests pass, deploys to your GCE instance
3. Rebuilds Docker containers with the latest code
4. Runs database migrations
5. Restarts the application

## Prerequisites

- GitHub repository connected to this project
- GCE instance with Docker and Docker Compose installed
- SSH access to your GCE instance
- Your project cloned on the GCE instance

---

## Step 1: Set Up SSH Key for GitHub Actions

### On your LOCAL machine (where you are now):

1. Generate a new SSH key pair for GitHub Actions (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -C "github-actions@deploy" -f ~/.ssh/github_actions_deploy
   ```
   - Press Enter when asked for a passphrase (leave it empty)

2. Copy the PUBLIC key content:
   ```bash
   cat ~/.ssh/github_actions_deploy.pub
   ```
   - Save this output - you'll need it for the GCE instance

3. Copy the PRIVATE key content:
   ```bash
   cat ~/.ssh/github_actions_deploy
   ```
   - Save this output - you'll need it for GitHub secrets

### On your GCE instance:

1. SSH into your GCE instance:
   ```bash
   ssh your-username@your-gce-ip
   ```

2. Add the PUBLIC key to authorized_keys:
   ```bash
   echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. Find your project path (where the code is located):
   ```bash
   pwd
   ```
   - Example: `/home/your-username/postgreSQL` or `/opt/library-app`
   - Save this path - you'll need it for GitHub secrets

---

## Step 2: Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:

### Required Secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GCE_HOST` | Your GCE instance external IP address | `34.123.45.67` |
| `GCE_USERNAME` | SSH username on GCE instance | `your-username` |
| `GCE_SSH_KEY` | Private SSH key (from Step 1) | Contents of `github_actions_deploy` file |
| `GCE_PROJECT_PATH` | Full path to project on GCE | `/home/your-username/postgreSQL` |
| `GCE_SSH_PORT` | SSH port (optional, defaults to 22) | `22` |

### How to add each secret:
1. Click "New repository secret"
2. Enter the **Name** (e.g., `GCE_HOST`)
3. Paste the **Value**
4. Click "Add secret"
5. Repeat for all secrets

---

## Step 3: Verify GCE Instance Setup

SSH into your GCE instance and verify:

### 1. Docker is installed:
```bash
docker --version
docker-compose --version
```

### 2. Project is cloned:
```bash
cd /path/to/your/project
git status
```

### 3. Environment variables exist:
```bash
ls -la .env
cat .env  # Check contents
```

### 4. Git remote is configured:
```bash
git remote -v
```

### 5. Docker containers can be managed:
```bash
docker-compose ps
```

---

## Step 4: Configure GCE Firewall (if needed)

Make sure your GCE instance allows:
- SSH access (port 22) from GitHub Actions IPs
- HTTP/HTTPS traffic (port 8000 or 80/443)

```bash
# On GCE, check firewall status
sudo ufw status

# If needed, allow ports
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
```

Or use GCP Console → VPC Network → Firewall rules

---

## Step 5: Test the Deployment

### Option 1: Make a test commit
```bash
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

### Option 2: Trigger manually
1. Go to GitHub → **Actions** tab
2. Click on "CI/CD Pipeline - Deploy to GCE"
3. Click "Run workflow" → "Run workflow"

### Monitor the deployment:
1. Go to GitHub → **Actions** tab
2. Click on your running workflow
3. Watch the logs in real-time

---

## Step 6: Verify Deployment on GCE

After the GitHub Action completes:

1. SSH into your GCE instance:
   ```bash
   ssh your-username@your-gce-ip
   ```

2. Check container status:
   ```bash
   cd /path/to/your/project
   docker-compose ps
   ```

3. Check application logs:
   ```bash
   docker-compose logs -f web
   ```

4. Test the application:
   ```bash
   curl http://localhost:8000
   ```

---

## Troubleshooting

### Deployment fails with "Permission denied"
- Verify the SSH key was added correctly to GCE's `~/.ssh/authorized_keys`
- Check SSH key format (should be one line, no extra spaces)

### Deployment fails with "git pull" errors
- SSH into GCE and manually run `git pull origin main`
- Check for uncommitted changes: `git status`
- If needed, stash changes: `git stash`

### Docker build fails
- SSH into GCE and check disk space: `df -h`
- Clean up old images: `docker system prune -a`
- Check Docker logs: `docker-compose logs`

### Tests fail in CI
- Run tests locally first: `python manage.py test`
- Check if all dependencies are in `requirements.txt`
- Verify database connection settings

### Containers don't start after deployment
- Check logs: `docker-compose logs`
- Verify `.env` file exists on GCE
- Check if ports are already in use: `sudo netstat -tulpn | grep 8000`

---

## Workflow Details

The pipeline consists of two jobs:

### 1. Test Job
- Runs on every push to `main`
- Sets up Python 3.12 and PostgreSQL
- Installs dependencies
- Runs Django tests
- Must pass before deployment

### 2. Deploy Job
- Runs only if tests pass
- Connects to GCE via SSH
- Pulls latest code from GitHub
- Rebuilds Docker containers
- Restarts the application
- Cleans up old images

---

## Security Notes

- Never commit `.env` files to GitHub
- Keep your SSH private key secure
- Use GitHub secrets for all sensitive data
- Consider using a dedicated service account for deployments
- Regularly rotate SSH keys
- Monitor GitHub Actions logs for suspicious activity

---

## Customization

### Deploy to different branches
Edit [.github/workflows/deploy.yml](.github/workflows/deploy.yml):
```yaml
on:
  push:
    branches:
      - main
      - staging  # Add more branches
```

### Skip tests (not recommended)
Remove or comment out the `needs: test` line in the deploy job

### Add deployment notifications
Integrate with Slack, Discord, or email in the workflow

---

## Next Steps

1. Set up HTTPS with Let's Encrypt/Certbot
2. Add monitoring (e.g., Prometheus, Grafana)
3. Implement blue-green deployment
4. Add database backup before deployment
5. Set up staging environment

---

## Questions?

If you encounter issues:
1. Check GitHub Actions logs
2. SSH into GCE and check `docker-compose logs`
3. Verify all secrets are configured correctly
4. Review this guide for missed steps
