FROM apache/spark:3.5.1

USER root
RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars && \
    chown -R spark:spark /home/spark
USER spark

# Base Spark image - Ivy cache directory for package downloads
