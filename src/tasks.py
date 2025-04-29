import os
import shutil
import logging
from pathlib import Path
import google.generativeai as genai
from PIL import Image
from prefect import task, get_run_logger
import time

# Configure logging
def configure_logging():
    logging.basicConfig(level=logging.INFO)

MODEL_NAME = "gemini-1.5-flash"

@task(name="Scan Input Directory")
def scan_directory(input_dir: str) -> list[Path]:
    logger = get_run_logger()
    input_path = Path(input_dir)
    if not input_path.is_dir():
        logger.error(f"Input directory not found: {input_dir}")
        return []

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    logger.info(f"Found {len(image_files)} image files in {input_dir}.")
    return image_files

@task(name="Classify Image")
def classify_image_with_gemini(image_path: Path, api_key: str) -> str:
    """Classifies an image using Google Gemini Vision API with American-Chinese categories."""
    logger = get_run_logger()
    logger.info(f"Classifying {image_path.name}...")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    # Validate image
    try:
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)
    except Exception as e:
        logger.error(f"Invalid image {image_path.name}: {e}")
        return "invalid_image"

    # Improved prompt for American-Chinese food sorting
    prompt = (
        "You are classifying American-Chinese restaurant photos into specific categories. "
        "If the image shows any fried noodle dish (e.g., chow mein, lo mein), classify it as 'chaomien'. "
        "If it shows any rice dish (e.g., fried rice, white rice), classify it as 'rice'. "
        "If the image shows multiple distinct dishes together, classify it as 'whole_meal'. "
        "If it shows a single protein (e.g., beef, chicken, shrimp) without distinguishing base, classify by protein name (e.g., 'beef'). "
        "If the photo is of the restaurant exterior or interior (building), classify as 'building'. "
        "If the photo shows a menu, classify as 'menu'. "
        "Otherwise, if it does not match above categories (plants, random objects), classify as 'random-food', or random-non-food."
        "If unsure, respond with 'unsure'. "
        "Be concise, lowercase, and use underscores (e.g., 'chaomien', 'rice', 'beef')."
    )

    # Enforce rate limit: ~15 requests/minute
    time.sleep(4)

    try:
        response = model.generate_content([prompt, img])
        classification = response.text.strip().lower().replace(" ", "_").rstrip(".")
        if not classification:
            return "unsure"
        return classification
    except Exception as e:
        logger.error(f"Error classifying {image_path.name}: {e}")
        return "classification_error"

@task(name="Move Classified Image")
def move_file(source_path: Path, output_base_dir: str, classification: str) -> dict:
    logger = get_run_logger()
    if not classification:
        classification = "error_or_skipped"

    # Normalize folder name
    classification = classification.lower().rstrip("._ ")
    target_dir = Path(output_base_dir) / classification
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / source_path.name

    try:
        shutil.move(str(source_path), str(target_path))
        logger.info(f"Moved {source_path.name} to {target_path}")
        return {"source": str(source_path), "destination": str(target_path), "classification": classification, "status": "success"}
    except Exception as e:
        logger.error(f"Error moving {source_path.name}: {e}")
        return {"source": str(source_path), "destination": None, "classification": classification, "status": "failure"}
