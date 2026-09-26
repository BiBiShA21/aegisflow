#!/bin/sh
set -e

# Replace the hardcoded local backend URL with the actual one from environment variables
if [ -n "$BACKEND_URL" ]; then
    echo "Updating frontend API endpoints to point to $BACKEND_URL"
    for file in /usr/share/nginx/html/*.html /usr/share/nginx/html/*.js; do
        if [ -f "$file" ]; then
            sed -i "s|http://127.0.0.1:8000|$BACKEND_URL|g" "$file"
            sed -i "s|http://localhost:8000|$BACKEND_URL|g" "$file"
        fi
    done
fi

echo "Starting Nginx..."
exec nginx -g 'daemon off;'
