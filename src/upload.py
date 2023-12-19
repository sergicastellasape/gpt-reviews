# script just to upload output to my azure blob container
import argparse
import os
import shutil
from azure.storage.blob import BlobServiceClient

assert os.path.exists("assets-today/")
assert os.path.exists("episode/")

parser = argparse.ArgumentParser()
parser.add_argument(
    "--date", type=str, required=True, help="base path for the azure blob"
)
parser.add_argument(
    "--delete-after",
    dest="delete",
    action="store_true",
    help="Delete stuff after uploading",
)
args = parser.parse_args()

storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(
    storage_connection_string
)


def list_files(dir):
    paths = []
    for root, _, files in os.walk(dir):
        for fname in files:
            paths.append(os.path.join(root, fname))
    return paths


def upload_dir_to_azure(dir, date):
    list_paths = list_files(dir)
    for path in list_paths:
        target = os.path.join(date, path)
        blob_client = blob_service_client.get_blob_client(
            container="gpt-reviews", blob=target
        )
        with open(path, "rb") as f:
            blob_client.upload_blob(f, overwrite=True)


if __name__ == "__main__":
    upload_dir_to_azure("assets-today", args.date)
    upload_dir_to_azure("episode", args.date)
    if args.delete:
        print("Deleting folders")
        shutil.rmtree("assets-today")
        shutil.rmtree("episode")
