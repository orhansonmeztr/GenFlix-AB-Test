import pandas as pd
import json
from pathlib import Path
from tqdm import tqdm
import time

from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, GEMINI_MODEL

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "netflix_titles_CLEANED.csv"
TEMP_DIR = BASE_DIR / "data" / "temp"
REQUESTS_FILE_PATH = TEMP_DIR / "batch_requests.jsonl"
JOB_STATE_FILE_PATH = TEMP_DIR / "batch_job_state.json"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "generated_synopses.csv"

NUM_SAMPLES = 1000

PROMPT_TEMPLATE = """
You are a witty and engaging storyteller. Your task is to rewrite a movie synopsis to make it more exciting and appealing, like a friend recommending a must-see film.

Focus on the hook and the emotional core, not just the plot points. Keep it concise (under 50 words).

Original Title: {title}
Original Synopsis: {description}

Your Engaging Synopsis:
"""

def prepare_and_submit_batch():
    """
    Prepares a JSONL file with generation requests and submits it as a batch job.
    """

    if PROCESSED_DATA_PATH.exists():
        print(f"--> Final output file already exists at: {PROCESSED_DATA_PATH}")
        print("--> Skipping batch job submission to avoid overwriting.")
        print("--> To re-run the generation, please manually delete this file first.")
        return

    print("--- Step 1: Preparing Batch Requests ---")

    # 1. Load and sample data
    try:
        df = pd.read_csv(RAW_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Raw data file not found at {RAW_DATA_PATH}")
        print("Please follow the instructions in README.md to download the dataset.")
        return
        
    movies_df = df[df['type'] == 'Movie'].dropna(subset=['description']).copy()
    
    sample_count = min(NUM_SAMPLES, len(movies_df))
    if sample_count < NUM_SAMPLES:
        print(f"Warning: Requested {NUM_SAMPLES} samples, but only {sample_count} movies are available.")
        
    sampled_df = movies_df.sample(n=sample_count, random_state=42)
    
    # 2. Create the JSONL request file
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(REQUESTS_FILE_PATH, "w") as f:
        for _, row in tqdm(sampled_df.iterrows(), total=len(sampled_df), desc="Preparing JSONL"):
            prompt = PROMPT_TEMPLATE.format(title=row['title'], description=row['description'])
            
            # Batch API format: {"key": "...", "request": {...}}
            request = {
                "key": row['show_id'],
                "request": {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
            }
            f.write(json.dumps(request) + "\n")
    
    print(f"Successfully created request file for {sample_count} titles at: {REQUESTS_FILE_PATH}")

    print("\n--- Step 2: Submitting Batch Job to API ---")
    
    # 3. Initialize client and upload the file
    client = genai.Client(api_key=GOOGLE_API_KEY)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    upload_display_name = f"genflix_requests_{timestamp}"
    
    print(f"Uploading request file with display name: '{upload_display_name}'...")
    uploaded_file = client.files.upload(
        file=REQUESTS_FILE_PATH,
        config=types.UploadFileConfig(display_name=upload_display_name, mime_type='application/json')
    )
    print(f"File uploaded successfully: {uploaded_file.name}")

    # 4. Create and submit the batch job
    job_display_name = f"genflix_batch_{timestamp}"
    print(f"Creating batch job with display name: '{job_display_name}'...")
    
    batch_job = client.batches.create(
        model=GEMINI_MODEL,
        src=uploaded_file.name,
        config={
            'display_name': job_display_name,
        },
    )
    print(f"Batch job '{job_display_name}' created successfully! Job Name: {batch_job.name}")

    # 5. Save the job name for the monitoring script
    with open(JOB_STATE_FILE_PATH, "w") as f:
        json.dump({'job_name': batch_job.name, 'display_name': job_display_name}, f)
        
    print(f"Job name saved to {JOB_STATE_FILE_PATH}")
    print("\n--- Submission Complete ---")
    print("You can now run 'python src/monitor_batch_job.py' to check the status and retrieve results when finished.")

if __name__ == "__main__":
    prepare_and_submit_batch()