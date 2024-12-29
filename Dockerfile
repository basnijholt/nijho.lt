FROM ghcr.io/hugomods/hugo:ci-0.128.0 AS build

WORKDIR /app

# Copy project files to a temporary directory
COPY go.mod go.sum /tmp/build/
COPY netlify.toml /tmp/build/
COPY . /tmp/build/

# Set working directory to the temporary directory
WORKDIR /tmp/build

# Fetch Hugo modules (dependencies) in the temporary directory
RUN hugo mod get ./...

# Move necessary files to the actual working directory (/app)
RUN mv /tmp/build/public /app/ && \
    mv /tmp/build/resources /app/ && \
    mv /tmp/build/go.mod /app/ && \
    mv /tmp/build/go.sum /app/ && \
    mv /tmp/build/netlify.toml /app/

# Move the rest of your project to /app
RUN find /tmp/build -mindepth 1 -maxdepth 1 -not -name public -not -name resources -not -name go.mod -not -name go.sum -not -name netlify.toml -exec mv {} /app/ \;

# Change back to the /app working directory
WORKDIR /app

# Build the Hugo site.
RUN hugo --gc --minify

# Now, use a lightweight web server image for the final image.
FROM nginx:alpine

# Copy the built website from the 'build' stage to the Nginx web root.
COPY --from=build /app/public /usr/share/nginx/html

# Expose port 80 for HTTP traffic.
EXPOSE 80