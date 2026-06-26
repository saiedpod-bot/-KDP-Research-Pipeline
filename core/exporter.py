"""
exporter.py — Tier 3: Google Sheets Export Module

Part of the Amazon KDP Research Pipeline.
Reads ranked JSON output from analyzer.py and uploads it to Google Sheets
in "Master Sheet" mode — each research run is appended with a timestamp.

Additive-only module: extend with new export targets, never rewrite existing.

Dependencies:
    pip install gspread google-auth

Google Cloud Setup (one-time):
    1. Go to https://console.cloud.google.com
    2. Create a project (or select existing)
    3. Enable the "Google Sheets API"
    4. Go to IAM & Admin → Service Accounts → Create Service Account
    5. Assign role: "Editor" (or "Viewer" is sufficient for read-only)
    6. Create a JSON key → download as credentials.json
    7. Share your target Google Sheet with the service account email
       (found in the JSON key: client_email)
    8. Place credentials.json in the project root (or set GOOGLE_CREDENTIALS_PATH)

Author: KDP Automation Architect
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional dependencies — graceful fallback
# ---------------------------------------------------------------------------
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "exporter.log", mode="a"),
    ],
)
logger = logging.getLogger("kdpexporter")

# ---------------------------------------------------------------------------
# Paths — aligned with scraper.py and analyzer.py
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
OUTPUT_DIR: Path = PROJECT_ROOT / "output"


# ---------------------------------------------------------------------------
# Auth: service account → gspread client
# ---------------------------------------------------------------------------
def authenticate_sheets(
    credentials_path: Optional[str] = None,
) -> Optional[Any]:
    """
    Authenticate with Google Sheets API using a service account JSON key.

    Parameters
    ----------
    credentials_path : str, optional
        Path to the service account JSON file.
        If None, checks the GOOGLE_CREDENTIALS_PATH env var,
        then falls back to PROJECT_ROOT / credentials.json.

    Returns
    -------
    gspread.Client or None
        Authenticated gspread client, or None if auth fails.
    """
    if not HAS_GSHEETS:
        logger.error(
            "gspread / google-auth not installed. "
            "Run: pip install gspread google-auth"
        )
        return None

    try:
        # Resolve credentials path
        resolved_path: Optional[Path] = None
        if credentials_path:
            resolved_path = Path(credentials_path)
        elif os.getenv("GOOGLE_CREDENTIALS_PATH"):
            resolved_path = Path(os.getenv("GOOGLE_CREDENTIALS_PATH"))
        else:
            resolved_path = PROJECT_ROOT / "credentials.json"

        if not resolved_path.exists():
            logger.error(
                "Credentials file not found at %s. "
                "See module docstring for Google Cloud setup instructions.",
                resolved_path,
            )
            return None

        # Define required scopes
        scopes: List[str] = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
        ]

        creds = Credentials.from_service_account_file(
            str(resolved_path), scopes=scopes
        )
        client = gspread.authorize(creds)

        logger.info(
            "Authenticated with Google Sheets — service account: %s",
            creds.service_account_email,
        )
        return client

    except Exception as exc:
        logger.error("Google Sheets authentication failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Loader: read ranked JSON output from analyzer.py
# ---------------------------------------------------------------------------
def load_ranked_data(
    query: str,
    file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load ranked product data from analyzer.py's output.

    Parameters
    ----------
    query : str
        Search query (derives default filename).
    file_path : str, optional
        Override path to a specific ranked JSON file.

    Returns
    -------
    list[dict]
        Ranked product rows, or empty list on failure.
    """
    try:
        if file_path:
            path = Path(file_path)
        else:
            safe_name: str = query.lower().replace(" ", "_")[:60]
            path = OUTPUT_DIR / f"ranked_{safe_name}.json"

        if not path.exists():
            logger.error("Ranked data not found at %s. Run analyzer.py first.", path)
            return []

        with open(path, "r", encoding="utf-8") as fh:
            data: List[Dict[str, Any]] = json.load(fh)

        logger.info("Loaded %d ranked rows from %s", len(data), path)
        return data

    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        return []
    except Exception as exc:
        logger.error("Failed to load ranked data: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Sheet writer: append rows to a Google Sheet
# ---------------------------------------------------------------------------
def upload_to_sheet(
    rows: List[Dict[str, Any]],
    spreadsheet_id: str,
    sheet_name: str = "KDP_Research",
    client: Optional[Any] = None,
    credentials_path: Optional[str] = None,
) -> bool:
    """
    Upload ranked product data to a Google Sheet in Master Sheet mode.

    Master Sheet behaviour
    ----------------------
    - If the sheet (tab) does not exist, it is created with a header row.
    - Data rows are appended with a UTC timestamp column prepended.
    - Subsequent runs append new rows below existing data — never overwrites.

    Parameters
    ----------
    rows : list[dict]
        Ranked product rows from analyzer.py.
    spreadsheet_id : str
        ID of the target Google Sheet
        (extracted from its URL: https://docs.google.com/spreadsheets/d/{ID}/edit).
    sheet_name : str
        Name of the sheet tab within the spreadsheet (default: "KDP_Research").
    client : gspread.Client, optional
        Pre-authenticated client. If None, calls authenticate_sheets().
    credentials_path : str, optional
        Path to service account JSON (used if client is None).

    Returns
    -------
    bool
        True on success, False on failure.
    """
    if not rows:
        logger.warning("No rows to upload — skipping.")
        return False

    try:
        # --- Auth ---
        gs_client = client or authenticate_sheets(credentials_path)
        if gs_client is None:
            return False

        # --- Open spreadsheet ---
        try:
            sh = gs_client.open_by_key(spreadsheet_id)
            logger.info("Opened spreadsheet: %s", sh.title)
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(
                "Spreadsheet with ID '%s' not found. "
                "Ensure the service account email has access.",
                spreadsheet_id,
            )
            return False
        except gspread.exceptions.APIError as exc:
            logger.error("Google Sheets API error (quota / access): %s", exc)
            return False

        # --- Open or create sheet tab ---
        try:
            worksheet = sh.worksheet(sheet_name)
            logger.info("Found existing sheet tab: %s", sheet_name)
            # Check if header row exists
            existing = worksheet.get_all_values()
            has_header = len(existing) > 0
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=sheet_name, rows=1000, cols=50)
            has_header = False
            logger.info("Created new sheet tab: %s", sheet_name)

        # --- Prepare data rows with timestamp ---
        timestamp: str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        headers: List[str] = [
            "Timestamp",
            "ASIN",
            "Title",
            "Author",
            "Price",
            "BSR",
            "ReviewCount",
            "Rating",
            "PublicationDate",
            "SmartScore",
        ]

        # Build row values, safely extracting each field
        data_rows: List[List[Any]] = []
        for row in rows:
            try:
                data_rows.append([
                    timestamp,
                    row.get("ASIN", ""),
                    row.get("Title", ""),
                    row.get("Author", ""),
                    row.get("Price", 0),
                    row.get("BSR", 0),
                    row.get("ReviewCount", 0),
                    row.get("Rating", 0),
                    row.get("PublicationDate", ""),
                    row.get("SmartScore", 0),
                ])
            except Exception as exc:
                logger.warning(
                    "Skipping malformed row (ASIN: %s): %s",
                    row.get("ASIN", "?"),
                    exc,
                )
                continue

        # --- Write ---
        if not has_header:
            # Write header + data in one call
            worksheet.append_rows(
                [headers] + data_rows,
                value_input_option="USER_ENTERED",
            )
            logger.info(
                "Created header + appended %d rows to sheet '%s'.",
                len(data_rows),
                sheet_name,
            )
        else:
            # Append only data rows (skip header)
            worksheet.append_rows(
                data_rows,
                value_input_option="USER_ENTERED",
            )
            logger.info(
                "Appended %d rows to existing sheet '%s'.",
                len(data_rows),
                sheet_name,
            )

        return True

    except gspread.exceptions.APIError as exc:
        logger.error("Google Sheets API quota / rate-limit error: %s", exc)
        return False
    except Exception as exc:
        logger.error("Failed to upload to Google Sheets: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Full pipeline: load ranked data → authenticate → upload
# ---------------------------------------------------------------------------
def run_export(
    query: str,
    spreadsheet_id: str,
    sheet_name: str = "KDP_Research",
    credentials_path: Optional[str] = None,
    file_path: Optional[str] = None,
) -> bool:
    """
    Execute the full export pipeline for a given search query.

    Steps
    -----
    1. Load ranked data from analyzer.py output.
    2. Authenticate with Google Sheets.
    3. Upload (append) data to the master sheet.

    Parameters
    ----------
    query : str
        Search query matching an analyzer output file.
    spreadsheet_id : str
        Google Sheet ID to upload to.
    sheet_name : str
        Sheet tab name (default: KDP_Research).
    credentials_path : str, optional
        Path to service account JSON.
    file_path : str, optional
        Override path for ranked JSON file.

    Returns
    -------
    bool
        True on success, False on failure.
    """
    logger.info("=" * 60)
    logger.info("KDP Research Pipeline — Tier 3: Export")
    logger.info("Query: %s", query)
    logger.info("Sheet ID: %s", spreadsheet_id)
    logger.info("=" * 60)

    # Step 1 — load
    rows: List[Dict[str, Any]] = load_ranked_data(query=query, file_path=file_path)
    if not rows:
        logger.error("No data to export. Run scraper.py + analyzer.py first.")
        return False

    # Step 2 — upload
    success: bool = upload_to_sheet(
        rows=rows,
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
        credentials_path=credentials_path,
    )

    if success:
        logger.info("Export complete — %d rows pushed to Google Sheets.", len(rows))
    else:
        logger.error("Export failed — see logs above for details.")

    return success


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Tier 3: Export ranked KDP data to Google Sheets"
    )
    parser.add_argument("query", type=str, help="Search query matching an analyzer output file")
    parser.add_argument(
        "--sheet-id",
        type=str,
        default=os.getenv("GOOGLE_SHEET_ID", ""),
        help=(
            "Google Sheet ID (or set GOOGLE_SHEET_ID env var). "
            "Extracted from URL: "
            "https://docs.google.com/spreadsheets/d/{ID}/edit"
        ),
    )
    parser.add_argument(
        "--sheet-name",
        type=str,
        default="KDP_Research",
        help="Sheet tab name within the spreadsheet (default: KDP_Research)",
    )
    parser.add_argument(
        "--creds",
        type=str,
        default=None,
        help="Path to service account JSON (default: project root / credentials.json)",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Direct path to ranked JSON file (overrides query-based lookup)",
    )

    args = parser.parse_args()

    if not args.sheet_id:
        logger.error(
            "No spreadsheet ID provided. "
            "Pass --sheet-id or set the GOOGLE_SHEET_ID environment variable."
        )
        sys.exit(1)

    success = run_export(
        query=args.query,
        spreadsheet_id=args.sheet_id,
        sheet_name=args.sheet_name,
        credentials_path=args.creds,
        file_path=args.file,
    )

    sys.exit(0 if success else 1)
