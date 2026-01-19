FROM apache/superset:latest

USER root

# Install PostgreSQL driver
RUN pip install psycopg2-binary

# Copy init script
COPY superset-init.sh /app/docker/superset-init.sh
RUN chmod +x /app/docker/superset-init.sh

USER superset

# Use custom init script as entrypoint
ENTRYPOINT ["/app/docker/superset-init.sh"]
