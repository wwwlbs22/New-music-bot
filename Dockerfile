FROM python:3.13.2

# Install ffmpeg and MongoDB
RUN apt-get update && \
    apt-get install -y ffmpeg gnupg curl && \
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
      gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \
      --dearmor && \
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
      tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org && \
    mkdir -p /data/db && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create startup script to launch both MongoDB and your Python app
RUN echo '#!/bin/bash\nmongod --fork --logpath /var/log/mongodb.log\npython3 main.py' > start.sh && \
    chmod +x start.sh

# Default command
CMD ["./start.sh"]
