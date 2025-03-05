#!/usr/bin/env python
# coding: utf-8

# In[27]:
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt  # ✅ Gebruik Matplotlib in plaats van Plotly
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

# 📊 **Grafiek: Aantal vluchten per bestemming (Matplotlib)**
if 'route.destinations' in df.columns:
    st.subheader("🌍 Aantal Vluchten per Bestemming")
    df_dest_count = df['route.destinations'].value_counts()

    fig, ax = plt.subplots()
    df_dest_count.plot(kind='bar', color='blue', ax=ax)
    ax.set_xlabel("Bestemming")
    ax.set_ylabel("Aantal Vluchten")
    ax.set_title("Top Bestemmingen")

    st.pyplot(fig)

# 📊 **Boxplot: Spreiding van vertragingen in minuten (Matplotlib)**
if 'landingDelay' in df.columns:
    st.subheader("⏳ Vertragingen bij Landingen (in Minuten)")

    fig, ax = plt.subplots()
    ax.boxplot(df['landingDelay'].dropna(), vert=True, patch_artist=True)
    ax.set_ylabel("Vertraging (minuten)")
    ax.set_title("Spreiding van Vertragingen")

    st.pyplot(fig)

# 📊 **Scatter plot: Vertraging per bestemming (Matplotlib)**
if 'route.destinations' in df.columns and 'landingDelay' in df.columns:
    st.subheader("🎯 Vertraging vs. Bestemming")

    fig, ax = plt.subplots()
    ax.scatter(df['route.destinations'], df['landingDelay'], alpha=0.5, color='red')
    ax.set_xlabel("Bestemming")
    ax.set_ylabel("Vertraging (minuten)")
    ax.set_title("Vertragingen per Bestemming")

    st.pyplot(fig)

# 📊 **Pie-chart: Aantal vluchten per pier (Matplotlib)**
if 'pier' in df.columns:
    st.subheader("🏗 Aantal Vluchten per Pier")
    df_pier_count = df['pier'].value_counts()

    fig, ax = plt.subplots()
    ax.pie(df_pier_count, labels=df_pier_count.index, autopct='%1.1f%%', colors=plt.cm.Paired.colors)
    ax.set_title("Verdeling Vluchten per Pier")

    st.pyplot(fig)
