import streamlit as st
import pandas as pd
from streamlit_vertical_slider import vertical_slider
from utils import split_utils, files_utils
import random
import json

def app():
    """Streamlit App for Dataset Splitting and Filtering"""
    data = st.session_state.get("data", pd.DataFrame())
    meta = st.session_state.get("meta", {})

    if "selections" not in st.session_state:
        st.session_state.selections = []  

    if "user_choices" not in st.session_state:
        st.session_state.user_choices = []

    if "remove_baseline" not in st.session_state:
        st.session_state["remove_baseline"] = True

    if "with_baseline" not in st.session_state:
        st.session_state["with_baseline"] = True

    if "boostrap" not in st.session_state:
        st.session_state["boostrap"] = False

    if "boostrap_occurences" not in st.session_state:
        st.session_state["boostrap_occurences"] = 3

    def add_column():
        """Adds a new column selection box dynamically"""
        available_columns = [col for col in data.columns if col not in {s["column"] for s in st.session_state.selections}]
        if available_columns:
            st.session_state.selections.append({"column": "", "values": []})  # Default structure

    def clear_selections():
        """Clears all selections and filters"""
        st.session_state.selections = []  
        st.session_state.user_choices = []
        for key in list(st.session_state.keys()):
            if key.startswith("column_") or key.startswith("values_"):
                del st.session_state[key]  

    dataset_summary, plot = st.columns([4, 2.5]) 
    column_selection, value_selection, dataset_split, other_options = st.columns([2, 2, 1, 2]) 

    current_filters = {}

    selected_columns = set()

    with column_selection:
        st.write("### Segment Selection")
        for idx in range(len(st.session_state.selections)):
            available_columns = [col for col in data.columns if col not in selected_columns]

            selected_column = st.selectbox(
                f"Column {idx + 1}:",
                available_columns,  
                key=f"column_{idx}",
            )
            if selected_column:
                st.session_state.selections[idx]["column"] = selected_column  # Store in selections
                selected_columns.add(selected_column)

        if len(selected_columns) < len(data.columns):
            st.button("➕ Add Another Column", on_click=add_column)

    with value_selection:
        st.write("### Value Selection")
        for idx in range(len(st.session_state.selections)):
            selected_column = st.session_state.selections[idx].get("column", "")

            if selected_column:
                @st.cache_data
                def get_unique_values(column):
                    """Returns unique non-null values from the specified column as a list."""
                    return list(data[column].dropna().unique()) 

                unique_values = get_unique_values(selected_column)

                value_map = {
                    f"{val} - {label}" if (label := files_utils.get_label(meta, selected_column, val)) else str(val): val
                    for val in unique_values
                } if meta else {str(val): val for val in unique_values}

                selected_display_values = st.multiselect(
                    f"Values for {selected_column}:",
                    list(value_map.keys()),  
                    key=f"values_{idx}"
                )

                selected_values = [value_map[val] for val in selected_display_values]
                st.session_state.selections[idx]["values"] = selected_values  # Store values in selections

        st.button("❌ Clear All Filters", on_click=clear_selections)

    with dataset_split:
        st.write("### Settings")
        train_size_percentage = 100 - vertical_slider(
            label="Holdout Split",
            default_value=90,
            min_value=0,
            max_value=100,
            step=1,
            key="targeted_split_slider"
        )

    with other_options:
        st.write("### ")
        st.write("### ")

        # Update session state directly
        if st.toggle("Baseline", value=st.session_state["with_baseline"], key="with_baseline_targeted"):
            if not st.session_state["with_baseline"]:  
                st.session_state["with_baseline"] = True
                st.rerun()
        else:
            if st.session_state["with_baseline"]:
                st.session_state["with_baseline"] = False
                st.rerun()


        if st.toggle("Remove Baseline from Holdout", 
                    value=st.session_state["remove_baseline"], 
                    key="remove_baseline_targeted", 
                    disabled=not st.session_state["with_baseline"]):
            if not st.session_state["remove_baseline"]:
                st.session_state["remove_baseline"] = True
                st.rerun()
        else:
            if st.session_state["remove_baseline"]:
                st.session_state["remove_baseline"] = False
                st.rerun()


        # Bootstrap setting
        new_boostrap_state = st.toggle(
            "Boostrap", value=st.session_state["boostrap"], key="bootstrap_targeted"
        )

        if new_boostrap_state != st.session_state["boostrap"]:
            st.session_state["boostrap"] = new_boostrap_state
            st.rerun()  # Ensures UI updates immediately

        if st.session_state["boostrap"]:
            st.session_state["boostrap_occurences"] = st.number_input(
                "Boostrap Occurrences", 
                min_value=0, max_value=10, 
                value=st.session_state["boostrap_occurences"], 
                key="bootstrap_targeted_occurences"
            )


    current_filters = {s["column"]: s["values"] for s in st.session_state.selections if s["values"]}
    st.session_state.user_choices = [current_filters] if current_filters else []


    filtered_df, remaining_df = split_utils.filter_dataframe(data, st.session_state.user_choices)

    segment_training_size = round(filtered_df.shape[0] * train_size_percentage / 100)
    total_training_size = segment_training_size + remaining_df.shape[0]
    holdout_size = filtered_df.shape[0] - segment_training_size if not st.session_state["remove_baseline"] else filtered_df.shape[0] - 2*segment_training_size

    with dataset_summary:
        st.write("### Dataset Summary:")
        row1 = st.columns(3)
        st.write("##### Split Simulation")
        row2 = st.columns(4) if st.session_state["with_baseline"] else st.columns(3)

        with row1[0]:
            tile = st.container(height=120)
            tile.metric(label="Original Dataset", value=f"{data.shape[0]}")

        with row1[1]:
            tile = st.container(height=120)
            tile.metric(label="Number of Columns", value=f"{data.shape[1]}")

        with row1[2]:
            tile = st.container(height=120)
            segment_percentage = round(filtered_df.shape[0] * 100 / data.shape[0], 2)
            tile.metric(label="Segment Size", value=f"{filtered_df.shape[0]}", delta=f"{segment_percentage}%")

        with row2[0]:
            tile = st.container(height=120)
            segment_train_percentage = round(segment_training_size * 100 / data.shape[0], 2)
            tile.metric(label="Segment Train Size", value=f"{segment_training_size}", delta=f"{segment_train_percentage}%")

        with row2[1]:
            tile = st.container(height=120)
            total_train_percentage = round(total_training_size * 100 / data.shape[0], 2)
            tile.metric(label="Total Train Size", value=f"{total_training_size}", delta=f"{total_train_percentage}%")

        with row2[2]:
            tile = st.container(height=120)
            holdout_percentage = round(holdout_size * 100 / data.shape[0], 2)
            tile.metric(label="Holdout Size", value=f"{holdout_size} ", delta=f"{holdout_percentage}%")

        if st.session_state["with_baseline"]:
            with row2[3]:
                tile = st.container(height=120)
                baseline_size = segment_training_size * 2
                baseline_percentage = round(baseline_size * 100 / data.shape[0], 2)
                tile.metric(label="Baseline Size", value=f"{baseline_size}", delta=f"{baseline_percentage}%")

    with plot:
        split_utils.plot_training_holdout(
            total_training_size=total_training_size, 
            holdout_size=holdout_size, 
            segment_training_size=segment_training_size
        )

    split_row = st.columns(3)

    with split_row[1]:
        if st.button("Split Data", key="targeted_split_button", use_container_width=True, type="primary"):
            files_utils.empty_folder("outputs")

            # Generate multiple random states if bootstrapping is enabled, otherwise set to None
            random_states = [random.randint(1, 100) for _ in range(st.session_state["boostrap_occurences"])] if st.session_state["boostrap"] else None

            # Perform dataset splitting
            split_results = split_utils.targeted_split(
                st.session_state["data"], 
                train_size=train_size_percentage / 100, 
                baseline=st.session_state["with_baseline"], 
                remove_baseline=st.session_state["remove_baseline"], 
                random_states=random_states,
                filters=st.session_state["selections"]
            )

            # Save results for each split (single or multiple depending on bootstrapping)
            for idx, (train_df, holdout_df, baseline_df) in enumerate(split_results):
                suffix = f"_batch_{idx+1}" if st.session_state["boostrap"] else ""

                files_utils.save_file(df=train_df, metadata=meta, file_path=f"outputs/train_{total_training_size}{suffix}" + "." + st.session_state["file_type"])
                files_utils.save_file(df=holdout_df, metadata=meta, file_path=f"outputs/holdout_{holdout_size}{suffix}" + "." + st.session_state["file_type"])

                if st.session_state["with_baseline"]:
                    files_utils.save_file(df=baseline_df, metadata=meta, file_path=f"outputs/baseline_{baseline_size}{suffix}" + "." + st.session_state["file_type"])

            st.success("Data has been successfully split!")