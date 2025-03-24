import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import streamlit as st
from sklearn.model_selection import train_test_split

def random_split(df: pd.DataFrame, train_size: float = 0.1, baseline: bool = True, remove_baseline: bool = True, random_states=None):
    """
    Splits the dataset into train, holdout, and optionally a baseline.
    """
    if not isinstance(random_states, list):
        random_states = [None]  # Default to a single random split without a seed

    results = []

    for seed in random_states:
        if not baseline:
            # Standard train-test split when baseline is not needed
            train_df, holdout_df = train_test_split(df, train_size=train_size, random_state=seed)
            results.append((train_df, holdout_df, None))
            continue

        # Compute baseline size as twice the training size
        baseline_size = min(2 * train_size, 1.0)  # Ensure it doesn't exceed dataset size

        baseline_df, holdout_df = train_test_split(df, train_size=baseline_size, random_state=seed)

        # Half of the baseline is assigned to training
        train_df, _ = train_test_split(baseline_df, train_size=0.5, random_state=seed)

        if remove_baseline:
            # Remove all baseline data from holdout
            holdout_df = holdout_df.loc[~holdout_df.index.isin(baseline_df.index)]
        else:
            # Only remove train indexes from holdout
            holdout_df = holdout_df.loc[~holdout_df.index.isin(train_df.index)]

        results.append((train_df, holdout_df, baseline_df))

    return results


def filter_dataframe(data: pd.DataFrame, filters: list):
    """
    Filters a DataFrame based on a list of column-value mappings from JSON.
    """
    if not filters:
        return data, pd.DataFrame()  
    filtered_df = data.copy()
    
    for filter_dict in filters:
        for column, values in filter_dict.items():

            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].isin(values)]
    
    remaining_df = data.drop(filtered_df.index)

    return filtered_df, remaining_df


def plot_training_holdout(total_training_size, holdout_size, segment_training_size=None):
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(5, 6))

    # Prepare data, labels, and colors
    if segment_training_size is not None:
        rest_training_size = total_training_size - segment_training_size
        sizes = [segment_training_size, rest_training_size, holdout_size]
        labels = ["Training Segment", "Training", "Holdout"]
        colors = ["#f34b4c", "#f8b7ba", "#f0f2f6"]
    else:
        sizes = [total_training_size, holdout_size]
        labels = ["Training", "Holdout"]
        colors = ["#f34b4c", "#f0f2f6"]

    # Draw the donut, shifting it upward by setting the center to (0, 0.2)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        startangle=140,
        wedgeprops={'edgecolor': 'white'},
        autopct='%1.1f%%',
        textprops={'fontsize': 12, 'color': 'black'},
        radius=0.8,
        pctdistance=0.70,
        center=(0, 0.2)
    )

    # Ensure text is black
    for text in texts:
        text.set_color("black")

    # Add the white center circle to complete the donut look
    center_circle = plt.Circle((0, 0.2), 0.4, fc='white')
    ax.add_artist(center_circle)

    # Set equal aspect ratio and remove axes visuals
    ax.set_aspect('equal')
    ax.axis('off')

    # Remove extra margins around the figure
    fig.subplots_adjust(top=1, bottom=0, left=0, right=1)
    
    # Adjust the y-axis limits to remove top padding:
    ax.set_ylim(-0.6, 1.0)

    # Optional: Move legend to the bottom
    fig.legend(
        wedges, labels,
        loc="lower center",
        ncol=len(labels),
        fontsize=12,
        frameon=False,
        bbox_to_anchor=(0.5, 0.05)
    )
    
    st.pyplot(fig, clear_figure=True, use_container_width=True)


def targeted_split(df: pd.DataFrame, filters: list, train_size: float = 0.1, baseline: bool = True, remove_baseline: bool = True, random_states=None):
    """
    Splits the dataset into train, holdout, and optionally a baseline, based on specific segment filters.
    """
    if not isinstance(random_states, list):
        random_states = [None]  # Default to a single split with no specific seed
    
    # Apply filtering based on the conditions
    mask = pd.Series(True, index=df.index)
    for condition in filters:
        column, values = condition["column"], condition["values"]
        mask &= df[column].isin(values)
    
    segment_df = df[mask]  # Data matching the filter conditions
    rest_df = df[~mask]  # Data that doesn't match the filter conditions
    
    results = []
    
    for seed in random_states:
        if not baseline:
            # No baseline, just a train-test split
            if len(segment_df) == 0:
                train_df, holdout_df = rest_df, pd.DataFrame()
            else:
                train_segment, holdout_segment = train_test_split(segment_df, train_size=train_size, random_state=seed)
                train_df = pd.concat([train_segment, rest_df])
                holdout_df = holdout_segment
            results.append((train_df, holdout_df, None))
            continue
        
        # Compute baseline size (2x train_size of the segment)
        baseline_size = min(2 * train_size, 1.0)  # Ensure it doesn't exceed available data
        if len(segment_df) == 0:
            results.append((rest_df, pd.DataFrame(), None))
            continue
        
        baseline_df, holdout_segment = train_test_split(segment_df, train_size=baseline_size, random_state=seed)
        
        # Train is half of the baseline
        train_df, _ = train_test_split(baseline_df, train_size=0.5, random_state=seed)
        
        if remove_baseline:
            # Holdout should exclude the entire baseline
            holdout_df = holdout_segment.loc[~holdout_segment.index.isin(baseline_df.index)]
        else:
            # Holdout should only exclude the train portion
            holdout_df = holdout_segment.loc[~holdout_segment.index.isin(train_df.index)]
            
            # Extend the baseline with another train-sized sample from the segment (without replacement)
            if len(holdout_segment) >= len(train_df):
                extra_baseline_sample = holdout_segment.sample(n=len(train_df), random_state=seed, replace=False)
                baseline_df = pd.concat([baseline_df, extra_baseline_sample])
        
        # Add the rest of the data to train
        train_df = pd.concat([train_df, rest_df])
        
        results.append((train_df, holdout_df, baseline_df))
    
    return results





