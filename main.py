#!/usr/bin/env python3
# ======================================
# IMPORTS
# ======================================
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import paramiko
import re
import time
import json
import os
from datetime import datetime, timedelta


# ======================================
# CONFIGURACIÓN STREAMLIT
# ======================================
st.set_page_config(page_title="CALLAN COOLING MONITOR", layout="wide")
st.title("CALLAN COOLING MONITOR")


# ======================================
# CREDENCIALES SSH
# ======================================
USER = os.getenv("SSH_USERNAME")
PASSWORD = os.getenv("SSH_PASSWORD")


# ======================================
# INVENTARIO DE IPS CALLANS (JSON)
# ======================================
with open("callans.json", "r") as f:
    data = json.load(f)

ips_asignadas = {int(k): v for k, v in data["callans"].items()}


# ======================================
# FUNCIONES SSH
# ======================================
def esperar_prompt(canal, texto_esperado="RScmCli#", timeout=30):
    salida = ""
    canal.settimeout(timeout)
    inicio = time.time()

    while True:
        if time.time() - inicio > timeout:
            raise TimeoutError(f"Timeout esperando: {texto_esperado}")

        if canal.recv_ready():
            salida += canal.recv(1024).decode("utf-8", errors="ignore")
            if texto_esperado in salida:
                break

        time.sleep(0.1)

    return salida


# ======================================
# OBTENCIÓN DE TEMPERATURAS EN TIEMPO REAL
# ======================================
def obtener_temperaturas(ip):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=USER, password=PASSWORD, timeout=5)

        canal = ssh.invoke_shell()
        esperar_prompt(canal)
        canal.send("show cdu fan info\n")
        salida = esperar_prompt(canal)

        ssh.close()

        temp_air = re.search(r"Temp Air Cold Average:\s*([\d.]+)", salida)
        temp_liquid = re.search(r"Temp Liquid Supply:\s*([\d.]+)", salida)

        return {
            "timestamp": datetime.now(),
            "temp_air": float(temp_air.group(1)) if temp_air else None,
            "temp_liquid": float(temp_liquid.group(1)) if temp_liquid else None,
        }

    except Exception as e:
        return {"timestamp": datetime.now(), "error": str(e)}


# ======================================
# INICIALIZACIÓN DE SESIÓN
# ======================================
for i in range(1, 17):
    key = f"data_callan{i}"
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(
            columns=["timestamp", "temp_air", "temp_liquid"]
        )


# ======================================
# LAYOUT ESTÁTICO
# ======================================
placeholders = {}
for i in range(1, 17):
    with st.container():
        st.markdown(f"### CALLAN #{i}")
        placeholders[i] = st.empty()


# ======================================
# MONITOREO CONTINUO
# ======================================
try:
    while True:
        for i, ip in ips_asignadas.items():
            registro = obtener_temperaturas(ip)
            placeholder = placeholders[i]

            if "error" not in registro:
                df = st.session_state[f"data_callan{i}"]
                df = pd.concat([df, pd.DataFrame([registro])], ignore_index=True)
                df = df[df["timestamp"] > datetime.now() - timedelta(hours=24)]
                st.session_state[f"data_callan{i}"] = df

                with placeholder.container():
                    fig = go.Figure()
                    fig.add_trace(
                        go.Scatter(
                            x=df["timestamp"],
                            y=df["temp_air"],
                            mode="lines+markers",
                            name="Air Temp (°C)",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=df["timestamp"],
                            y=df["temp_liquid"],
                            mode="lines+markers",
                            name="Liquid Temp (°C)",
                        )
                    )
                    fig.update_layout(
                        title=f"Temperaturas CALLAN #{i} (Últimas 24h)",
                        xaxis_title="Hora",
                        yaxis_title="Temperatura (°C)",
                        yaxis=dict(range=[0, 60]),
                        template="plotly_dark",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            else:
                with placeholder.container():
                    st.markdown(
                        "<p style='color:red;'>Sin conexión</p>",
                        unsafe_allow_html=True,
                    )

        time.sleep(5)

except Exception as e:
    st.error(f"Error ejecutando monitoreo: {e}")
