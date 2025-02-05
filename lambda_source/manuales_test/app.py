import os
import logging

logging.basicConfig(level=logging.INFO)

# Read input from environment
descripcion_evento = os.getenv("DESCRIPCION_EVENTO", "No input").upper()

# Log the result (Lambda will retrieve from CloudWatch Logs)
logging.info(f"Processed Event: {descripcion_evento}")
