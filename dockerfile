# Use the official PostgreSQL image
FROM postgres:17

# Install dependencies for building pgvector
RUN apt-get update && apt-get install -y postgresql-server-dev-17 make gcc git \
    && git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make && make install \
    && rm -rf /tmp/pgvector

# Set environment variables for PostgreSQL (if needed)
# You can remove these if you're connecting to an external database via env vars
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=Tt501007
ENV POSTGRES_DB=postgres

# Copy the init.sql script into the PostgreSQL entrypoint directory
COPY init.sql /docker-entrypoint-initdb.d/

# Make sure the init.sql is executed at container start
# The PostgreSQL image runs any scripts inside /docker-entrypoint-initdb.d/ during initialization.
