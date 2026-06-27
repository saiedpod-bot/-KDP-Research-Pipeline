# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.0.x | ✅ |
| < 2.0 | ❌ |

## Credential Management

**No credentials are ever hardcoded.** All sensitive values are handled through:

1. **`config.ini`** — user configuration file (listed in `.gitignore`)
2. **`.env`** — legacy environment file (listed in `.gitignore`)
3. **Environment variables** — `SERPAPI_KEY`, `GOOGLE_SHEET_ID`, etc.

### For Local Development

#### 1. SerpApi Key

Obtain a free API key from [SerpApi](https://serpapi.com) (100 searches/month free).

Set it using one of the following methods (listed in order of precedence):

- **config.ini**: Add `SERPAPI_KEY=your_key` to your `config.ini`
- **Environment variable**: `$env:SERPAPI_KEY="your_key"` (PowerShell) or `export SERPAPI_KEY="your_key"` (bash)

#### 2. Google Sheets (Optional)

- Create a Google Cloud service account
- Download the JSON credentials file
- Share your target Google Sheet with the service account email
- Do **not** commit the credentials file — add it to `.gitignore`

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue. Instead, report it privately by emailing the project maintainers.

We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Best Practices

- **Never commit** `config.ini`, `.env`, or `credentials.json` to version control
- **Rotate API keys** regularly via the SerpApi dashboard
- **Revoke compromised keys** immediately
- **Use a virtual environment** to isolate dependencies

## .gitignore Protection

The following files are protected by `.gitignore` and will never be committed:

- `.env` — environment variables
- `config.ini` — user configuration
- `credentials.json` — Google service account keys
- `*.db` — SQLite databases
- `*.log` — log files
- `dist/`, `build/`, `dist_obfuscated/` — build artifacts
