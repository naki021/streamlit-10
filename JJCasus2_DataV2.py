#!/usr/bin/env python
# coding: utf-8

# In[27]:
import streamlit as st
import requests
import pandas as pd
import plotly as plt 
from io import StringIO

# Streamlit titel
st.title("✈️ Schiphol Vluchtdata Dashboard")

# API URL en headers
API_URL = "https://api.schiphol.nl/public-flights/flights?includedelays=false&page={}&sort=%2BscheduleTime"
HEADERS = {
    "app_id": "c93492b2",
    "app_key": "16a5764ed747d28fc0c58196e7322a04",
    'ResourceVersion': 'v4'
}

# Ophalen van vluchtgegevens
@st.cache_data
def fetch_flight_data(pages=10):
    all_flights_data = []
    for page in range(pages):
        response = requests.get(API_URL.format(page), headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            flights_data = data.get('flights', [])
            all_flights_data.extend(flights_data)
    return pd.json_normalize(all_flights_data)

# Haal vluchtgegevens op
pages = st.sidebar.slider("📂 Aantal pagina's op te halen", 1, 50, 10)
df = fetch_flight_data(pages)

# ✅ **Vertraging berekenen in MINUTEN**
if 'actualLandingTime' in df.columns and 'estimatedLandingTime' in df.columns:
    df['actualLandingTime'] = pd.to_datetime(df['actualLandingTime'], errors='coerce')
    df['estimatedLandingTime'] = pd.to_datetime(df['estimatedLandingTime'], errors='coerce')
    df['landingDelay'] = (df['actualLandingTime'] - df['estimatedLandingTime']).dt.total_seconds() / 60  # 🔹 Omgezet naar minuten

# 🔹 **FIX: Zorg dat 'route.destinations' een string wordt**
if 'route.destinations' in df.columns:
    df['route.destinations'] = df['route.destinations'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)

# 🔹 **SLIDER: Filter vluchten op maximale vertraging (nu in minuten)**
if 'landingDelay' in df.columns:
    max_delay = st.sidebar.slider("⏳ Maximale vertraging (minuten)", 0, 60, 10)  # 🔹 Nu in minuten
    df = df[df['landingDelay'] <= max_delay]

# 🔹 **CHECKBOX: Toon alleen vertraagde vluchten**
show_delayed = st.sidebar.checkbox("⚠️ Toon alleen vertraagde vluchten")
if show_delayed:
    df = df[df['landingDelay'] > 0]

# 🔹 **DROPDOWN: Filter op bestemming**
if 'route.destinations' in df.columns:
    unique_destinations = df['route.destinations'].dropna().unique()
    selected_destination = st.sidebar.selectbox("🌍 Kies een bestemming", ["Alle"] + list(unique_destinations))

    if selected_destination != "Alle":
        df = df[df['route.destinations'] == selected_destination]

# 🎨 **Stijlvolle Dataframe Weergave**
st.subheader("📊 Vluchtgegevens")
st.dataframe(df.head(10))

# 📊 **Grafiek: Aantal vluchten per bestemming**
if 'route.destinations' in df.columns:
    st.subheader("🌍 Aantal Vluchten per Bestemming")
    df_dest_count = df['route.destinations'].value_counts().reset_index()
    df_dest_count.columns = ['Bestemming', 'Aantal Vluchten']

    fig_dest = plt.graph_objects.Figure(data=[
        plt.graph_objects.Bar(x=df_dest_count['Bestemming'], y=df_dest_count['Aantal Vluchten'], 
               marker=dict(color=df_dest_count['Aantal Vluchten'], colorscale="Blues"),
               text=df_dest_count['Aantal Vluchten'], textposition='auto')
    ])
    fig_dest.update_layout(title="Top Bestemmingen", xaxis_title="Bestemming", yaxis_title="Aantal Vluchten")

    st.plotly_chart(fig_dest)

# 📊 **Boxplot: Spreiding van vertragingen in minuten**
if 'landingDelay' in df.columns:
    st.subheader("⏳ Vertragingen bij Landingen (in Minuten)")
    fig_delay_box = plt.graph_objects.Figure(data=[
        plt.graph_objects.Box(y=df['landingDelay'], boxpoints="all", jitter=0.3, pointpos=-1.8)
    ])
    fig_delay_box.update_layout(title="Spreiding van Vertragingen (in Minuten)", yaxis_title="Vertraging (minuten)")

    st.plotly_chart(fig_delay_box)

# 📊 **Scatter plot: Vertraging per bestemming**
if 'route.destinations' in df.columns and 'landingDelay' in df.columns:
    st.subheader("🎯 Vertraging vs. Bestemming")
    fig_scatter = plt.graph_objects.Figure(data=[
        plt.graph_objects.Scatter(x=df['route.destinations'], y=df['landingDelay'], 
                   mode='markers', marker=dict(size=10, color=df['landingDelay'], colorscale="Blues", opacity=0.7))
    ])
    fig_scatter.update_layout(title="Vertragingen per Bestemming (in Minuten)", 
                              xaxis_title="Bestemming", yaxis_title="Vertraging (minuten)")

    st.plotly_chart(fig_scatter)

# 📊 **Pie-chart: Aantal vluchten per pier**
if 'pier' in df.columns:
    st.subheader("🏗 Aantal Vluchten per Pier")
    df_pier_count = df['pier'].value_counts().reset_index()
    df_pier_count.columns = ['Pier', 'Aantal Vluchten']

    fig_pier = plt.graph_objects.Figure(data=[
        plt.graph_objects.Pie(labels=df_pier_count['Pier'], values=df_pier_count['Aantal Vluchten'])
    ])
    fig_pier.update_layout(title="Verdeling Vluchten per Pier")

    st.plotly_chart(fig_pier)
