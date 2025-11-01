# GenFlix-AB-Test

In this project, an A/B test will be used to determine whether movie descriptions by an AI with a particular personality can receive more user clicks. It is driven by the Gemini Batch API of Google.

## Project Overview

The project investigates the possibility of achieving a significant shift in the user behavior through content customization with Generative AI. Rather than calling APIs individually and sluggishly, we call the affordable API known as the Google Gemini Batch API, with thousands of requests at a time.

In this project we build new synopsis of movies using the Netflix Movies and TV Shows dataset on the basis of various personas. This is followed by simulated A/B test to determine how this influences the user click-through rates (CTR) and testing whether the findings are statistically significant.

The point is that, when a movie is rewritten by a computer with a sense of humor (as a part of a friendly person, rather than a serious critic), it can be more noticeable to a user than an ordinary description.

## How It Works

1. **Make a Batch Job**: We begin with the publicly available Netflix data and then write a file, batch_requests.jsonl. This file contains each line with unique show id, and a prompt indicating to the AI to write a new interesting synopsis on that movie.
2. **Create the Content**: The batch_requests file is submitted as a one-batch job to Google Gemini API. A script is then used to poll the API to see the status of the job until the job is completed.
3. **Process the Results**: The results are then downloaded and cleaned up and then combined with our original data. This results in the final file generated as the generated_synopses.csv file which contains the original (Control Group A) and the AI-generated (Treatment Group B) texts.
4. **Simulate an A/B Test**: A simulator is then used to simulate thousands of users. The individual user is presented with either the control or the new synopsis and we count the number of people who click on it depending upon some base conversion rates.
5. **Analysis of Data**: This is the last stage of analysing the simulation results of a Jupyter Notebook. A Chi-Squared test is used to determine whether the difference between the CTR of Group A and Group B is significant.

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
   git clone orhansonmeztr/GenFlix-AB-Test.github.com.git.
   cd GenFlix-AB-Test
   ```
2. **Set up the environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows requires venv/Scripts/activate.
   pip install requirements.txt.
   ```
3. **Add your API Key:**
   In the parent folder, create a file named .env and put your Google AI API key and the model you desire to use:

   ```
   GOOGLE_API_KEY="YOUR_API_KEY_HERE"
   GEMINI_MODEL="gemini-2.5-flash"
   ```
4. **Download the data:**
   Obtaining the dataset. Download [this Kaggle page](https://www.kaggle.com/datasets/hqdataprofiler/cleaned-netflix-movies-and-tv-shows) and place the `netflix_titles_CLEANED.csv` file in the `data/raw/` folder.
5. **Run the Main Workflow:**

   * **Step 5.1: Submit the Batch Job**
     This script develops the requests and forwards them to the API. Only when generated `generated_synopses.csv` is not available, it will run.

     ```bash
     python src/submit_batch_job.py
     ```
   * **Step 5.2: Monitor the Job**
     This script can be run to monitor the job. It will just hold there till it is finished and then download and process the results.

     ```bash
     python src/monitor_batch_job.py
     ```

     Note: The Batch jobs may require several minutes. The status will be checked after some time intervals by the script.
   * **Step 5.3: A/B Test Simulation Run**
     When you have a ready generated `generated_synopses.csv`, run the simulation:

     ```bash
     python src/ab_simulator.py 
     ```
   * **Step 5.4: Analyze the Results**
     Start and execute the `notebooks/analysis.ipynb` and view the results, statistics and charts.

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

The `analysis.ipynb` notebook has all the findings of the analysis. It contains the calculation of the click-through rates, the Chi-Squared test, and certain charts that indicate the difference in the performance between the two groups.
