import pandas as pd
import json
import time
from pathlib import Path
from collections import defaultdict
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
    Monitors a job and retrieves results, creating a single CSV with a column
    for each persona.
    """

    if PROCESSED_DATA_PATH.exists():
        print(f"--> Final output file already exists at: {PROCESSED_DATA_PATH.name}")
        print("--> Skipping monitoring process.")
        return
    
    print("--- Starting Batch Job Monitor ---")

    # 1. Load the job name
    try:
        with open(JOB_STATE_FILE_PATH, "r") as f:
            job_info = json.load(f)
            job_name = job_info['job_name']
        print(f"Monitoring job: '{job_info.get('display_name', job_name)}'")
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
        
        parsed_results = defaultdict(dict)
        for line in result_lines:
            data = json.loads(line)
            full_key = data['key']
            show_id, persona_key = full_key.rsplit('_', 1) # 's123_witty' -> ('s123', 'witty')
            
            if 'response' in data and 'candidates' in data['response']:
                try:
                    text = data['response']['candidates'][0]['content']['parts'][0]['text']
                    parsed_results[show_id][persona_key] = text.strip()
                except (KeyError, IndexError):
                    parsed_results[show_id][persona_key] = "PARSING_ERROR"
            else:
                parsed_results[show_id][persona_key] = "GENERATION_FAILED"
        
        print(f"Successfully parsed results for {len(parsed_results)} unique shows.")

        results_df = pd.DataFrame.from_dict(parsed_results, orient='index')
        results_df = results_df.add_prefix('generated_')
        results_df = results_df.reset_index().rename(columns={'index': 'show_id'})

        # 4. Merge results with original data and save
        print("Merging results with original data...")
        original_df = pd.read_csv(RAW_DATA_PATH)

        final_df = pd.merge(original_df, results_df, on='show_id', how='inner')
        final_df = final_df.rename(columns={'description': 'original_synopsis'})

        final_columns = ['show_id', 'title', 'original_synopsis'] + sorted(list(results_df.columns.drop('show_id')))
        output_df = final_df[final_columns]
        
        output_df.to_csv(PROCESSED_DATA_PATH, index=False)
        print(f"Final combined results saved to: {PROCESSED_DATA_PATH}")
    else:
        print(f"Job failed or was cancelled. Error: {batch_job.error}")

if __name__ == "__main__":
    monitor_and_retrieve_results()