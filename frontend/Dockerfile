# Use Bun image
FROM oven/bun:1 AS base

WORKDIR /app

# Install dependencies
COPY package.json bun.lockb ./
RUN bun install --frozen-lockfile

# Copy application files
COPY . .

# Expose port
EXPOSE 3000

# Run development server
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]
