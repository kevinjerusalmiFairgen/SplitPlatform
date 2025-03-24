import os
import io
import pandas as pd
import pyreadstat
from google.cloud import storage
from google.oauth2 import service_account
import tempfile
from datetime import timedelta
import streamlit as st
import glob


SERVICE_ACCOUNT_INFO = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
    "universe_domain": st.secrets["universe_domain"],
}
BUCKET_NAME = "fairgen-cs-materials"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_uploaded_file(uploaded_file):
    """
    Uploads the given file-like object to the specified Google Cloud Storage bucket under the "UploadedFile" folder.
    """
    # Create credentials and storage client
    credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
    client = storage.Client(project=SERVICE_ACCOUNT_INFO["project_id"], credentials=credentials)
    
    # Define folder and create blob name
    folder_name = "Uploaded-Files"
    blob_name = f"{folder_name}/{uploaded_file.name}"
    
    # Get the bucket and create a blob using the new blob name
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    
    # Ensure the file pointer is at the beginning
    uploaded_file.seek(0)
    
    # Upload the file using the file object
    blob.upload_from_file(uploaded_file, rewind=True)
    
    return f"gs://{BUCKET_NAME}/{blob_name}"


@st.cache_data
def load_file(file_path):
    """
    Loads CSV, XLSX, or SAV files from Google Cloud Storage into a Pandas DataFrame.
    """
    meta = None
    try:
        # Ensure file_path is a GCS path
        if not file_path.startswith("gs://"):
            return None, {"error": "File path must be a GCS path starting with gs://"}
        
        # Parse the bucket and blob name from the file_path
        # Example file_path: gs://bucket_name/file_name.ext
        path_without_prefix = file_path[5:]  # Remove 'gs://'
        parts = path_without_prefix.split("/", 1)
        if len(parts) != 2:
            return None, {"error": "Invalid GCS file path format."}
        bucket_name, blob_name = parts
        file_name_lower = blob_name.lower()

        # Create GCS client using service account credentials
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        client = storage.Client(project=SERVICE_ACCOUNT_INFO["project_id"], credentials=credentials)
        
        # Access the bucket and blob
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Download the file's bytes from GCS
        file_bytes = blob.download_as_bytes()
        
        # Load the file into a DataFrame based on its extension
        if file_name_lower.endswith(".csv"):
            # For CSV, decode bytes to a string and use StringIO
            file_str = file_bytes.decode("utf-8")
            df = pd.read_csv(io.StringIO(file_str))
        
        elif file_name_lower.endswith(".xlsx"):
            try:
                df = pd.read_excel(io.BytesIO(file_bytes))
            except Exception as e:
                return None, {"error": f"Error loading XLSX file: {str(e)}"}
        
        elif file_name_lower.endswith(".sav"):
            # For SAV, write the bytes to a temporary file then use pyreadstat
            with tempfile.NamedTemporaryFile(suffix=".sav", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp.flush()
                temp_file_path = tmp.name
            df, meta = pyreadstat.read_sav(temp_file_path)
            os.remove(temp_file_path)
        else:
            return None, {"error": "Unsupported file type"}
        
        return df, meta

    except Exception as e:
        print(e)
        return


def save_file(df, file_path, metadata=None):
    """
    Saves a DataFrame to CSV, XLSX, or SAV format.
    """
    # Extract the file name and file type from file_path
    file_name = os.path.basename(file_path)  # e.g., "train_100.csv"
    file_type = file_path.split(".")[1]  

    try:
        # Create a temporary file with the appropriate suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + file_type) as tmp:
            temp_file_path = tmp.name

        # Save the DataFrame locally to the temporary file
        if file_type == "csv":
            df.to_csv(temp_file_path, index=False)
        elif file_type == "xlsx":
            df.to_excel(temp_file_path, index=False, engine="xlsxwriter")
        elif file_type == "sav":
            pyreadstat.write_sav(
                df, temp_file_path, 
                column_labels=metadata.column_labels,
                variable_value_labels=metadata.variable_value_labels,
                missing_ranges=metadata.missing_ranges
            )
        else:
            print("error")
            return {"error": "Unsupported file type"}

        # Create credentials and a storage client
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        client = storage.Client(project=SERVICE_ACCOUNT_INFO["project_id"], credentials=credentials)
        
        # Upload the file to the "Processed-Files" folder in the bucket
        bucket = client.bucket(BUCKET_NAME)
        blob_name = f"Processed-Files/{file_name}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(temp_file_path)

        print(f"✅ File saved successfully to GCP at gs://{BUCKET_NAME}/{blob_name}")

    except Exception as e:
        print(e)
        return {"error": str(e)}

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def empty_folder(folder_path):
    """
    Empties the contents of a folder using only the os module.
    """
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)  # Remove file or symbolic link
                elif os.path.isdir(item_path):
                    os.rmdir(item_path)  # Remove empty directory
            except Exception as e:
                print(f"Error removing {item_path}: {e}")

        print(f"Folder '{folder_path}' emptied successfully.")
    else:
        print("Invalid folder path or folder does not exist.")


def get_label(metadata, column, value):
    return metadata.variable_value_labels.get(column, {}).get(value, None) 


@st.cache_data(show_spinner=False)
def generate_signed_url(blob):
    """
    Generate a signed URL for downloading the file from GCP.
    """
    return blob.generate_signed_url(
        expiration=3600,  # URL valid for 1 hour
        method="GET"
    )

def download_processed_files(bucket_name, file_path, expiration=60):
    """
    Downloads a file from GCS and provides a clickable download button in Streamlit.

    Parameters:
        bucket_name (str): The name of the GCS bucket.
        file_path (str): The full path of the file within the bucket.
        expiration (int): The expiration time of the signed URL in seconds.

    Returns:
        str: Signed URL for downloading the file.
    """
    try:
        # Initialize the client
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        client = storage.Client(project=SERVICE_ACCOUNT_INFO["project_id"], credentials=credentials)

        # Get the bucket
        bucket = client.bucket(bucket_name)

        # Get the blob (file) from the bucket
        blob = bucket.blob(file_path)

        # Generate a signed URL for downloading the file
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="GET"
        )
        return signed_url

    except Exception as e:
        st.error(f"Error downloading file from GCS: {str(e)}")
        st.write("fack")
        return None