import streamlit as st
import pandas as pd
from utils import files_utils
import numpy as np
import plotly.graph_objects as go


def compare_dataframes_pivot(df1, df2):
    """
    Compare two DataFrames in a structured pivot format with percentages using Plotly Table.
    Returns a Plotly figure.
    """

    # Find common columns
    common_columns = list(set(df1.columns) & set(df2.columns))
    if not common_columns:
        st.sidebar.error("❌ No common columns found!")
        return None

    # Lists to store table content
    column_labels = []
    values_col = []
    df1_percent = []
    df2_percent = []

    for col in common_columns:
        # Compute percentages
        df1_counts = df1[col].value_counts(normalize=True) * 100
        df2_counts = df2[col].value_counts(normalize=True) * 100

        # Merge counts
        merged_counts = pd.merge(df1_counts.rename("df1 (%)"),
                                 df2_counts.rename("df2 (%)"),
                                 left_index=True, right_index=True, how="outer").fillna(0)

        # Round values
        merged_counts = merged_counts.round(2)

        # Append column header row (for grouping)
        column_labels.append(f"{col}")
        values_col.append("")
        df1_percent.append("")
        df2_percent.append("")

        # Append each value with percentages
        for value, row in merged_counts.iterrows():
            column_labels.append("")  # Keep the column header above
            values_col.append(str(value))
            df1_percent.append(f"{row['df1 (%)']}%")
            df2_percent.append(f"{row['df2 (%)']}%")

    # Create Plotly Table with full-width layout
    fig = go.Figure(data=[go.Table(
        columnwidth=[20, 20, 20, 20],  # Increase column width to avoid scrolling
        header=dict(
            values=["Column", "Value", "df1 (%)", "df2 (%)"],
            fill_color="lightgrey",
            align="center",
            font=dict(size=15, color="black")
        ),
        cells=dict(
            values=[column_labels, values_col, df1_percent, df2_percent],
            fill=dict(color=[["white"] * len(column_labels)]),
            align="left",
            font=dict(size=13, color="black")
        )
    )])

    # Ensure the table takes full width
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=10), width=1000, height=600)

    return fig


def app():
    st.write("### Validation Process")

    # File upload
    uploaded_file = st.file_uploader(
        "Drag & Drop or Click to Upload",
        type=["csv", "xlsx", "sav"],
        key="fairset_uploader"
    )

    if uploaded_file:
        try:
            # Save and load the file
            fairset_path = files_utils.save_uploaded_file(uploaded_file)
            fairset, fairset_meta = files_utils.load_file(fairset_path)

            if fairset is not None:
                # Store in session_state
                st.session_state["fairset"] = fairset
                st.session_state["fairset_meta"] = fairset_meta
                st.session_state["fairset_path"] = fairset_path
                file_type = fairset_path.split(".")[-1]
                st.session_state["fairset_type"] = file_type
                
                st.sidebar.success(f"✅ {file_type.upper()} file successfully loaded!")

                # Ensure comparison is done with stored data
                if "data" in st.session_state:
                    # Generate Plotly table
                    fig = compare_dataframes_pivot(st.session_state["data"], fairset)

                    # Display table in Streamlit
                    st.write("### Tri croisé avec proportions (%)")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.sidebar.error("❌ 'data' not found in session_state.")
                    
            else:
                st.sidebar.error("❌ Error Uploading")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading file: {str(e)}")
    else:
        st.sidebar.info("📂 Upload a file to begin.")