import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ============================
# LOAD METADATA
# ============================
@st.cache_data
def load_state_metadata(path: str = "data/state_metadata.csv"):
    df = pd.read_csv(path)
    required = {"state_code", "state_name", "display_title", "visual_path", "raw_data_path"}
    missing = required - set(df.columns)
    if missing:
        st.error(f"Metadata file is missing columns: {missing}")
    return df

state_meta = load_state_metadata()

st.set_page_config(page_title="InsightLegi – Fines & Fees", layout="wide")
st.title("InsightLegi — Fines & Fees Across States")
st.markdown("Click a state on the map OR choose one from the sidebar.")

# ============================
# BUILD CHOROPLETH
# ============================
state_meta["value"] = 1  # keeps all states colored

fig = px.choropleth(
    state_meta,
    locations="state_code",
    locationmode="USA-states",
    color="value",
    scope="usa",
    hover_name="state_name",
    color_continuous_scale=px.colors.sequential.Blues
)

fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
fig.update_traces(marker_line_width=0.3)

# ============================
# CLICK HANDLING
# ============================
click_event = st.plotly_chart(
    fig,
    use_container_width=True,
    key="us_map_chart",
    on_select="rerun"
)

if "us_map_chart" in st.session_state:
    selected_points = st.session_state["us_map_chart"].get("selection", None)
else:
    selected_points = None

if selected_points and "points" in selected_points and len(selected_points["points"]) > 0:
    clicked_state_code = selected_points["points"][0]["location"]
    st.session_state["selected_state_code"] = clicked_state_code

# ============================
# SIDEBAR SELECTION FALLBACK
# ============================
state_options = dict(zip(state_meta["state_name"], state_meta["state_code"]))

if "selected_state_code" in st.session_state:
    code = st.session_state["selected_state_code"]
    preselect_name = state_meta[state_meta["state_code"] == code]["state_name"].iloc[0]
else:
    preselect_name = list(state_options.keys())[0]

selected_state = st.sidebar.selectbox(
    "Choose a State",
    list(state_options.keys()),
    index=list(state_options.keys()).index(preselect_name)
)

selected_code = state_options[selected_state]
st.session_state["selected_state_code"] = selected_code

# ============================
# LOAD ROW FOR SELECTED STATE
# ============================
row = state_meta[state_meta["state_code"] == selected_code].iloc[0]

st.subheader(row["display_title"])

# ============================
# DISPLAY PNG VISUALS
# ============================
try:
    visual_folder = Path(row["visual_path"])

    if visual_folder.exists() and visual_folder.is_dir():
        png_files = sorted(visual_folder.glob("*.png"))

        if png_files:
            for i in range(0, len(png_files), 2):
                col1, col2 = st.columns([1, 1], gap="large")

                with col1:
                    st.image(str(png_files[i]), use_container_width=True)

                if i + 1 < len(png_files):
                    with col2:
                        st.image(str(png_files[i + 1]), use_container_width=True)
                else:
                    col2.write("")
        else:
            st.warning("No PNG images found.")
    else:
        st.warning(f"Visual folder missing: {visual_folder}")

except Exception as e:
    st.warning(f"Could not load images: {e}")

# ============================
# RAW DATA PREVIEW
# ============================
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