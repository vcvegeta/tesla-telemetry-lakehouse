FROM apache/superset:latest

USER root

# Install PostgreSQL driver in the correct Python environment
RUN python -m ensurepip && \
    python -m pip install psycopg2-binary

# Copy init script
COPY superset-init.sh /app/docker/superset-init.sh
RUN chmod +x /app/docker/superset-init.sh

# Copy dashboard export for auto-import
COPY dashboards_export.zip /app/docker/dashboards_export.zip

USER superset

# Use custom init script as entrypoint
ENTRYPOINT ["/app/docker/superset-init.sh"]
