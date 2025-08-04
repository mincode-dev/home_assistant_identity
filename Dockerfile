FROM python:3.11-slim

# Install dependencies
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Copy addon code
COPY src/ /app/
COPY run.sh /

# Set permissions
RUN chmod +x /run.sh

WORKDIR /app
CMD ["/run.sh"] 