import streamlit as st
import pandas as pd

data = pd.read_csv("taxi-trips.csv")

selected_company = st.selectbox(label="Company", options=data["Company"].unique(), index=None)

if selected_company != None:
    st.metric(label="Trips", value=data.groupby(["Company"]).size()[selected_company])
else:
    st.metric(label="Trips", value=data.groupby(["Company"]).size().sum())
