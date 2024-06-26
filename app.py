import datetime
import streamlit as st
import pandas as pd
import pydeck as pdk
import altair as alt

def apply_color_payment(row):
    colors = {
        "Cash": "#e81416",
        "Credit Card": "#ffa500",
        "Dispute": "#faeb36",
        "Mobile": "#79c314",
        "No Charge": "#487de7",
        "Prcard": "#4b369d",
        "Unknown": "#70369d",
    }

    return colors[row["Payment Type"]]

def apply_color_weekday(row):
    colors = {
        "Sunday": "#ff2b2b",
        "Monday": "#092d52",
        "Tuesday": "#29b09d",
        "Wednesday": "#ffd16a",
        "Thursday": "#7defa1",
        "Friday": "#83c9ff",
        "Saturday": "#ffabab",
    }

    return colors[row["Weekday"]]

def apply_weekday(row):
    parsed_timestamp = datetime.datetime.strptime(row["Trip Start Timestamp"], "%m/%d/%Y %I:%M:%S %p")

    return parsed_timestamp.strftime("%A")

@st.cache_data
def load_data():
    url = "https://www.dropbox.com/scl/fi/ftt2wzhzpjbemcovcayl0/taxi-trips.csv?rlkey=sxyqqsdmoug4mhpb1raiiugws&st=zy6h9ru0&dl=1"
    data = pd.read_csv(url)
    data = data.rename(columns={"Pickup Centroid Latitude": "latitude", "Pickup Centroid Longitude": "longitude"})

    data.loc[data["Company"] == "Taxicab Insurance Agency Llc", "Company"] = "Taxicab Insurance Agency, LLC"
    data.loc[data["Company"] == "Choice Taxi Association Inc", "Company"] = "Choice Taxi Association"
    data.loc[data["Company"] == "Blue Ribbon Taxi Association Inc.", "Company"] = "Blue Ribbon Taxi Association"
    data.loc[data["Company"] == "Taxi Affiliation Services Llc - Yell", "Company"] = "Taxi Affiliation Services"

    data["Weekday"] = data.apply(apply_weekday, 1)

    return data

data = load_data()

selected_company = st.selectbox(label="Company", options=data["Company"].sort_values().unique(), index=None)

default_date_start = datetime.date(2024, 1, 1)
default_date_end = datetime.date(2024, 3, 1)
selected_date_range = st.date_input("Date", (default_date_start, default_date_end), default_date_start, default_date_end)

selected_date_start, selected_date_end = selected_date_range
data = data[(data["Trip Start Timestamp"] >= selected_date_start.strftime("%m/%d/%Y %I:%M:%S %p")) & (data["Trip Start Timestamp"] <= selected_date_end.strftime("%m/%d/%Y %I:%M:%S %p"))]

if selected_company != None:
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Trips", value=data.groupby(["Company"]).size()[selected_company])
        st.metric(label="Average fare", value='${:,.2f}'.format(data[data["Company"] == selected_company]["Fare"].mean()))
        minutes, seconds = divmod(datetime.timedelta(seconds=data[data["Company"] == selected_company]["Trip Seconds"].mean()).seconds % 3600, 60)
        st.metric(label="Average duration", value="{}m {}s".format(minutes, seconds))

    with col2:
        st.metric(label="Amount made", value='${:,.2f}'.format(data[data["Company"] == selected_company]["Trip Total"].sum()))
        st.metric(label="Average tip", value='${:,.2f}'.format(data[data["Company"] == selected_company]["Tips"].mean()))
        st.metric(label="Average distance", value='{:.2f} miles'.format(data[data["Company"] == selected_company]["Trip Miles"].mean()))

    st.subheader("Most used payment types", divider="rainbow")

    # Bar chart
    payment_bar_data = data[data["Company"] == selected_company].groupby(["Payment Type"], as_index=False).size();
    payment_bar_data["color"] = payment_bar_data.apply(apply_color_payment, axis=1)

    st.altair_chart(alt.Chart(payment_bar_data).mark_bar().encode(x="Payment Type", y="size", color=alt.Color("color").scale(None)).properties(height=500), use_container_width=True)

    # Map
    payment_map_data = data[data["Company"] == selected_company].groupby(["latitude", "longitude"], as_index=False)["Payment Type"].agg(pd.Series.mode)
    payment_map_data["Payment Type"] = payment_map_data["Payment Type"].map(lambda val : val if(isinstance(val, str)) else val[0])
    payment_map_data["color"] = payment_map_data.apply(apply_color_payment, 1)

    st.map(payment_map_data, color="color", size=300)

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

    st.subheader("Fare map", divider="rainbow")

    fare_map_data = data[data["Company"] == selected_company].groupby(["latitude", "longitude"], as_index=False)["Fare"].mean()

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.5,
            pitch=55,
        ),
        layers=[
            pdk.Layer(
                'ColumnLayer',
                data=fare_map_data,
                extruded=True,
                get_position='[longitude, latitude]',
                radius=400,
                get_elevation="Fare",
                elevation_scale=200,
                get_fill_color=['Fare / 3', 0, 'Fare * 2'],
            )
        ]
    ))

    st.subheader("Tips map", divider="rainbow")

    tips_map_data = data[data["Company"] == selected_company].groupby(["latitude", "longitude"], as_index=False)["Tips"].mean()

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.2,
            pitch=55,
        ),
        layers=[
            pdk.Layer(
                'ColumnLayer',
                data=tips_map_data,
                extruded=True,
                get_position='[longitude, latitude]',
                radius=400,
                get_elevation="Tips",
                elevation_scale=1500,
                get_fill_color=['Tips * 7 / 2', 0, 'Tips * 60'],
            )
        ]
    ))

    st.subheader("Duration map", divider="rainbow")

    duration_map_data = data[data["Company"] == selected_company].groupby(["latitude", "longitude"], as_index=False)["Trip Seconds"].mean()
    duration_map_data["time"] = duration_map_data["Trip Seconds"]
    
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.5,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ColumnLayer',
                data=duration_map_data,
                extruded=True,
                get_position='[longitude, latitude]',
                radius=200,
                get_elevation="time",
                elevation_scale=5,
                get_fill_color=['time / 10', 0, 'time * 5'],
            )
        ]
    ))

    st.subheader("Distance map", divider="rainbow")

    distance_map_data = data[data["Company"] == selected_company].groupby(["latitude", "longitude"], as_index=False)["Trip Miles"].mean()
    distance_map_data["distance"] = distance_map_data["Trip Miles"]

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=41.876984,
            longitude=-87.629704,
            zoom=8.5,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ColumnLayer',
                data=distance_map_data,
                extruded=True,
                get_position='[longitude, latitude]',
                radius=200,
                get_elevation="distance",
                elevation_scale=1100,
                get_fill_color=['distance * 10', 0, 'distance * 50'],
            )
        ]
    ))

else:
    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="Trips", value=data.groupby(["Company"]).size().sum())
        st.metric(label="Average fare", value='${:,.2f}'.format(data["Fare"].mean()))
        minutes, seconds = divmod(datetime.timedelta(seconds=data["Trip Seconds"].mean()).seconds % 3600, 60)
        st.metric(label="Average duration", value="{}m {}s".format(minutes, seconds))

    with col2:
        st.metric(label="Amount made", value='${:,.2f}'.format(data["Trip Total"].sum()))
        st.metric(label="Average tip", value='${:,.2f}'.format(data["Tips"].mean()))
        st.metric(label="Average distance", value='{:.2f} miles'.format(data["Trip Miles"].mean()))

    general_tab, companies_tab, weekdays_tab = st.tabs(["General", "Compare companies", "Weekdays"])

    with general_tab:
        st.subheader("Most used payment types", divider="rainbow")

        # Bar chart
        payment_bar_data = data.groupby(["Payment Type"], as_index=False).size();
        payment_bar_data["color"] = payment_bar_data.apply(apply_color_payment, axis=1)

        st.altair_chart(alt.Chart(payment_bar_data).mark_bar().encode(x="Payment Type", y=alt.Y("size", title="Times used"), color=alt.Color("color").scale(None)).properties(height=500), use_container_width=True)

        # Map
        payment_map_data = data.groupby(["latitude", "longitude"], as_index=False)["Payment Type"].agg(pd.Series.mode)
        payment_map_data["Payment Type"] = payment_map_data["Payment Type"].map(lambda val : val if(isinstance(val, str)) else val[0])
        payment_map_data["color"] = payment_map_data.apply(apply_color_payment, 1)

        st.map(payment_map_data, color="color", size=300)

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

        fare_map_data = data.groupby(["latitude", "longitude"], as_index=False)["Fare"].mean()

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=41.876984,
                longitude=-87.629704,
                zoom=8.5,
                pitch=55,
            ),
            layers=[
                pdk.Layer(
                    'ColumnLayer',
                    data=fare_map_data,
                    extruded=True,
                    get_position='[longitude, latitude]',
                    radius=400,
                    get_elevation="Fare",
                    elevation_scale=100,
                    get_fill_color=['Fare / 3', 0, 'Fare * 2'],
                )
            ]
        ))

        st.subheader("Tips map", divider="rainbow")

        tips_map_data = data.groupby(["latitude", "longitude"], as_index=False)["Tips"].mean()

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=41.876984,
                longitude=-87.629704,
                zoom=8.2,
                pitch=55,
            ),
            layers=[
                pdk.Layer(
                    'ColumnLayer',
                    data=tips_map_data,
                    extruded=True,
                    get_position='[longitude, latitude]',
                    radius=400,
                    get_elevation="Tips",
                    elevation_scale=1500,
                    get_fill_color=['Tips * 7 / 2', 0, 'Tips * 60'],
                )
            ]
        ))

        st.subheader("Duration map", divider="rainbow")

        duration_map_data = data.groupby(["latitude", "longitude"], as_index=False)["Trip Seconds"].mean()
        duration_map_data["time"] = duration_map_data["Trip Seconds"]
        
        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=41.876984,
                longitude=-87.629704,
                zoom=8.5,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ColumnLayer',
                    data=duration_map_data,
                    extruded=True,
                    get_position='[longitude, latitude]',
                    radius=200,
                    get_elevation="time",
                    elevation_scale=5,
                    get_fill_color=['time / 10', 0, 'time * 5'],
                )
            ]
        ))

        st.subheader("Distance map", divider="rainbow")

        distance_map_data = data.groupby(["latitude", "longitude"], as_index=False)["Trip Miles"].mean()
        distance_map_data["distance"] = distance_map_data["Trip Miles"]

        st.pydeck_chart(pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=41.876984,
                longitude=-87.629704,
                zoom=8.5,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ColumnLayer',
                    data=distance_map_data,
                    extruded=True,
                    get_position='[longitude, latitude]',
                    radius=200,
                    get_elevation="distance",
                    elevation_scale=1100,
                    get_fill_color=['distance * 10', 0, 'distance * 50'],
                )
            ]
        ))

    with companies_tab:
        company_trips_data = data.groupby(["Company"], as_index=False).size().sort_values(by=["size"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(company_trips_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("size", title="Trips completed"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

        company_amount_data = data.groupby(["Company"], as_index=False)["Trip Total"].sum().sort_values(by=["Trip Total"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(company_amount_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("Trip Total", title="Amount made (dollars)"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

        average_fare_data = data.groupby(["Company"], as_index=False)["Fare"].mean().sort_values(by=["Fare"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(average_fare_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("Fare", title="Average fare (dollars)"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

        average_seconds_data = data.groupby(["Company"], as_index=False)["Trip Seconds"].mean().sort_values(by=["Trip Seconds"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(average_seconds_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("Trip Seconds", title="Average trip duration (seconds)"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

        average_tips_data = data.groupby(["Company"], as_index=False)["Tips"].mean().sort_values(by=["Tips"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(average_tips_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("Tips", title="Average tip (dollars)"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

        average_distance_data = data.groupby(["Company"], as_index=False)["Trip Miles"].mean().sort_values(by=["Trip Miles"], ascending=False)[0:8]
        st.altair_chart(alt.Chart(average_distance_data).mark_bar().encode(x=alt.X("Company", sort="-y"), y=alt.Y("Trip Miles", title="Average distance (miles)"), color=alt.Color("Company", legend=None)).properties(height=500), use_container_width=True)

    with weekdays_tab:
        sort_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        companies_to_keep = data.groupby(["Company"], as_index=False).size().sort_values(by=["size"], ascending=False)[:15]["Company"]

        weekday_with_most_trips_per_location = data.groupby(["latitude", "longitude"], as_index=False)["Weekday"].agg(pd.Series.mode)
        weekday_with_most_trips_per_location["Weekday"] = weekday_with_most_trips_per_location["Weekday"].map(lambda val : val if(isinstance(val, str)) else val[0])
        weekday_with_most_trips_per_location["color"] = weekday_with_most_trips_per_location.apply(apply_color_weekday, 1)
        st.map(weekday_with_most_trips_per_location, color="color", size=300)

        trips_per_weekday_data = data.groupby(["Weekday"], as_index=False).size()
        st.altair_chart(alt.Chart(trips_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), y=alt.Y("size", title="Trips completed"), color=alt.Color("Weekday", legend=None)).properties(height=500), use_container_width=True)

        amount_per_weekday_data = data.groupby(["Weekday"], as_index=False)["Trip Total"].sum()
        st.altair_chart(alt.Chart(amount_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), y=alt.Y("Trip Total", title="Amount made (dollars)"), color=alt.Color("Weekday", legend=None)).properties(height=500), use_container_width=True)

        average_fare_per_weekday_data = data.groupby(["Weekday"], as_index=False)["Fare"].mean()
        st.altair_chart(alt.Chart(average_fare_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), y=alt.Y("Fare", title="Average fare (dollars)"), color=alt.Color("Weekday", legend=None)).properties(height=500), use_container_width=True)

        average_tip_per_weekday_data = data.groupby(["Weekday"], as_index=False)["Tips"].mean()
        st.altair_chart(alt.Chart(average_tip_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), y=alt.Y("Tips", title="Average tip (dollars)"), color=alt.Color("Weekday", legend=None)).properties(height=500), use_container_width=True)

        average_duration_per_weekday_data = data.groupby(["Weekday"], as_index=False)["Trip Seconds"].mean()
        st.altair_chart(alt.Chart(average_duration_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), y=alt.Y("Trip Seconds", title="Average duration (seconds)"), color=alt.Color("Weekday", legend=None)).properties(height=500), use_container_width=True)

        company_trips_per_weekday_data = data[data["Company"].isin(companies_to_keep)].groupby(["Weekday", "Company"], as_index=False).size()
        st.altair_chart(alt.Chart(company_trips_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), xOffset="Company", y=alt.Y("size", title="Trips Completed"), color=alt.Color("Company")).properties(height=500), use_container_width=True)

        company_amount_per_weekday_data = data[data["Company"].isin(companies_to_keep)].groupby(["Weekday", "Company"], as_index=False)["Trip Total"].sum()
        st.altair_chart(alt.Chart(company_amount_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), xOffset="Company", y=alt.Y("Trip Total", title="Amount made (dollars)"), color=alt.Color("Company")).properties(height=500), use_container_width=True)

        payment_type_per_weekday_data = data.groupby(["Weekday", "Payment Type"], as_index=False).size()
        st.altair_chart(alt.Chart(payment_type_per_weekday_data).mark_bar().encode(x=alt.X("Weekday", sort=sort_order), xOffset="Payment Type", y=alt.Y("size", title="Times used"), color=alt.Color("Payment Type")).properties(height=500), use_container_width=True)

