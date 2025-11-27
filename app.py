import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

@st.cache_data
def load_state_metadata(path: str = "data/state_metadata.csv"):
    df = pd.read_csv(path)
    required = {"state_code", "state_name", "display_title", "visual_path", "raw_data_path"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Metadata file is missing columns: {missing}")
    return df

# Load metadata
state_meta = load_state_metadata()

st.set_page_config(page_title="InsightLegi – Fines & Fees", layout="wide")
st.title("InsightLegi — Fines & Fees Across States")
st.markdown("Select a state to view its visualization and raw data.")

# Choropleth map
state_meta["value"] = 1
fig = px.choropleth(
    state_meta,
    locations="state_code",
    locationmode="USA-states",
    color="value",
    scope="usa",
    hover_name="state_name"
)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True, key="us_map_chart")

# Sidebar state selection
st.sidebar.header("State Details")
state_options = dict(zip(state_meta["state_name"], state_meta["state_code"]))
selected_state = st.sidebar.selectbox("Choose a State", list(state_options.keys()))
row = state_meta[state_meta["state_name"] == selected_state].iloc[0]

# Display selected state title
st.subheader(row["display_title"])

# --- Show all PNG visualizations in order, perfectly aligned in rows of 2 ---
try:
    visual_folder = Path(row["visual_path"])

    if visual_folder.exists() and visual_folder.is_dir():
        png_files = sorted(visual_folder.glob("*.png"))

        if png_files:
            # Display 2 images per row with perfect alignment
            for i in range(0, len(png_files), 2):
                col1, col2 = st.columns([1, 1], gap="large")

                # Left image
                with col1:
                    st.image(str(png_files[i]), use_container_width=True)

                # Right image, only if it exists
                if i + 1 < len(png_files):
                    with col2:
                        st.image(str(png_files[i + 1]), use_container_width=True)
                else:
                    # Ensure visual alignment by keeping the row structure
                    col2.write("")
        else:
            st.warning("No PNG files found in the folder.")
    else:
        st.warning(f"Visual folder does not exist: {visual_folder}")

except Exception as e:
    st.warning(f"Could not load images: {e}")

# --- Show raw data ---
st.markdown("#### Raw Data Preview")
try:
    raw_df = pd.read_csv(row["raw_data_path"])
    st.dataframe(raw_df.head(20))

    st.download_button(
        label=f"Download {row['state_code']} Raw Data",
        data=raw_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{row['state_code']}_raw.csv",
        mime="text/csv"
    )
except Exception as e:
    st.warning(f"Could not load raw data: {e}")

