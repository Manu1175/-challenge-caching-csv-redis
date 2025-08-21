FROM python:3.12-slim

# Install tzdata for timezone support
RUN apt-get update && \
    apt-get install -y tzdata && \
    rm -rf /var/lib/apt/lists/*

# Set timezone environment variable
ENV TZ=Europe/Brussels

# Ensure container uses local timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port if needed (for API)
EXPOSE 8000

# Run main.py
CMD ["python", "app/main.py"]
