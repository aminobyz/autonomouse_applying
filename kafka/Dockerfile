FROM python:3.11-slim

WORKDIR /app

# Install standard open-source library for running kafka clients in python
RUN pip install --no-cache-dir confluent-kafka

COPY . .

# Make the shell script executable
RUN chmod +x run.sh

# Run the shell script wrapper
CMD ["./run.sh"]