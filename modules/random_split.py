import streamlit as st
from utils import split_utils, files_utils
from streamlit_vertical_slider import vertical_slider
import random
import pandas as pd


def app():
    data = st.session_state.get("data", pd.DataFrame())
    meta = st.session_state.get("meta", {})

    if "boostrap" not in st.session_state:
        st.session_state["boostrap"] = False
    if "boostrap_occurences" not in st.session_state:
        st.session_state["boostrap_occurences"] = 3

    total_size = len(data)

    col_shape, col_preview = st.columns([5, 4]) 

    with col_shape:
        st.write("### Shape:")

        col_slider, col_stats = st.columns([3, 5]) 
        
        with col_slider:
            st.write("")
            st.write("")

            train_size_percentage = 100 - vertical_slider(
                label="Holdout Split",
                default_value=90,
                min_value=0,
                max_value=100,
                step=1,
                key="random split"
            )

        train_size = int((train_size_percentage / 100) * total_size)
        holdout_size = total_size - train_size 
        holdout_size_percentage = 100 - train_size_percentage * 2 

        # Added warning if training data is not between 10% (1/10) and 20% (1/5) of the data
        if not (10 <= train_size_percentage <= 20):
            st.warning("Warning: The training data percentage should be between 10% (1/10) and 20% (1/5) of the total data.")

        with col_stats:
            st.metric(label="Total Size", value=f"{total_size} rows")
            st.metric(label=f"Train Size ({train_size_percentage}%)", value=f"{train_size} rows")
            st.metric(label=f"Holdout Size ({holdout_size_percentage}%)", value=f"{holdout_size} rows")

        new_boostrap_state = st.toggle("Boostrap", value=st.session_state["boostrap"], help="Repeated data splitting with replacement")
        if new_boostrap_state != st.session_state["boostrap"]:
            st.session_state["boostrap"] = new_boostrap_state
            st.rerun()

        if st.session_state["boostrap"]:
            st.session_state["boostrap_occurences"] = st.number_input(
                "Boostrap Occurences", min_value=0, max_value=10, value=st.session_state["boostrap_occurences"]
            )

    with col_preview:
        st.write("### Preview:")
        split_utils.plot_training_holdout(train_size, holdout_size)

    if st.button("Split Data"):
        files_utils.empty_folder("outputs")

        # Generate multiple random states if bootstrapping is enabled, otherwise set to None
        random_states = [random.randint(1, 100) for _ in range(st.session_state["boostrap_occurences"])] if st.session_state["boostrap"] else None

        # Perform dataset splitting
        split_results = split_utils.random_split(
            st.session_state["data"], 
            train_size=train_size_percentage / 100, 
            baseline=False,
            remove_baseline=False,
            random_states=random_states
        )
        print(len(split_results[0]))

        # Save results for each split (single or multiple depending on bootstrapping)
        for idx, (train_df, holdout_df, baseline_df) in enumerate(split_results):
            suffix = f"_batch_{idx+1}" if st.session_state["boostrap"] else ""
            
            files_utils.save_file(df=train_df, metadata=meta, file_path=f"train_{train_size}{suffix}" + "." +  st.session_state["file_type"])
            files_utils.save_file(df=holdout_df, metadata=meta, file_path=f"holdout_{holdout_size}{suffix}" + "." + st.session_state["file_type"])

            if baseline_df is not None:
                files_utils.save_file(df=baseline_df, metadata=meta, file_path=f"baseline_{train_size*2}{suffix}" + "." + st.session_state["file_type"])

        #if st.button("Download Processed Files"):
        train_signed_url = files_utils.download_processed_files(bucket_name="fairgen-cs-materials", file_path=f"Processed-Files/train_{train_size}{suffix}" + "." +  st.session_state["file_type"])
        holdout_signed_url = files_utils.download_processed_files(bucket_name="fairgen-cs-materials", file_path=f"Processed-Files/holdout_{holdout_size}{suffix}" + "." +  st.session_state["file_type"])
        if baseline_df is not None:
            baseline_signed_url = files_utils.download_processed_files(bucket_name="fairgen-cs-materials", file_path=f"Processed-Files/baseline_{train_size*2}{suffix}" + "." +  st.session_state["file_type"])
        
        # st.markdown(f"[Click Here to get your train set]({train_signed_url})")
        # st.markdown(f"[Click Here to get your holdout set]({holdout_signed_url})")
        # if baseline_df is not None:
        #     st.markdown(f"[Click Here to get your baseline set]({baseline_signed_url})")
        st.write(train_signed_url)
        st.write(holdout_signed_url)

            