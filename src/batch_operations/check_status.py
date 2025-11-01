import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


from src.config import GOOGLE_API_KEY
import google.genai as genai


def check_job_status(job_name: str):
    """Checks the status of a given batch job."""
    if not job_name:
        print("Error: Please provide a job name.")
        print("Usage: python check_status.py batches/123456789")
        return

    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        return

    print(f"--- Checking status for job: {job_name} ---")
    
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        batch_job = client.batches.get(name=job_name)
        
        print(f"      Display Name: {batch_job.display_name}")
        print(f"      Current State: {batch_job.state.name}")
        print(f"      Creation Time: {batch_job.create_time}")
        
        if batch_job.state.name == 'JOB_STATE_FAILED':
            print(f"      Error: {batch_job.error}")
            
    except Exception as e:
        print(f"An error occurred while fetching job status: {e}")

if __name__ == "__main__":
    # Get the job name from the command line argument
    job_name_from_arg = sys.argv[1] if len(sys.argv) > 1 else None
    check_job_status(job_name_from_arg)