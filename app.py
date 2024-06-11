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

if selected_company != None:
    st.metric(label="Trips", value=data.groupby(["Company"]).size()[selected_company])

    pydeck_prepared_data = data[data["Company"] == selected_company].dropna(subset=["latitude"]).groupby(["latitude", "longitude"], as_index=False).size()

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
                data=pydeck_prepared_data,
                get_position='[longitude, latitude]',
                get_weight='size',
                radius=1000,
                pickable=False,
                extruded=True,
            ),
        ],
    ))
else:
    st.metric(label="Trips", value=data.groupby(["Company"]).size().sum())

    pydeck_prepared_data = data.dropna(subset=["latitude"]).groupby(["latitude", "longitude"], as_index=False).size()

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
                data=pydeck_prepared_data,
                get_position='[longitude, latitude]',
                radius=500,
                get_weight='size',
                pickable=False,
                extruded=True,
            ),
        ],
    ))
