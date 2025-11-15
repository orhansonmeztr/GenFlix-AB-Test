import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from config import PERSONA_CONFIGS

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DATA_PATH = BASE_DIR / "data" / "processed" / "generated_synopses.csv"
SIMULATION_RESULTS_PATH = BASE_DIR / "data" / "processed" / "simulation_results.csv"
NUM_USERS = 100000

TRUE_CTR = {
    'control': 0.040, # Original text (Control Group A)
    'witty': 0.055,   # Humorous text (Test Group B)
    'serious': 0.042, # Serious text (Test Group C)
    'mysterious': 0.051, # Mysterious text (Test Group D)
    'enthusiastic': 0.058 # Enthusiastic text (Test Group E)
}

def run_simulation():
    """
    Simulates a multi-group (A/B/C/D/E) test using the combined synopses data.
    """
    if SIMULATION_RESULTS_PATH.exists():
        print(f"--> {SIMULATION_RESULTS_PATH} file already exists. Skipping simulation.")
        return

    print("--- Starting Multi-Group A/B Test Simulation ---")

    try:
        content_df = pd.read_csv(GENERATED_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Generated content file not found at {GENERATED_DATA_PATH}")
        print("Please run 'monitor_batch_job.py' after a successful batch job.")
        return    
          
    print(f"Loaded {len(content_df)} titles for the simulation.")
    generated_cols = [f"generated_{key}" for key in PERSONA_CONFIGS.keys()]
    
    failed_mask = (content_df[generated_cols].eq('GENERATION_FAILED')).any(axis=1) | \
                  (content_df[generated_cols].eq('PARSING_ERROR')).any(axis=1)
    
    clean_content_df = content_df[~failed_mask].copy()
    
    num_dropped = len(content_df) - len(clean_content_df)
    if num_dropped > 0:
        print(f"Dropped {num_dropped} rows due to generation/parsing errors.")

    if clean_content_df.empty:
        print("No valid generated content to run simulation on. Exiting.")
        return

    groups_to_test = ['control'] + list(PERSONA_CONFIGS.keys())
    print(f"Simulating for groups: {groups_to_test}")
    
    assigned_groups = np.random.choice(groups_to_test, size=NUM_USERS)

    simulation_data = []    
    for user_id in tqdm(range(NUM_USERS), desc="Simulating Users"):
        group = assigned_groups[user_id]
        random_movie = clean_content_df.sample(n=1).iloc[0]
        show_id = random_movie['show_id']
        conversion_rate = TRUE_CTR.get(group, 0.01)
        
        # Simulate the click event
        clicked = 1 if np.random.random() < conversion_rate else 0
        
        simulation_data.append({
            'user_id': user_id,
            'group': group,
            'show_id': show_id,
            'clicked': clicked
        })

    if not simulation_data:
        print("Simulation did not produce any data. Exiting.")
        return

    results_df = pd.DataFrame(simulation_data)
    SIMULATION_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)    
    results_df.to_csv(SIMULATION_RESULTS_PATH, index=False)
    
    print("\n--- A/B Test Simulation Complete ---")
    print(f"Simulated {NUM_USERS} user interactions across {len(groups_to_test)} groups.")
    print(f"Results saved to: {SIMULATION_RESULTS_PATH.name}")

if __name__ == "__main__":
    run_simulation()