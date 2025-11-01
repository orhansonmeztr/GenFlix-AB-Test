import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DATA_PATH = BASE_DIR / "data" / "processed" / "generated_synopses.csv"
SIMULATION_RESULTS_PATH = BASE_DIR / "data" / "processed" / "simulation_results.csv"
NUM_USERS = 100000

TRUE_CTR = {
    'A': 0.040,  # Control Group (Original Synopsis) gets a 4.0% CTR
    'B': 0.055   # Treatment Group (AI Synopsis) gets a 5.5% CTR
}

def run_simulation():
    """
    Simulates an A/B test using the generated synopses data.
    """
    print("--- Starting A/B Test Simulation ---")

    try:
        content_df = pd.read_csv(GENERATED_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: Generated content file not found at {GENERATED_DATA_PATH}")
        print("Please run 'python src/content_generator.py' first.")
        return
    
    content_df = content_df[content_df['generated_synopsis'] != 'GENERATION_FAILED'].copy()
    if content_df.empty:
        print("No valid generated content to run simulation on. Exiting.")
        return
        
    print(f"Loaded {len(content_df)} titles for the simulation.")

    simulation_data = []
    groups = np.random.choice(['A', 'B'], size=NUM_USERS, p=[0.5, 0.5])
    
    for user_id in tqdm(range(NUM_USERS), desc="Simulating Users"):
        group = groups[user_id]
        random_movie = content_df.sample(n=1).iloc[0]
        show_id = random_movie['show_id']
        conversion_rate = TRUE_CTR[group]
        
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
    print(f"Simulated {NUM_USERS} user interactions.")
    print(f"Results saved to: {SIMULATION_RESULTS_PATH}")

if __name__ == "__main__":
    run_simulation()