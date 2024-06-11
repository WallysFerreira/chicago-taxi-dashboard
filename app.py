import datetime
import streamlit as st
import pandas as pd
import pydeck as pdk

@st.cache_data
def load_data():
    url = "https://www.dropbox.com/scl/fi/ftt2wzhzpjbemcovcayl0/taxi-trips.csv?rlkey=sxyqqsdmoug4mhpb1raiiugws&st=zy6h9ru0&dl=1"
    data = pd.read_csv(url)
    data = data.rename(columns={"Pickup Centroid Latitude": "latitude", "Pickup Centroid Longitude": "longitude"})

    return data

data = load_data()

selected_company = st.selectbox(label="Company", options=data["Company"].unique(), index=None)

default_date_start = datetime.date(2024, 1, 1)
default_date_end = datetime.date(2024, 3, 1)
selected_date_range = st.date_input("Date", (default_date_start, default_date_end), default_date_start, default_date_end)

if selected_company != None:
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Trips", value=data.groupby(["Company"]).size()[selected_company])

    with col2:
        st.metric(label="Amount made", value='${:,.2f}'.format(data[data["Company"] == selected_company]["Trip Total"].sum()))

    heatmap_prepared_data = data[data["Company"] == selected_company].dropna(subset=["latitude"]).groupby(["latitude", "longitude"], as_index=False).size()

    st.subheader("Trips heatmap", divider="rainbow")
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'HeatmapLayer',
                data=heatmap_prepared_data,
                get_position='[longitude, latitude]',
                get_weight='size',
                radius=1000,
                pickable=False,
                extruded=True,
            ),
        ],
    ))
else:
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Trips", value=data.groupby(["Company"]).size().sum())
        st.metric(label="Average fare", value='${:,.2f}'.format(20.33))

    with col2:
        st.metric(label="Amount made", value='${:,.2f}'.format(data["Trip Total"].sum()))
        st.metric(label="Average tip", value='${:,.2f}'.format(2.15))

    st.subheader("Most used payment types", divider="rainbow")
    # Bar chart

    # Map

    heatmap_prepared_data = data.dropna(subset=["latitude"]).groupby(["latitude", "longitude"], as_index=False).size()

    st.subheader("Trips heatmap", divider="rainbow")
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'HeatmapLayer',
                data=heatmap_prepared_data,
                get_position='[longitude, latitude]',
                radius=500,
                get_weight='size',
                pickable=False,
                extruded=True,
            ),
        ],
    ))


    st.subheader("Fare map", divider="rainbow")

    st.subheader("Tip map", divider="rainbow")


