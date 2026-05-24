#!/bin/bash

# Start the producer in the background (&)
python -u producer.py &

# Start the consumer in the foreground so the container stays alive
python -u consumer.py