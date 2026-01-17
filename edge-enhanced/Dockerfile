FROM nginx:alpine

# Install Python for logging script
RUN apk add --no-cache python3 py3-pip curl

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages requests

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy logging script
COPY log_sender.py /usr/local/bin/log_sender.py
RUN chmod +x /usr/local/bin/log_sender.py

# Create cache directory
RUN mkdir -p /var/cache/nginx

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

