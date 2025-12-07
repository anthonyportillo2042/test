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
st.markdown("Click a state on the map OR choose one from the sidebar.")

st.markdown(
    """
    <style>
    /* Make plotly map regions use a pointer on hover */
    .plotly .layer.below > g > path,
    .plotly .choroplethlayer path {
        cursor: pointer !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- BUILD CHOROPLETH --------------------
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

# Remove margins
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
fig.update_traces(marker_line_width=0.3)

# ----- LIMIT ZOOM-OUT BUT KEEP ZOOM-IN -----
fig.update_geos(
    projection_type="albers usa",
    projection_scale=1,               # minimum zoom (default USA view)
    center={"lat": 37.8, "lon": -96}, # keeps map centered
    fitbounds="locations",            # prevents drifting outside USA
)

fig.update_layout(
    geo=dict(
        projection_scale=1,           # ensures minimum zoom stays here
        showland=True,
        showcountries=False,
        showcoastlines=False,
        lataxis=dict(range=[23, 50]),
        lonaxis=dict(range=[-130, -65]),
    )
)

# ----- CSS: pointer cursor on hover -----
st.markdown(
    """
    <style>
    .plotly .choroplethlayer path,
    .plotly .geo path,
    .plotly .layer.below path {
        cursor: pointer !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- HANDLE CLICKS --------------------
click_event = st.plotly_chart(
    fig,
    use_container_width=True,
    key="us_map_chart",
    on_select="rerun"
)

# -------------------- SIDEBAR SELECTION FALLBACK --------------------
state_options = dict(zip(state_meta["state_name"], state_meta["state_code"]))

# If map click selected a state, sync sidebar with it
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

# -------------------- LOAD THE SELECTED ROW --------------------
row = state_meta[state_meta["state_code"] == selected_code].iloc[0]

# -------------------- DISPLAY PAGE CONTENT --------------------
st.subheader(row["display_title"])

# --- PNG visualizations ---
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
                        st.image(str(png_files[i+1]), use_container_width=True)
                else:
                    col2.write("")
        else:
            st.warning("No PNG images found.")
    else:
        st.warning(f"Visual folder missing: {visual_folder}")
except Exception as e:
    st.warning(f"Could not load images: {e}")

# --- Raw data ---
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
