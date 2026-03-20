# LLMOps: Production Monitoring and Observability for LLM Applications

This portfolio project provides a complete monitoring and observability solution for Large Language Model (LLM) applications. It is designed to capture, record, analyze, and visualize critical metrics such as token usage, cost, latency, error rates, and output quality – the foundational pillars of effective LLMOps.

## 🚀 Features

- **LLM API Interception**: A robust Python wrapper (`LLMCallWrapper`) that intercepts LLM generations to gather token usage, model choices, and network latency.
- **Cost Calculation Engine**: Reconciles varying model pricing dynamics to compute the exact cost of each LLM transaction instantly.
- **Automated Quality Heuristics**: Applies rules-based post-generation checks to flag sub-optimal outputs automatically:
  - `too_short`: Flags unnaturally short responses (< 20 words).
  - `refusal`: Detects standard AI refusal languages (e.g. "I cannot", "I am an AI").
  - `repetition`: Flags if the API gets trapped in a repetitive generation loop.
  - `low_confidence`: Flags excessive hedging.
- **Structured Metrics Logging**: Persists all observability records precisely to a `logs.jsonl` (JSON Lines) flat file.
- **Alerting Mechanisms**: Actively monitors error rates utilizing a sliding window pattern (over the last 10 requests), firing console alerts automatically if the error rate breaches a predefined 20% limit.
- **Executive Dashboard**: A comprehensive Streamlit visual interface to parse and visualize Request Volumes, Timings, Costs, Errors, and Quality Flags cleanly.

## 🛠️ Architecture

```
├── llm_app.py        # Core generation logic, LLMCallWrapper, Alerting checker.
├── heuristics.py     # Post-processing heuristics to grade generation quality.
├── simulate_load.py  # Automation script to synthesize 60 varied LLM requests.
├── dashboard.py      # Streamlit-powered observability dashboard.
├── logs.jsonl        # The structured datastore driving the UI.
├── Dockerfile        # Container build instructions.
├── docker-compose.yml# Container orchestration file.
├── requirements.txt  # Python packages list.
└── .env.example      # Environment variables template.
```

## 💻 Setup and Usage Instructions

### Method 1: Docker (Recommended)

1. Make sure [Docker](https://docs.docker.com/get-docker/) is installed.
2. Build and run the entire suite using Docker Compose:
```bash
docker-compose up --build
```
> *What this does: The container will automatically invoke `simulate_load.py` to synthetically generate rich log data (with forced failures to trigger Alerts!), and subsequently host the Streamlit dashboard on port 8501.*

3. Navigate to [http://localhost:8501](http://localhost:8501) to interact with your metrics!

### Method 2: Local Python Execution

If you prefer testing natively without containers:
1. Initialize a Python environment (Python 3.9+ supported):
```bash
python -m venv venv
### Windows
venv\Scripts\activate
### macOS/Linux
source venv/bin/activate
```
2. Install pip dependencies:
```bash
pip install -r requirements.txt
```
3. Generate sample load:
```bash
python simulate_load.py
```
> *Enjoy watching the console! You will see request statuses and automated Alerts triggering dynamically towards the console as the error rate hits the defined threshold.*

4. Boot the Dashboard:
```bash
streamlit run dashboard.py
```
5. View at [http://localhost:8501](http://localhost:8501).

---

## 🏗️ Design Decisions
*   **Decoupled Wrapper:** The `LLMCallWrapper` encapsulates the raw client interaction separately from business logic, ensuring observability is implemented flawlessly without cluttering root endpoints.
*   **JSON Lines (JSONL) Data Layer:** Optimized structured data persistence format perfectly tailored for append-only streaming mechanisms, universally parseable by data tools unreliant on relational database complexity overheads for a POC.
*   **Heuristics Engine:** Provides safety checks to shield users from hallucinated/refused outputs by giving engineering teams the flag insight immediately upon ingestion.

## 🤝 Next Steps / Submission Check
To submit your work:
1. Ensure all code resides cleanly in the root of the folder.
2. Select all files and package them securely into a `zip` archive.
3. Submit the `.zip` archive to complete the objective properly.
