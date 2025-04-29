import os
from dotenv import load_dotenv
from prefect import flow, get_run_logger
from src.tasks import scan_directory, classify_image_with_gemini, move_file

# pull in GOOGLE_API_KEY from .env
load_dotenv()

@flow(name="Image Classification and Sorting Flow")
def image_classification_flow(
    input_dir: str = "photos_input",
    output_dir: str = "photos_output",
):
    logger = get_run_logger()
    api_key = os.getenv("GOOGLE_API_KEY")

    # 1) scan for images
    image_paths = scan_directory(input_dir)
    if not image_paths:
        logger.info(f"No images found in {input_dir}")
        return

    results = []
    # 2) sequentially classify → move
    for img_path in image_paths:
        # classify (this already sleeps 4 s under the hood)
        classification = classify_image_with_gemini(img_path, api_key)
        # move into the right folder
        move_res = move_file(img_path, output_dir, classification)
        results.append(move_res)

    # 3) summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed     = len(results) - successful
    logger.info(f"Flow finished. Moved {successful}; skipped/failed {failed}.")

if __name__ == "__main__":
    image_classification_flow.serve(
        name="sort-images",
        parameters={"input_dir": "photos_input", "output_dir": "photos_output"},
    )

