from huggingface_hub import snapshot_download

# Download model
model_path = snapshot_download(
    repo_id="vidore/colpali-v1.3",
    local_dir="./local_model"  # Save to local directory
)

# Download processor
processor_path = snapshot_download(
    repo_id="vidore/colpaligemma-3b-pt-448-base",
    local_dir="./local_processor"
)

