"""
design_engine.py — Design Intelligence Studio for KDP Discovery Engine Pro

Provides:
  - Unified AI art prompt generation (Midjourney / Stable Diffusion)
  - Google Imagen image generation (actual image output)
  - Cover description generator
  - External tool links (Creative Fabrica, Canva, Amazon)
  - Optional OpenAI prompt enhancement

Author: KDP Automation Architect
"""

import os
import json
import logging
import base64
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("kdpdesign")

# ---------------------------------------------------------------------------
# Unified Style Templates — single source of truth
# ---------------------------------------------------------------------------

_STYLE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Coloring Book": {
        "mj_style": "black and white line art coloring book style, clean bold outlines, white background, high contrast, intricate details",
        "sd_style": "black and white line art, coloring book page, clean outlines, no shading, white background, high contrast",
        "cover_suffix": "vibrant full-color cover design, professional book cover, 3D rendering, Amazon bestseller style",
    },
    "Planner": {
        "mj_style": "clean minimalist planner design, elegant layout, pastel color palette, organized grid structure, bullet journal style",
        "sd_style": "planner layout design, clean lines, organized grid, minimalist, pastel colors, bullet journal aesthetic",
        "cover_suffix": "professional planner cover design, elegant typography, spiral binding mockup, lifestyle photography",
    },
    "Sketch Book": {
        "mj_style": "blank sketchbook style, textured paper background, minimal design, artistic, creative space, soft shadows",
        "sd_style": "blank sketchbook, textured paper texture, minimal design, artistic, creative workspace",
        "cover_suffix": "premium sketchbook cover design, artistic, canvas texture, professional book cover mockup",
    },
    "Journal": {
        "mj_style": "elegant journal design, vintage aesthetic, decorative borders, sophisticated patterns, gold foil accents",
        "sd_style": "journal design, vintage style, decorative borders, elegant patterns, gold accents, sophisticated",
        "cover_suffix": "luxury journal cover design, gold foil details, embossed leather texture, ribbon bookmark mockup",
    },
    "Workbook": {
        "mj_style": "clean educational workbook design, modern layout, playful colors, activity page style, kid-friendly",
        "sd_style": "workbook page design, clean layout, educational style, activity worksheet, colorful, engaging",
        "cover_suffix": "educational workbook cover design, bright colors, engaging layout, school supplies style mockup",
    },
    "Activity Book": {
        "mj_style": "fun activity book design, colorful illustrations, game-style layout, mazes and puzzles, children's book aesthetic",
        "sd_style": "activity book page, colorful, game layout, puzzles, mazes, dot-to-dot, children's illustration style",
        "cover_suffix": "exciting activity book cover, bright rainbow colors, playful typography, 3D toy-like mockup",
    },
}

_AGE_DESCRIPTORS: Dict[str, str] = {
    "Toddlers (1-3)": "extra large simple shapes, very thick lines, minimal details, baby-safe rounded edges",
    "Preschool (3-5)": "large simple shapes, thick lines, basic patterns, recognizable objects, friendly characters",
    "Kids (5-8)": "moderate detail, fun characters, clear distinct areas, age-appropriate themes, educational elements",
    "Tweens (8-12)": "more intricate details, fashion-forward, sophisticated patterns, trending themes, moderate complexity",
    "Teens (13-17)": "intricate designs, zentangle-inspired, aesthetic patterns, trending social media themes, detailed",
    "Adults (18+)": "highly intricate details, zentangle and mandala patterns, sophisticated themes, professional-grade",
    "Seniors (65+)": "large print, easy-to-see lines, simple shapes, familiar themes, low-vision accessible, relaxing",
}

_COMPLEXITY_DESCRIPTORS: Dict[str, str] = {
    "Simple": "simple designs, few elements, large open spaces, easy to complete, minimal detail",
    "Moderate": "balanced complexity, medium detail, mix of simple and intricate areas, engaging",
    "Detailed": "highly detailed, many small elements, intricate patterns, challenging and rewarding",
    "Extreme": "ultra-detailed, microscopic patterns, zentangle-level complexity, hundreds of elements",
}

_ASPECT_RATIOS: Dict[str, str] = {
    "Coloring Book": "--ar 8.5:11",
    "Planner": "--ar 8.5:11",
    "Sketch Book": "--ar 8.5:11",
    "Journal": "--ar 8.5:11",
    "Workbook": "--ar 8.5:11",
    "Activity Book": "--ar 8.5:11",
}

_DEFAULT_MJ_PARAMS = "--v 6.0 --style expressive --s 250"
_DEFAULT_SD_PARAMS = "--ar 8.5:11"

# Imagen pricing per image (USD)
_IMAGEN_PRICE_PER_IMAGE = 0.020

# ---------------------------------------------------------------------------
# Public API — Prompt Generation
# ---------------------------------------------------------------------------


def generate_prompt(
    niche: str,
    age_group: str = "Adults (18+)",
    style: str = "Coloring Book",
    complexity: str = "Moderate",
    platform: str = "midjourney",
    interior_page: bool = True,
) -> Dict[str, str]:
    """Construct a highly-optimized AI art prompt.

    Parameters
    ----------
    niche : str
        Target niche (e.g. "yoga anatomy", "keto cookbook").
    age_group : str
        One of _AGE_DESCRIPTORS keys.
    style : str
        One of _STYLE_TEMPLATES keys.
    complexity : str
        One of _COMPLEXITY_DESCRIPTORS keys.
    platform : str
        'midjourney', 'stablediffusion', or 'imagen'.
    interior_page : bool
        True for interior page prompt, False for cover prompt.

    Returns
    -------
    Dict[str, str]
        {platform, prompt, params, full_prompt, cover_prompt, cost_estimate}
    """
    tmpl = _STYLE_TEMPLATES.get(style, _STYLE_TEMPLATES["Coloring Book"])
    age_desc = _AGE_DESCRIPTORS.get(age_group, _AGE_DESCRIPTORS["Adults (18+)"])
    comp_desc = _COMPLEXITY_DESCRIPTORS.get(complexity, _COMPLEXITY_DESCRIPTORS["Moderate"])
    aspect = _ASPECT_RATIOS.get(style, "--ar 8.5:11")

    if interior_page:
        if platform == "imagen":
            base_style = tmpl.get("sd_style", tmpl["mj_style"])
        else:
            base_style = tmpl["mj_style" if platform == "midjourney" else "sd_style"]
        prompt = f"{niche}, {base_style}, {comp_desc}, {age_desc}"
    else:
        base_style = tmpl["cover_suffix"]
        prompt = f"{niche} book cover, {base_style}, {comp_desc}, professional publishing"

    if platform == "midjourney":
        params = f"{aspect} {_DEFAULT_MJ_PARAMS}"
    elif platform == "stablediffusion":
        params = f"{aspect} {_DEFAULT_SD_PARAMS}"
    else:
        params = ""

    full_prompt = f"{prompt} {params}".strip()
    cover_prompt = f"{niche} book cover, {tmpl['cover_suffix']}, {comp_desc}, professional book cover design".strip()

    return {
        "platform": platform,
        "prompt": prompt,
        "params": params,
        "full_prompt": full_prompt,
        "cover_prompt": cover_prompt,
        "style": style,
        "age_group": age_group,
        "complexity": complexity,
        "cost_estimate": _IMAGEN_PRICE_PER_IMAGE if platform == "imagen" else 0,
    }


def generate_cover_description(niche: str, age_group: str = "Adults (18+)", style: str = "Coloring Book") -> str:
    """Generate a human-readable cover description suitable for KDP upload."""
    tmpl = _STYLE_TEMPLATES.get(style, _STYLE_TEMPLATES["Coloring Book"])
    age_key = age_group.split(" ")[0].lower() if age_group else "adult"

    return (
        f"A beautiful {'cover design for a ' + style.lower() if style else ''} book about {niche}. "
        f"Designed for {age_group.lower() if age_group else 'all ages'}, "
        f"this cover features {tmpl['cover_suffix'].replace('pro', '').strip()} "
        f"with elegant typography and a clean layout. "
        f"The design is optimized for Amazon KDP thumbnail visibility "
        f"and appeals to {age_key}s interested in {niche}."
    )


# ---------------------------------------------------------------------------
# Google Imagen — Actual Image Generation
# ---------------------------------------------------------------------------

IMAGEN_ENDPOINTS = {
    "imagen-3.0-generate-001": "https://us-central1-aiplatform.googleapis.com/v1/projects/{project}/locations/us-central1/publishers/google/models/imagen-3.0-generate-001:predict",
    "imagen-3.0-fast": "https://us-central1-aiplatform.googleapis.com/v1/projects/{project}/locations/us-central1/publishers/google/models/imagen-3.0-fast:predict",
}

IMAGEN_ASPECT_RATIOS = {
    "1:1": {"width": 1024, "height": 1024},
    "3:4": {"width": 768, "height": 1024},
    "4:3": {"width": 1024, "height": 768},
    "9:16": {"width": 576, "height": 1024},
    "16:9": {"width": 1024, "height": 576},
}


def generate_image(
    prompt: str,
    api_key: str,
    project: str,
    model: str = "imagen-3.0-generate-001",
    sample_count: int = 1,
    aspect_ratio: str = "1:1",
    safety_filter_level: str = "block_some",
) -> Optional[Dict[str, Any]]:
    """Generate one or more images via Google Imagen API.

    Parameters
    ----------
    prompt : str
        Text prompt for image generation.
    api_key : str
        Google Cloud API key.
    project : str
        Google Cloud project ID.
    model : str
        Imagen model name (default: imagen-3.0-generate-001).
    sample_count : int
        Number of images to generate (1-4, default: 1).
    aspect_ratio : str
        One of IMAGEN_ASPECT_RATIOS keys (default: 1:1).
    safety_filter_level : str
        'block_some' or 'block_few' (default: block_some).

    Returns
    -------
    Optional[Dict[str, Any]]
        {images: list of base64 strings, mime_type, prompt,
         cost, model} or None on failure.
    """
    endpoint = IMAGEN_ENDPOINTS.get(model)
    if not endpoint:
        logger.error(f"Unknown Imagen model: {model}")
        return None

    url = endpoint.format(project=project)
    aspect = IMAGEN_ASPECT_RATIOS.get(aspect_ratio, IMAGEN_ASPECT_RATIOS["1:1"])

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": min(max(sample_count, 1), 4),
            "aspectRatio": aspect_ratio,
        },
    }

    for attempt in range(1, 4):
        try:
            import requests
            resp = requests.post(
                f"{url}?key={api_key}",
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                images = []
                for pred in predictions:
                    b64 = pred.get("bytesBase64Encoded")
                    if b64:
                        images.append(b64)

                cost = len(images) * _IMAGEN_PRICE_PER_IMAGE
                logger.info(
                    "Imagen generated %d image(s) for $%.3f",
                    len(images), cost,
                )
                return {
                    "images": images,
                    "mime_type": predictions[0].get("mimeType", "image/png") if predictions else "image/png",
                    "prompt": prompt,
                    "count": len(images),
                    "cost": cost,
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                }
            else:
                err = resp.text[:500]
                logger.warning(
                    "Imagen attempt %d/3 failed (%d): %s",
                    attempt, resp.status_code, err,
                )
                if attempt < 3:
                    time.sleep(2 ** attempt)
        except ImportError:
            logger.error("requests library not installed. Run: pip install requests")
            return {"error": "requests library not found. Run: pip install requests"}
        except Exception as exc:
            logger.warning("Imagen attempt %d/3 exception: %s", attempt, exc)
            if attempt < 3:
                time.sleep(2 ** attempt)

    logger.error("All Imagen attempts exhausted")
    return None


def generate_images_batch(
    prompts: List[str],
    api_key: str,
    project: str,
    model: str = "imagen-3.0-generate-001",
    aspect_ratio: str = "1:1",
    delay: float = 2.0,
    progress_callback: Optional[callable] = None,
) -> List[Dict[str, Any]]:
    """Generate images for multiple prompts sequentially.

    Parameters are same as generate_image() but prompts is a list.
    Returns list of result dicts, one per prompt.
    """
    results: List[Dict[str, Any]] = []
    total_cost = 0.0

    for i, prompt in enumerate(prompts):
        logger.info("Batch image %d/%d: '%s'", i + 1, len(prompts), prompt[:60])
        result = generate_image(
            prompt=prompt,
            api_key=api_key,
            project=project,
            model=model,
            sample_count=1,
            aspect_ratio=aspect_ratio,
        )
        if result and "images" in result:
            results.append(result)
            total_cost += result.get("cost", 0)
        else:
            results.append({"prompt": prompt, "error": "Generation failed", "count": 0, "cost": 0})

        if progress_callback:
            progress_callback(i + 1, len(prompts))

        if i < len(prompts) - 1:
            time.sleep(delay)

    logger.info(
        "Batch complete: %d/%d images generated, total cost $%.3f",
        len([r for r in results if r.get("count", 0) > 0]),
        len(prompts),
        total_cost,
    )
    return results


def estimate_image_cost(
    image_count: int,
    model: str = "imagen-3.0-generate-001",
) -> Dict[str, Any]:
    """Estimate cost for generating N images.

    Returns dict with count, unit_price, total_cost, model.
    """
    total = image_count * _IMAGEN_PRICE_PER_IMAGE
    return {
        "count": image_count,
        "unit_price": _IMAGEN_PRICE_PER_IMAGE,
        "total_cost": round(total, 4),
        "model": model,
        "credits_needed": total * 1000,
    }


# ---------------------------------------------------------------------------
# External Tool Links
# ---------------------------------------------------------------------------


def build_creative_fabrica_link(keywords: str) -> Dict[str, str]:
    """Generate a clickable search link for Creative Fabrica."""
    query = keywords.strip().replace(" ", "%20")
    return {
        "url": f"https://www.creativefabrica.com/search/?q={query}",
        "label": "Search Creative Fabrica",
        "description": "Find graphics, fonts, and templates for your book design",
    }


def build_canva_link(keywords: str) -> Dict[str, str]:
    """Generate a clickable search link for Canva templates."""
    query = keywords.strip().replace(" ", "+")
    return {
        "url": f"https://www.canva.com/search/templates?q={query}",
        "label": "Search Canva Templates",
        "description": "Find pre-made templates for book covers and interiors",
    }


def build_amazon_link(keywords: str) -> Dict[str, str]:
    """Generate a search link for best-selling books on Amazon."""
    query = keywords.strip().replace(" ", "+")
    return {
        "url": f"https://www.amazon.com/s?k={query}&ref=nb_sb_noss",
        "label": "Search Amazon Bestsellers",
        "description": "See top-selling books in this niche for design inspiration",
    }


# ---------------------------------------------------------------------------
# OpenAI Integration (optional)
# ---------------------------------------------------------------------------


def generate_with_openai(
    system_prompt: str,
    user_message: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int = 500,
) -> Optional[Dict[str, Any]]:
    """Send a prompt to OpenAI and return the response.

    Parameters
    ----------
    system_prompt : str
        System-level instruction.
    user_message : str
        User message content.
    api_key : str
        OpenAI API key.
    model : str
        Model name (default: gpt-4o-mini).
    temperature : float
        Creativity level (0.0-1.0).
    max_tokens : int
        Maximum response tokens.

    Returns
    -------
    Optional[Dict[str, Any]]
        {role, content, model, usage} or None on failure.
    """
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            logger.error("OpenAI API error %s: %s", resp.status_code, resp.text)
            return {"error": f"API error {resp.status_code}: {resp.text}", "role": "assistant", "content": ""}

        data = resp.json()
        choice = data["choices"][0]
        return {
            "role": choice["message"]["role"],
            "content": choice["message"]["content"],
            "model": data["model"],
            "usage": data.get("usage", {}),
        }
    except ImportError:
        logger.warning("requests not installed — cannot call OpenAI API")
        return {"error": "requests library not installed. Run: pip install requests", "role": "assistant", "content": ""}
    except Exception as exc:
        logger.error("OpenAI call failed: %s", exc)
        return {"error": str(exc), "role": "assistant", "content": ""}


# ---------------------------------------------------------------------------
# Dropdown helpers
# ---------------------------------------------------------------------------


def get_style_options() -> List[str]:
    """Return list of available book styles."""
    return sorted(_STYLE_TEMPLATES.keys())


def get_age_options() -> List[str]:
    """Return list of available age groups."""
    return list(_AGE_DESCRIPTORS.keys())


def get_complexity_options() -> List[str]:
    """Return list of available complexity levels."""
    return list(_COMPLEXITY_DESCRIPTORS.keys())


def get_imagen_models() -> List[str]:
    """Return list of available Imagen models."""
    return list(IMAGEN_ENDPOINTS.keys())


def get_imagen_aspect_ratios() -> List[str]:
    """Return list of available aspect ratios for Imagen."""
    return list(IMAGEN_ASPECT_RATIOS.keys())
