import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


from src.config import GOOGLE_API_KEY
import google.genai as genai

def list_all_batch_jobs():
    """
    Connects to the Google AI API and lists all batch jobs associated with the API key.
    """
    print("--- Fetching all batch jobs ---")
    
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
        
        # client.batches.list() bir 'pager' nesnesi döndürür, bu da for döngüsüyle gezilebilir.
        job_list = list(client.batches.list())
        
        if not job_list:
            print("No batch jobs found for this project.")
            return

        print(f"Found {len(job_list)} batch job(s):\n")
        
        # İşleri oluşturulma zamanına göre tersten sıralayalım (en yeni en üstte)
        sorted_jobs = sorted(job_list, key=lambda job: job.create_time, reverse=True)

        for job in sorted_jobs:
            print(f"Display Name: {job.display_name}")
            print(f"  - Job Name (ID): {job.name}")
            print(f"  - State: {job.state.name}")
            print(f"  - Created At: {job.create_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Eğer iş başarılı olduysa, çıktı dosyasının adını göster
            if job.state.name == 'JOB_STATE_SUCCEEDED':
                if job.dest and job.dest.file_name:
                    print(f"  - Output File: {job.dest.file_name}")
            
            # Eğer iş hatalı bittiyse, hatayı göster
            elif job.state.name == 'JOB_STATE_FAILED':
                if job.error:
                    print(f"  - Error: {job.error.message}")
            
            print("-" * 30)

    except Exception as e:
        print(f"\nAn error occurred while fetching batch jobs.")
        print("Please check your API Key and project configuration.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    list_all_batch_jobs()