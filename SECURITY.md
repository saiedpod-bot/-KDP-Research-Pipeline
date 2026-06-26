# Security Policy — KDP Research Pipeline

## Credential Management

**No credentials are ever hardcoded.** All sensitive values are handled through environment variables, `.env` files, or GitHub Repository Secrets.

## For Local Development

### 1. SerpApi Key

```bash
cp .env.example .env
```

Edit `.env`:

```ini
SERPAPI_KEY=your_serpapi_key_here
```

`.env` is listed in `.gitignore` and will never be committed.

### 2. Google Sheets (Optional)

If using Google Sheets export:
1. Create a service account in [Google Cloud Console](https://console.cloud.google.com)
2. Download the JSON key as `credentials.json`
3. Place it in the project root
4. Reference it in `.env`:

```ini
GOOGLE_APPLICATION_CREDENTIALS=credentials.json
```

`credentials.json` is listed in `.gitignore` and will never be committed.

## For CI/CD (GitHub Actions)

### Setting Repository Secrets

1. Go to **GitHub repo → Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add:

| Secret Name | Value | Required For |
|-------------|-------|-------------|
| `SERPAPI_KEY` | Your SerpApi key | Integration tests (optional) |

The `GITHUB_TOKEN` secret is **automatically injected** by GitHub into all workflows — no manual setup needed.

### How Secrets Flow in CI

```
Your Secret → GitHub Encrypted Store → ${{ secrets.NAME }} in workflow → Runtime env var
```

Secrets are:
- Encrypted at rest by GitHub
- Masked in all logs
- Never exposed in build output
- Only accessible to workflows in the same repository

## For Docker (ghcr.io)

When running the Docker image, pass credentials via environment variables:

```bash
docker run -p 8501:8501 \
  -e SERPAPI_KEY=your_key_here \
  ghcr.io/saiedpod-bot/kdp-research-pipeline:latest
```

For Docker Compose, use an `.env` file (gitignored):

```yaml
# docker-compose.yml
services:
  kdp-pipeline:
    image: ghcr.io/saiedpod-bot/kdp-research-pipeline:latest
    env_file: .env
```

## Reporting a Vulnerability

If you find a security issue, please open a private issue or contact the repository owner directly. Do not post credentials or tokens in public issues.
