# GenFlix-AB-Test

An end-to-end A/B/n testing framework to evaluate the impact of multiple, distinct AI-generated personas on user engagement, powered by Google's Gemini Batch API.

## Project Overview

This project moves beyond a simple A/B test to create a robust experimental platform. It investigates whether tailoring movie synopses using different AI personalities—such as 'witty', 'serious', or 'mysterious'—can lead to statistically significant changes in user behavior.

Leveraging the cost-effective Google Gemini Batch API, the system generates content for all personas in a single, asynchronous job. It then simulates a multi-variant (A/B/C/D/E) test to measure the impact of each persona on user click-through rates (CTR). Finally, a comprehensive statistical analysis determines not only which personas outperform the original, but also if there is a single "best" persona among the winners.

The core hypothesis is that a strategically chosen AI persona can capture user interest more effectively than a standard, neutral description, and that different tones will resonate differently with users.

## Methodology

1. **Persona Definition**: A registry of distinct AI personas is defined in `src/config.py`. Each persona has a unique prompt and a fine-tuned `temperature` setting to control creative output.
2. **Batch Job Preparation**: The script reads the Netflix dataset and prepares a single `batch_requests.jsonl` file containing prompts for **all personas** for each sampled movie.
3. **Asynchronous Generation**: The request file is submitted as one batch job to the Google Gemini API. A monitoring script polls the API until the job is complete.
4. **Result Processing**: Once the job succeeds, the results are downloaded, parsed, and consolidated into a single `generated_synopses.csv` file. This file contains the original synopsis (control group) and a separate column for each AI-generated persona.
5. **Multi-Variant Simulation (Modeling User Behavior)**: Since this project does not have access to a live user base, real-world click data is unavailable. To bridge this gap, a simulation script (`ab_simulator.py`) models user behavior. It generates a large-scale dataset of user interactions by assigning tens of thousands of virtual users to the different persona groups. Each group is given a predefined, hypothetical "true" click-through rate, and the script records a "click" or "no-click" event for each user based on this probability. **The purpose of this simulation is to create a realistic dataset that allows for a robust, end-to-end demonstration of the statistical analysis framework.**

6. **Statistical Analysis**: The simulation results are analyzed in a Jupyter Notebook using a three-stage process:
   * **Omnibus Test**: A Chi-Squared test determines if there is any significant difference among all groups.
   * **Post-Hoc Test vs. Control**: If the omnibus test is significant, pairwise tests are run to identify which personas significantly outperform the control group.
   * **Post-Hoc Test Among Winners**: A final round of pairwise tests determines if there is a statistically significant difference between the top-performing personas.
   * **Bonferroni Correction** is applied in the post-hoc stages to prevent false positives from multiple comparisons.

## Project Structure

```
GenFlix-AB-Test/
├── README.md
├── requirements.txt
├── .env
├── .gitignore
├── data/
│   ├── processed/
│   │   ├── generated_synopses.csv
│   │   └── simulation_results.csv
│   ├── raw/
│   │   └── netflix_titles_CLEANED.csv
│   └── temp/
│       ├── batch_job_state.json
│       └── batch_requests.jsonl
├── notebooks/
│   └── analysis.ipynb
└── src/
    ├── __init__.py
    ├── ab_simulator.py
    ├── config.py
    ├── monitor_batch_job.py
    ├── submit_batch_job.py
    └── batch_operations/
        ├── __init__.py
        ├── cancel_job.py
        ├── check_status.py
        └── list_batch_jobs.py
```

## How to Run

1. **Clone the repository:**

   ```bash
   git clone https://github.com/orhansonmeztr/GenFlix-AB-Test.git
   cd GenFlix-AB-Test
   ```
2. **Set up the environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. **Add API Key and Configuration:**
   Create a `.env` file in the root directory and add your Google AI API key and the desired model:

   ```
   GOOGLE_API_KEY="YOUR_API_KEY_HERE"
   GEMINI_MODEL="gemini-2.5-flash"
   ```
4. **Download the data:**
   Download the dataset from [this Kaggle page](https://www.kaggle.com/datasets/hqdataprofiler/cleaned-netflix-movies-and-tv-shows) and place `netflix_titles_CLEANED.csv` into the `data/raw/` directory.
5. **Execute the Main Workflow:**

   * **Step 5.1: Submit the Batch Job for Content Generation**
     This script prepares requests for all personas and submits them to the API. It will not run if `generated_synopses.csv` already exists.

     ```bash
     python src/submit_batch_job.py
     ```
   * **Step 5.2: Monitor the Job and Retrieve Results**
     Run this script to check the job's status. It will wait until the job is complete, then download and process the results into the final multi-column CSV.

     ```bash
     python src/monitor_batch_job.py
     ```

     *(Note: Batch jobs can take several minutes to complete. The script will poll the status periodically.)*
   * **Step 5.3: Run the A/B/n Test Simulation**
     Once `generated_synopses.csv` is created, run the simulation for all groups:

     ```bash
     python src/ab_simulator.py
     ```
   * **Step 5.4: Analyze the Results**
     Open and run the `notebooks/analysis.ipynb` notebook to see the results, statistical tests, and visualizations.

     ```bash
     jupyter notebook notebooks/analysis.ipynb
     ```

## Batch Operation Utilities

There are a few useful scripts in the folder of the batch-operations of the sources, in the directory called `src/batch operations/`. Execute them in the root of the project.

* **List all recent batch jobs:**

  ```bash
  python src/batch_operations/list_batch_jobs.py
  ```
* **Status of a job:**

  ```bash
  python src/batch_operations/check_status.py a_batch_name
  ```
* **Cancel a job:**

  ```bash
  python src/batch_operations/cancel_job.py a_batch_name
  ```

## Results & Analysis

The findings from the statistical analysis are detailed in the `analysis.ipynb` notebook. The notebook includes the calculation of click-through rates, confidence intervals, the multi-stage hypothesis testing process, and visualizations to illustrate the performance differences. The analysis concludes with a data-driven business recommendation on which persona to deploy based on both statistical significance and strategic brand alignment.
