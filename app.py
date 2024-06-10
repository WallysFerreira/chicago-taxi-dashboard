import streamlit as st
import pandas as pd

data = pd.read_csv("taxi-trips.csv")

st.write(data.groupby(["Company"]).size())
