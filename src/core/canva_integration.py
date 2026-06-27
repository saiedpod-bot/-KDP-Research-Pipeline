"""
canva_integration.py — Canva Connect API Wrapper for KDP Discovery Engine

Provides:
  - Template URL redirection (open user's saved Canva templates per book type)
  - Asset upload to Canva via the Connect API (REST)
  - OAuth2 token management for Connect API

Requires config.ini [Canva] section or environment variables.

Canva Connect API Docs: https://www.canva.dev/docs/connect/
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from urllib.parse import urlencode

import requests

from . import config_manager as cfg

logger = logging.getLogger("kdpcanva")

# ---------------------------------------------------------------------------
# Book type → config key mapping
# ---------------------------------------------------------------------------
_BOOK_TYPE_TEMPLATE_KEYS: Dict[str, str] = {
    "Coloring Book": "COLORING_TEMPLATE",
    "Planner": "PLANNER_TEMPLATE",
    "Activity Book": "ACTIVITY_TEMPLATE",
}

# Book types that have template support
SUPPORTED_BOOK_TYPES: List[str] = list(_BOOK_TYPE_TEMPLATE_KEYS.keys())

# Canva Connect API base URL
_CONNECT_API_BASE = "https://api.canva.com/rest"


class CanvaIntegration:
    """Manages Canva template URLs and Connect API interactions.

    Two-tier design:
      1. **Template Redirection** — opens user-configured Canva template edit
         URLs in the browser. No authentication needed.
      2. **Connect API Upload** — uploads generated assets (images) to the
         user's Canva library via the REST Connect API (requires OAuth2).
    """

    def __init__(self, config_ini_path: Optional[Path] = None):
        self._config_path = config_ini_path or cfg.CONFIG_INI_PATH
        self._template_urls: Dict[str, str] = {}
        self._client_id: str = ""
        self._client_secret: str = ""
        self._access_token: str = ""
        self._token_expires_at: float = 0
        self._refresh_token: str = ""
        self._load_config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_template_url(self, book_type: str) -> Optional[str]:
        """Return the saved Canva template URL for a book type, if configured.

        Parameters
        ----------
        book_type : str
            One of SUPPORTED_BOOK_TYPES.

        Returns
        -------
        Optional[str]
            The full Canva edit URL, or None if not set.
        """
        key = _BOOK_TYPE_TEMPLATE_KEYS.get(book_type)
        if key is None:
            return None
        url = self._template_urls.get(key)
        return url if url else None

    def has_template(self, book_type: str) -> bool:
        """Check if a template URL is configured for the given book type."""
        return self.get_template_url(book_type) is not None

    def is_connect_configured(self) -> bool:
        """Check whether OAuth credentials are set (enables upload)."""
        return bool(self._client_id and self._client_secret)

    def upload_asset(
        self,
        file_path: str,
        name: str = "",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Upload an image asset to the user's Canva library via Connect API.

        Requires OAuth credentials + a valid access token.

        Parameters
        ----------
        file_path : str
            Local path to the image file.
        name : str
            Display name for the asset in Canva.
        tags : List[str], optional
            Tags for organizing the asset.

        Returns
        -------
        Dict[str, Any]
            Response from the Connect API containing the asset id and metadata.

        Raises
        ------
        RuntimeError
            If OAuth is not configured or the upload fails.
        """
        if not self.is_connect_configured():
            raise RuntimeError(
                "Canva OAuth not configured. Set CANVA_CLIENT_ID and "
                "CANVA_CLIENT_SECRET in config.ini [Canva] section."
            )

        token = self._ensure_token()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Asset file not found: {file_path}")

        if not name:
            name = path.stem

        url = f"{_CONNECT_API_BASE}/v1/assets/uploads/jobs"
        headers = {"Authorization": f"Bearer {token}"}

        # Use multipart upload via the Connect API
        with path.open("rb") as fh:
            files = {"file": (path.name, fh, self._mime_type(path))}
            data = {"name": name}
            if tags:
                data["tags"] = json.dumps(tags)

            resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Canva asset upload failed (HTTP {resp.status_code}): "
                f"{resp.text}"
            )

        result = resp.json()
        # The Connect API returns an async job; poll until complete
        job_id = result.get("job", {}).get("id", "")
        if job_id:
            return self._poll_job(job_id, token)
        return result

    def upload_asset_from_url(
        self,
        url: str,
        name: str = "",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Upload an asset from a publicly accessible URL.

        Parameters
        ----------
        url : str
            Public URL of the image to upload.
        name : str
            Display name for the asset.
        tags : List[str], optional
            Tags for organizing.

        Returns
        -------
        Dict[str, Any]
            Upload job result.
        """
        if not self.is_connect_configured():
            raise RuntimeError("Canva OAuth not configured.")

        token = self._ensure_token()
        api_url = f"{_CONNECT_API_BASE}/v1/assets/uploads/url"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {"url": url}
        if name:
            payload["name"] = name
        if tags:
            payload["tags"] = tags

        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Canva URL asset upload failed (HTTP {resp.status_code}): "
                f"{resp.text}"
            )
        result = resp.json()
        job_id = result.get("job", {}).get("id", "")
        if job_id:
            return self._poll_job(job_id, token)
        return result

    # ------------------------------------------------------------------
    # Internal: config loading
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        """Read Canva settings from config.ini using the key=value parser."""
        ini_path = self._config_path
        if not ini_path.exists():
            return

        section = "Canva"
        in_section = False
        for line in ini_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(";") or stripped.startswith("#"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                in_section = stripped[1:-1].strip() == section
                continue
            if not in_section:
                continue
            if "=" not in stripped:
                continue
            key, _, val = stripped.partition("=")
            key = key.strip().upper()
            val = val.strip().strip("\"'")
            if not val:
                continue

            if key in _BOOK_TYPE_TEMPLATE_KEYS.values():
                self._template_urls[key] = val
            elif key == "CANVA_CLIENT_ID":
                self._client_id = val
            elif key == "CANVA_CLIENT_SECRET":
                self._client_secret = val

        # Fallback to env vars
        if not self._client_id:
            self._client_id = os.getenv("CANVA_CLIENT_ID", "")
        if not self._client_secret:
            self._client_secret = os.getenv("CANVA_CLIENT_SECRET", "")

    # ------------------------------------------------------------------
    # Internal: OAuth2 token management
    # ------------------------------------------------------------------

    def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        return self._authenticate()

    def _authenticate(self) -> str:
        """Obtain or refresh an OAuth2 token via client credentials grant."""
        if self._refresh_token:
            return self._refresh_access_token()

        url = "https://api.canva.com/rest/v1/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        resp = requests.post(url, data=data, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Canva OAuth failed (HTTP {resp.status_code}): {resp.text}"
            )
        body = resp.json()
        self._access_token = body.get("access_token", "")
        expires_in = body.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in - 60
        self._refresh_token = body.get("refresh_token", "")
        return self._access_token

    def _refresh_access_token(self) -> str:
        url = "https://api.canva.com/rest/v1/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": self._refresh_token,
        }
        resp = requests.post(url, data=data, timeout=30)
        if resp.status_code != 200:
            self._refresh_token = ""
            return self._authenticate()
        body = resp.json()
        self._access_token = body.get("access_token", "")
        expires_in = body.get("expires_in", 3600)
        self._token_expires_at = time.time() + expires_in - 60
        new_refresh = body.get("refresh_token", "")
        if new_refresh:
            self._refresh_token = new_refresh
        return self._access_token

    # ------------------------------------------------------------------
    # Internal: job polling
    # ------------------------------------------------------------------

    def _poll_job(self, job_id: str, token: str, max_retries: int = 30) -> Dict[str, Any]:
        """Poll an async job until completion or failure."""
        url = f"{_CONNECT_API_BASE}/v1/assets/uploads/jobs/{job_id}"
        headers = {"Authorization": f"Bearer {token}"}

        for _ in range(max_retries):
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Job polling failed (HTTP {resp.status_code}): {resp.text}"
                )
            body = resp.json()
            status = body.get("job", {}).get("status", "")
            if status == "completed":
                return body
            if status in ("failed", "cancelled"):
                error = body.get("job", {}).get("error", "Unknown error")
                raise RuntimeError(f"Canva upload job {status}: {error}")
            time.sleep(2)

        raise TimeoutError(f"Canva upload job {job_id} did not complete in time.")

    @staticmethod
    def _mime_type(path: Path) -> str:
        ext = path.suffix.lower()
        return {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }.get(ext, "application/octet-stream")


# ---------------------------------------------------------------------------
# Module-level convenience helpers (used directly by dashboard)
# ---------------------------------------------------------------------------

_canva: Optional[CanvaIntegration] = None


def _get_canva() -> CanvaIntegration:
    global _canva
    if _canva is None:
        _canva = CanvaIntegration()
    return _canva


def get_template_url(book_type: str) -> Optional[str]:
    """Convenience: get the Canva template URL for a book type."""
    return _get_canva().get_template_url(book_type)


def has_template(book_type: str) -> bool:
    """Convenience: check if a template URL is configured."""
    return _get_canva().has_template(book_type)


def is_configured() -> bool:
    """Check if any Canva integration (templates or Connect) is configured."""
    c = _get_canva()
    return bool(c._template_urls) or c.is_connect_configured()


def upload_asset(file_path: str, name: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience: upload an asset to Canva."""
    return _get_canva().upload_asset(file_path, name, tags)


def upload_asset_from_url(url: str, name: str = "", tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience: upload an asset from a URL to Canva."""
    return _get_canva().upload_asset_from_url(url, name, tags)


# ===========================================================================
# Canva Automated Design Engine
# ===========================================================================

# Standard KDP trim sizes (width x height in inches)
KDP_TRIM_SIZES: Dict[str, Dict[str, float]] = {
    "6x9": {"width": 6.0, "height": 9.0},
    "6.14x9.21": {"width": 6.14, "height": 9.21},
    "7.5x9.25": {"width": 7.5, "height": 9.25},
    "8.5x11": {"width": 8.5, "height": 11.0},
    "8.25x6": {"width": 8.25, "height": 6.0},  # landscape
}

# Page placement descriptors for the Design Manifest
_PLACEMENT_SUGGESTIONS: List[str] = [
    "Cover — Full Front",
    "Cover — Full Back",
    "Interior — Left Page (Verso)",
    "Interior — Right Page (Recto)",
    "Interior — Full Spread",
    "Interior — Chapter Header",
    "Interior — Section Divider",
]


def build_new_design_url(
    width: float = 8.5,
    height: float = 11.0,
    unit: str = "in",
) -> str:
    """Build a Canva URL that opens the editor with custom dimensions.

    The resulting URL opens a blank Canva design canvas pre-sized to the
    given dimensions — ready for drag-and-drop composition.

    Parameters
    ----------
    width : float
        Page width in *unit* (default 8.5 inches for KDP letter size).
    height : float
        Page height in *unit* (default 11.0 inches).
    unit : str
        Unit of measurement (default "in" for inches). Canva also supports
        "px", "mm", "cm".

    Returns
    -------
    str
        Fully formed Canva URL, e.g.:
        https://www.canva.com/design/new?width=8.5in&height=11in
    """
    w = f"{width}{unit}" if not str(width).endswith(unit) else str(width)
    h = f"{height}{unit}" if not str(height).endswith(unit) else str(height)
    return f"https://www.canva.com/design/new?width={w}&height={h}"


def build_kdp_design_url(trim_size: str = "8.5x11") -> str:
    """Shortcut: build a Canva new-design URL for a standard KDP trim size.

    Parameters
    ----------
    trim_size : str
        One of the keys in KDP_TRIM_SIZES (e.g. "8.5x11", "6x9").

    Returns
    -------
    str
        Canva URL with pre-set KDP dimensions.
    """
    dims = KDP_TRIM_SIZES.get(trim_size, KDP_TRIM_SIZES["8.5x11"])
    return build_new_design_url(dims["width"], dims["height"])


def build_canva_template_url(
    template_id: str,
    elements: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Build a URL to open a specific Canva template for editing.

    Canva does not support programmatic element placement via URL parameters,
    but the resulting edit URL allows the user to open the template and
    manually arrange AI-generated images using the Design Manifest as a guide.

    Parameters
    ----------
    template_id : str
        The Canva template ID (the long hash from a design URL).
        Extract from: https://www.canva.com/design/{template_id}/edit
    elements : List[Dict[str, str]], optional
        Not directly supported in Canva URL scheme, but included for future
        extensibility. Each dict can carry metadata like:
            {"slot": "Left Page", "image_url": "...", "notes": "..."}

    Returns
    -------
    str
        Canva template edit URL.
    """
    base = f"https://www.canva.com/design/{template_id}/edit"
    # If elements are provided, encode them as a JSON fragment for reference
    if elements:
        import urllib.parse
        manifest = urllib.parse.quote(json.dumps(elements, ensure_ascii=False))
        base += f"?manifest={manifest}"
    return base


def get_kdp_trim_sizes() -> List[str]:
    """Return list of available KDP trim size keys for UI dropdowns."""
    return sorted(KDP_TRIM_SIZES.keys())


def get_placement_suggestions() -> List[str]:
    """Return list of page placement descriptors for the manifest."""
    return list(_PLACEMENT_SUGGESTIONS)


# ---------------------------------------------------------------------------
# Design Manifest — CSV-based bulk image placement guide
# ---------------------------------------------------------------------------

import csv as _csv
from io import StringIO as _StringIO


def generate_design_manifest(
    image_entries: List[Dict[str, str]],
    book_title: str = "",
    trim_size: str = "8.5x11",
) -> str:
    """Generate a CSV "Design Manifest" that guides the user in placing AI-
    generated images into their Canva template.

    The CSV is structured for readability and includes columns for:
      - Image URL or file path
      - Page number
      - Placement suggestion (e.g. "Left Page", "Right Page", "Cover")
      - Notes / instructions

    Parameters
    ----------
    image_entries : List[Dict[str, str]]
        Each entry should have keys:
          - "image" : URL or file path to the AI-generated image
          - "page"  : page number (optional, defaults to sequential)
          - "placement" : placement suggestion (optional)
          - "notes" : additional notes (optional)
    book_title : str
        Title of the book (used in the manifest header).
    trim_size : str
        KDP trim size key (e.g. "8.5x11").

    Returns
    -------
    str
        CSV content as a string, ready for download or display.
    """
    output = _StringIO()
    writer = _csv.writer(output)

    # Header rows (informational)
    writer.writerow(["# KDP Design Manifest — Canva Placement Guide"])
    if book_title:
        writer.writerow(["# Book:", book_title])
    writer.writerow(["# Trim Size:", trim_size])
    writer.writerow(["# Generated by: KDP Discovery Engine Pro"])
    writer.writerow(["#"])
    writer.writerow(
        [
            "# Instructions: For each image, open the Canva template, "
            "drag the image onto the canvas,"
        ]
    )
    writer.writerow(
        [
            "#               position it according to the 'Placement' "
            "column, and adjust as needed."
        ]
    )
    writer.writerow(["#"])
    writer.writerow(["# --- END HEADER ---"])

    # Data columns
    writer.writerow(["Page", "Image URL / Path", "Placement", "Notes"])

    for i, entry in enumerate(image_entries, start=1):
        page = entry.get("page", str(i))
        image = entry.get("image", "")
        placement = entry.get("placement", "Interior — Full Page")
        notes = entry.get("notes", "")
        writer.writerow([page, image, placement, notes])

    # Footer
    writer.writerow([])
    writer.writerow(["# Tip: Use the 'Auto-Setup Canva Project' button in "
                     "Design Studio to open Canva with correct dimensions."])
    writer.writerow(["# Tip: Upload all images to Canva via "
                     "Uploads > Upload Files, then drag them onto pages."])

    return output.getvalue()


def generate_image_entries_from_prompts(
    niche: str,
    num_pages: int = 10,
    image_urls: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """Build a list of image entries ready for the Design Manifest.

    Useful when the user has generated AI prompts and needs to plan
    their Canva layout.

    Parameters
    ----------
    niche : str
        The book niche (used in notes).
    num_pages : int
        Number of interior pages (default 10).
    image_urls : List[str], optional
        List of image URLs/paths. If shorter than num_pages, entries
        without URLs get a placeholder note.

    Returns
    -------
    List[Dict[str, str]]
        image_entries list ready for generate_design_manifest().
    """
    entries: List[Dict[str, str]] = []

    # Cover pages
    entries.append({
        "page": "Cover",
        "image": image_urls[0] if image_urls else "[Cover image]",
        "placement": "Cover — Full Front",
        "notes": f"Front cover for {niche}",
    })
    if image_urls and len(image_urls) > 1:
        entries.append({
            "page": "Back",
            "image": image_urls[1],
            "placement": "Cover — Full Back",
            "notes": "Back cover (optional)",
        })
        url_offset = 2
    else:
        url_offset = 1

    # Interior pages (alternating left/right)
    for i in range(1, num_pages + 1):
        side = "Right Page (Recto)" if i % 2 == 1 else "Left Page (Verso)"
        idx = url_offset + i - 1
        img = image_urls[idx] if image_urls and idx < len(image_urls) else "[AI-generated image]"
        entries.append({
            "page": str(i),
            "image": img,
            "placement": f"Interior — {side}",
            "notes": f"Page {i} — {niche}",
        })

    return entries
