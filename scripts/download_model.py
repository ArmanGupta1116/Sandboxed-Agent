from huggingface_hub import snapshot_download


MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


def main():
    path = snapshot_download(
        repo_id=MODEL_ID,
        repo_type="model",
    )

    print(f"Model cached at:")
    print(path)


if __name__ == "__main__":
    main()