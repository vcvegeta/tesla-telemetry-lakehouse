FROM apache/superset:latest

USER root

# Install PostgreSQL driver in the correct Python environment
RUN python -m ensurepip && \
    python -m pip install psycopg2-binary

# Copy init script and chart creation script
COPY superset-init.sh /app/docker/superset-init.sh
COPY create_charts.py /app/docker/create_charts.py
RUN chmod +x /app/docker/superset-init.sh

USER superset

# Use custom init script as entrypoint
ENTRYPOINT ["/app/docker/superset-init.sh"]
