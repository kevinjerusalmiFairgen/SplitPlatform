import streamlit as st
import utils.files_utils as files_utils
from modules import random_split
from google.cloud import storage
from google.oauth2 import service_account
import tempfile
import os

st.set_page_config(page_title="Data Splitting Tool", layout="wide")

st.sidebar.title("Global Controls")

uploaded_file = st.sidebar.file_uploader(
    "Drag & Drop or Click to Upload",
    type=["csv", "xlsx", "sav"]
)

if uploaded_file:
    try:
        # Only save and load the file if it's not already in session_state or if a new file is uploaded
        if "data" not in st.session_state or st.session_state.get("uploaded_file_name") != uploaded_file.name:
            file_path = files_utils.save_uploaded_file(uploaded_file)
            st.write(file_path)
            data, meta = files_utils.load_file(file_path)
            if data is not None:
                st.session_state["data"] = data
                st.session_state["meta"] = meta
                st.session_state["file_path"] = file_path
                st.session_state["file_type"] = file_path.split(".")[1]
                st.session_state["uploaded_file_name"] = uploaded_file.name  
                st.sidebar.success(f"✅ {st.session_state['file_type'].upper()} file successfully loaded!")
            else:
                st.sidebar.error("❌ Error Uploading")
        else:
            st.sidebar.info("File already loaded in session.")
    except Exception as e:
        st.sidebar.error(f"❌ Error loading file: {str(e)}")


else:
    st.sidebar.info("📂 Upload a file to begin.")

# Title
st.title("Data Splitting Tool 🚀")


if "data" in st.session_state:
    random_split.app()
else:
    st.warning("⚠️ Please upload a dataset.")
