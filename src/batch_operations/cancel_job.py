import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


from src.config import GOOGLE_API_KEY
import google.genai as genai


def cancel_batch_job(job_name: str):
    """Sends a cancellation request for a given batch job."""
    if not job_name:
        print("Error: Please provide a job name to cancel.")
        print("Usage: python cancel_job.py batches/123456789")
        return

    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        return

    print(f"--- Attempting to cancel job: {job_name} ---")
    
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # Optional but good practice: First, check if the job is in a cancellable state.
        job = client.batches.get(name=job_name)
        cancellable_states = {'JOB_STATE_PENDING', 'JOB_STATE_RUNNING'}
        
        if job.state.name not in cancellable_states:
            print(f"Job is in state '{job.state.name}' and cannot be cancelled.")
            return

        # Send the cancellation request
        client.batches.cancel(name=job_name)
        
        print(f"Successfully sent cancellation request for job: {job_name}")
        print("It may take a few moments for the job state to update.")
        print(f"Use 'python check_status.py {job_name}' to confirm.")

    except Exception as e:
        print(f"An error occurred while trying to cancel the job: {e}")
        print("The job may have already completed or been deleted.")

if __name__ == "__main__":
    # Get the job name from the command line argument
    job_name_from_arg = sys.argv[1] if len(sys.argv) > 1 else None
    cancel_batch_job(job_name_from_arg)