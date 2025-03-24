import os
import io
import pandas as pd
import pyreadstat
from google.cloud import storage
from google.oauth2 import service_account
import tempfile
from datetime import timedelta
import streamlit as st

type = "service_account"
project_id = "fairgen-dev"
private_key_id = "70e6e21803cd90766a534cf233a2fbc667f2c613"
private_key = """
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCMUbmchngPmeoy
hQndnqYEQ2OQVgP0ZN5n9q5n/qxp9qPyosRS2E1HSfMJeJmcbm3MWxV/LGBV5oGD
dM/NPJdqUozmXBf1l/1ZVe7kn/m7xcVijdnYQn+LlZKYT1s+vZ9bzOgjGU4u8sN/
GYyDy69vzZduEP6guJ8sEefAn0BVokcCdXxTFqpNhxkytIQC0g/QktMqUG29YeRk
tQZgNne28FNEME4BU071L3kiCUGWHI1/zD9fMhEBXy+AKQ0ObUw4r0dxvlCa6vVu
AXCr7rACfCH5gUTUdTHP59yxVR+3NOZIHNeYdqctVkeOtt8p/LgfuPrqOIHyVtGY
hMXNlZRDAgMBAAECggEAAhv1C5uLduSSLQGECam13AvtRi7WuDyGG/0M6fFp56Ce
Bb/6pPlkGI6vRUoOY7l1UIjzxtdjL5vwz3FoFiTzeKp0wo2Y1Y3JrYjVscOnRP6E
K/k+OCtIrTE/El5qn5Yq6c06D8d6q6RTWgQmCX+CbTw1vT+89T5TfTw3YXngS23I
vJDkFVq2rRrUHC3arGRWgZm/kxkg0dRlVI4Q3qlQ8+r63vgnvRuWlGPDvZrQF/jQ
cM8Z/+2lC1IYtqKSl224RNhJahm4f8TkrJKwuvjnU1Xgje1W0SvOgC+zC6pFenf5
Y1VFlVW/qVwWdQlblgDbdewgIXCNN6QVEiDzCTsBMQKBgQDFKefDdmHFwuHvvTfS
xEChxIWT6KzOoXzv57tUZzP6N8zORm2pRHEGvvxAxLylkEksLP+uhb3who9FsL6n
41VITUUa7yLN6XCymupPv1fRY60/IsQjzYYZGlbwuMbHGvxrgXjqSyANS28OvtzQ
id0FLWL/8HGneCjoVLwVmtmhkwKBgQC2MUCwOp1cU1w89y0cw/HsNb/74rKlqO8N
8XW9Ssa1ra9PAGbU5LUFzx3bz7z8z6SCXmhrD9u1qJrhE08TNGe+QJGQHjn9vjOw
4X+qMmjFYDhm9TVBCzO2Y3U9yKh7LaDqU9rpGqb05PTzHEnWEPVARDJEDKme8tc1
hJ8o11SwkQKBgGVMyo9a25FIN919UpkvzCVRW3BLM75WqmJ4pX8QJ1yAHvI8rUsy
pv/YULLWYjaOk4nm9NcuUBCskiA0V0DbRI4JZWAZTcCOGCEsBwdCQFSM6g5uRmg+
yI9NQS4dQcQ60UZLF10JjEZIY58n4TwkGTL3xs3JNBvfWOVF4/0VuouRAoGACppX
L2pZ2hOn3Ixt/ayRmbOPFrOcvfNU5jTVK0z8v3n6J9jYIy+kMVBaZn5yeywCYOvp
m8FygeHsEYk0IuP73aCYWBDKQzAchgC5k0gXvNTas3M1xDFIsyaanhvdYj3HjZuP
s90vNjVU5AkTavfVrgXJ/xfVj0CGscCkGpZdgWECgYEAjESrCkJdvbOXH1PT66o6
/dGWct8xN1dVZosK1U/vguI7MnovlrsJqDmdHlD0/7/cstZXKsF/wXRdoOBB82vV
OTMLO9owZEJetEg8INZ2E+qacIGmLUeRvtFKqLWt4ji/Z5Rh/VMdO2kSl+9wlTCg
sFzzRtABT5k6BEaea1Tv1MU=
-----END PRIVATE KEY-----
"""
client_email = "cs-materials@fairgen-dev.iam.gserviceaccount.com"
client_id = "103205185693481221052"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/cs-materials%40fairgen-dev.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

# Replace these with your actual service account info or load them securely.
SERVICE_ACCOUNT_INFO = {
    "type":  type, #st.secrets["type"],
    "project_id": project_id,# st.secrets["project_id"],
    "private_key_id": private_key_id,#st.secrets["private_key_id"],
    "private_key": private_key,#st.secrets["private_key"],
    "client_email": client_email,#st.secrets["client_email"],
    "client_id": client_id,#st.secrets["client_id"],
    "auth_uri": auth_uri,#st.secrets["auth_uri"],
    "token_uri": token_uri,#st.secrets["token_uri"],
    "auth_provider_x509_cert_url": auth_provider_x509_cert_url,#st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": client_x509_cert_url,#st.secrets["client_x509_cert_url"],
    "universe_domain": universe_domain,#st.secrets["universe_domain"],
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
            # For XLSX, use BytesIO
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
            if len(df) == 1:
                df = list(df.values())[0]
        
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


def download_processed_files():
    """
    Loads processed files from the "Processed-Files" folder in your GCP bucket and 
    provides a download button for each file so that customers can download the file.
    """
    try:
        # Create credentials and storage client
        credentials = service_account.Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        client = storage.Client(project=SERVICE_ACCOUNT_INFO["project_id"], credentials=credentials)
        bucket = client.bucket(BUCKET_NAME)
        
        # List blobs under the "Processed-Files/" prefix
        blobs = list(bucket.list_blobs(prefix="Processed-Files/"))
        if not blobs:
            st.info("No processed files found in GCP.")
        else:
            st.write("### Processed Files in GCP:")
            for blob in blobs:
                # Download blob content as bytes
                file_bytes = blob.download_as_bytes()
                # Extract the file name from blob path (e.g., "Processed-Files/train_100.csv" becomes "train_100.csv")
                file_name = os.path.basename(blob.name)
                st.download_button(
                    label=f"Download {file_name}",
                    data=file_bytes,
                    file_name=file_name,
                    mime="application/octet-stream"
                )
    except Exception as e:
        st.error(f"Error loading processed files: {e}")