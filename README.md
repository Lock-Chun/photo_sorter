# Gemini Photo Sorter

## Overview

**Gemini Photo Sorter** is a Prefect-based pipeline that:

1. **Scans** an input directory for image files.
2. **Classifies** each image using the Google Gemini Vision API.  
3. **Moves** the file into a subfolder named after its classification.

It enforces Google’s rate limits (≤15 requests/minute) by processing images sequentially with a built‑in delay.

## Architecture Diagram

```mermaid
flowchart LR
  subgraph Input
    A[photos_input/]
  end
  A --> B[Scan Directory Task]
  B --> C[Classify Image Task]
  C --> D{Rate Limit Enforcement}
  D -- Within Limit --> E[Move File Task]
  D -- Throttled --> F[Sleep 4s]
  F --> C
  E --> G[photos_output/<classification>/]
```

## Prerequisites

- Docker & Docker Compose
- A Google Cloud API key with Gemini Vision enabled
- Prefect 3.x installed (comes via image)

## Setup & Running

1. **Add your key** to a top‑level `.env`:
   ```env
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Build & start** the container:
   ```bash
   docker-compose up --build -d
   ```

3. **Run** the sorting flow:
   ```bash
   docker-compose exec app prefect deployment run "Image Classification and Sorting Flow/sort-images"
   ```

   Or, to run locally without Docker:
   ```bash
   cd src
   python flow.py
   ```

## Design & Development Process

### 1. Initial Prototype
- **Tasks** implemented in `src/tasks.py`:  
  - `scan_directory` to list image files.  
  - `classify_image_with_gemini` to call Gemini Vision and parse the result.  
  - `move_file` to relocate images into classification folders.
- **Flow** in `src/flow.py` used Prefect’s `.map()` for parallelism.

### 2. Quota & Concurrency
- Hitting Gemini’s **15 requests/minute** free‑tier quota caused 429 errors.
- **Sequential Processing**: Switched to a plain Python `for` loop, invoking classification one‐by‐one.
- **Built‑in Delay**: Kept a `time.sleep(4)` inside the classification task to space calls at roughly 15/minute.

## Tech Stack

- **Python 3.11**: Core scripting language, chosen for its modern features and Prefect compatibility.
- **Prefect 3.x**: Orchestration framework that provides an elegant API for defining tasks and flows, and makes sequential execution straightforward.
- **Docker & Docker Compose**: Ensures consistent runtime environments and simplifies deployment and testing.
- **Google Gemini Vision API**: Provides powerful, pre-trained image classification; rate-limiting was a core design consideration.
- **Pillow (PIL)**: Lightweight library for image validation and basic processing.
- **python-dotenv**: Securely loads environment variables from a `.env` file.
- **Pathlib & Shutil**: Standard library modules for filesystem operations (scanning directories, moving files).

---

