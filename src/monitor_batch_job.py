import pandas as pd
import json
import time
from pathlib import Path

from google import genai

from config import GOOGLE_API_KEY

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "data" / "temp"
JOB_STATE_FILE_PATH = TEMP_DIR / "batch_job_state.json"
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "netflix_titles_CLEANED.csv"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed" / "generated_synopses.csv"

POLLING_INTERVAL_SECONDS = 60 

def monitor_and_retrieve_results():
    """
    Monitors a submitted batch job and retrieves the results upon completion.
    """

    if PROCESSED_DATA_PATH.exists():
        print(f"--> Final output file already exists at: {PROCESSED_DATA_PATH}")
        print("--> Skipping monitoring process.")
        return
    
    print("--- Starting Batch Job Monitor ---")

    # 1. Load the job name
    try:
        with open(JOB_STATE_FILE_PATH, "r") as f:
            job_name = json.load(f)['job_name']
        print(f"Monitoring job: {job_name}")
    except FileNotFoundError:
        print(f"Error: Job state file not found at {JOB_STATE_FILE_PATH}")
        print("Please run 'submit_batch_job.py' first.")
        return

    # 2. Initialize client and start polling
    client = genai.Client(api_key=GOOGLE_API_KEY)
    completed_states = {'JOB_STATE_SUCCEEDED', 'JOB_STATE_FAILED', 'JOB_STATE_CANCELLED', 'JOB_STATE_EXPIRED'}

    while True:
        batch_job = client.batches.get(name=job_name)
        current_state = batch_job.state.name
        
        if current_state in completed_states:
            print(f"\nJob finished with state: {current_state}")
            break
        
        print(f"Job not finished. Current state: {current_state}. Waiting {POLLING_INTERVAL_SECONDS} seconds...")
        time.sleep(POLLING_INTERVAL_SECONDS)

    # 3. Process the results
    if batch_job.state.name == 'JOB_STATE_SUCCEEDED':
        print("Job succeeded! Retrieving results...")
        
        # Results are in an output file
        result_file_name = batch_job.dest.file_name
        print(f"Downloading result file: {result_file_name}")
        file_content_bytes = client.files.download(file=result_file_name)
        
        # Decode and parse the JSONL output
        results_str = file_content_bytes.decode('utf-8')
        result_lines = results_str.strip().split('\n')
        
        results_map = {}
        for line in result_lines:
            data = json.loads(line)
            key = data['key']
            if 'response' in data and 'candidates' in data['response']:
                # Safely extract text
                try:
                    text = data['response']['candidates'][0]['content']['parts'][0]['text']
                    results_map[key] = text.strip()
                except (KeyError, IndexError):
                    results_map[key] = "PARSING_ERROR"
            else:
                results_map[key] = "GENERATION_FAILED"
        
        print(f"Successfully parsed {len(results_map)} results.")

        # 4. Merge results with original data and save
        print("Merging results with original data...")
        original_df = pd.read_csv(RAW_DATA_PATH)
        
        # Create the final DataFrame in the expected format
        final_df = original_df[original_df['show_id'].isin(results_map.keys())].copy()
        final_df['generated_synopsis'] = final_df['show_id'].map(results_map)
        final_df = final_df.rename(columns={'description': 'original_synopsis'})
        
        # Select and reorder columns to match the downstream script's expectation
        output_df = final_df[['show_id', 'title', 'original_synopsis', 'generated_synopsis']]
        
        output_df.to_csv(PROCESSED_DATA_PATH, index=False)
        print(f"Final results saved to: {PROCESSED_DATA_PATH}")

    else:
        print(f"Job failed or was cancelled. Error: {batch_job.error}")

if __name__ == "__main__":
    monitor_and_retrieve_results()