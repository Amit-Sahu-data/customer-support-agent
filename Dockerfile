# Dockerfile
# Containerizes the entire application
# Why Docker?
# - Same environment everywhere — dev, staging, production
# - No "works on my machine" problems
# - Required for cloud deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Why copy requirements first?
# Docker caches layers — if requirements don't change,
# pip install is skipped on rebuild. Saves 3-5 minutes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of application
COPY . .

# Create necessary directories
RUN mkdir -p data knowledge_base models

# Initialize knowledge base at build time
RUN python knowledge_base/loader.py

# Expose Streamlit port
EXPOSE 8501

# Why these Streamlit flags?
# --server.address=0.0.0.0 — accepts connections from outside container
# --server.headless=true — no browser auto-open in container
CMD ["streamlit", "run", "app.py",
     "--server.port=8501",
     "--server.address=0.0.0.0",
     "--server.headless=true"]