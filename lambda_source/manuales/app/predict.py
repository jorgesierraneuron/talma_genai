import os
import json
import logging
from flask import Flask, request, jsonify
from vision_rag import VisionRAG  

logging.basicConfig(level=logging.INFO)

# Create Flask app
app = Flask(__name__)

# Load model only once (to optimize inference time)
vision_rag = VisionRAG()

@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint."""
    return jsonify(status="healthy"), 200

@app.route("/invocations", methods=["POST"])
def predict():
    """SageMaker calls this endpoint for inference."""
    try:
        data = request.get_json()  # Receive input as JSON
        descripcion_evento = data.get("descripcion_evento", "No input provided")
        
        logging.info(f"Received event: {descripcion_evento}")

        # Run the model
        response = vision_rag.run(descripcion_evento)

        return jsonify({"response": response})

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # SageMaker expects the container to run on port 8080
