FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the simulation script to generate mock data, then start the dashboard
CMD python simulate_load.py && streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
