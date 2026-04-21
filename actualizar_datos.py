import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
from datetime import datetime
import os
import io

# ─── CONFIGURACIÓN GENERAL ───
st.set_page_config(layout="wide", page_title="Reporte Los Brujos")

plt.rcParams['figure.dpi'] = 200
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.weight'] = 'bold'

COLORES = {
    2023: "#FFC107",
    2024: "#8BC34A",
    2025: "#009688",
    2026: "#E64A19"
}

ARCHIVO = "datos_actualizados.csv"

# ─── CARGA RÁPIDA ───
@st.cache_data(ttl=300, show_spinner="⚡ Cargando datos...")
def cargar_csv():
    try:
        df = pd.read_csv(ARCHIVO, encoding="utf-8-sig")
        df["Fecha_Grafico"] = pd.to_datetime(df["Fecha_Grafico"])
        return df
    except:
        return pd.DataFrame()

# ─── ETIQUETAS ───
def label_smart(ax, x, y, val, color, offset_y):
    ax.annotate(
        f"{val}",
        xy=(x, y),
        xytext=(0, offset_y),
        textcoords="offset points",
        ha='center',
        va='center',
        fontsize=11,
        fontweight='bold',
        color='white',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=color, edgecolor='none', alpha=0.9),
        zorder=10
    )

# ─── INTERFAZ ───
st.title("📊 Control de Temperaturas - Los Brujos")

# Info de actualización
if os.path.exists(ARCHIVO):
    mod_time = os.path.getmtime(ARCHIVO)
    st.caption(f"🕒 Última actualización: {datetime.fromtimestamp(mod_time).strftime('%d-%m %H:%M')}")

# Sidebar
anios_sel = st.sidebar.multiselect(
    "Años a comparar",
    [2023, 2024, 2025, 2026],
    default=[2023, 2024, 2025, 2026]
)

if st.sidebar.button("🔄 Actualizar vista"):
    st.cache_data.clear()
    st.rerun()

# ─── DATOS ───
df = cargar_csv()

if "Anio" not in df.columns:
    st.error("❌ No hay datos válidos. Ejecuta actualizar_datos.py")
    st.stop()

df = df[df["Anio"].isin(anios_sel)]

# ─── GRÁFICO ───
if not df.empty:

    ANIOS_PRESENTES = sorted(df['Anio'].unique())

    fig, (ax_max, ax_min) = plt.subplots(
        2, 1,
        figsize=(24, 14),
        dpi=200,
        sharex=True,
        gridspec_kw={'hspace': 0.18}
    )

    fig.patch.set_facecolor('white')

    for ax in [ax_max, ax_min]:
        ax.set_facecolor('white')
        ax.grid(True, linestyle=':', alpha=0.3, color='grey', zorder=0)
        ax.yaxis.set_major_locator(MultipleLocator(4))
        ax.tick_params(axis='y', labelsize=13, labelcolor='#333333', pad=10)

        # Quitar bordes innecesarios
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        fechas_unicas = pd.to_datetime(df['Fecha_Grafico'].unique())
        for f in fechas_unicas:
            if f.weekday() == 0:
                ax.axvline(f, color='#333333', linestyle=(0, (5, 5)), lw=2, alpha=0.4, zorder=1)

    # Líneas
    for anio in ANIOS_PRESENTES:
        df_a = df[df['Anio'] == anio].sort_values("Fecha_Grafico")
        color = COLORES.get(int(anio), "grey")

        ax_max.plot(df_a['Fecha_Grafico'], df_a['Max_Dia'],
                    color=color, lw=4, marker='o', markersize=9)

        ax_min.plot(df_a['Fecha_Grafico'], df_a['Min_Dia'],
                    color=color, lw=4, marker='s', markersize=8)

    # Etiquetas
    for f in df['Fecha_Grafico'].unique():
        for sub_df, ax, is_max in [
            (df[df['Fecha_Grafico']==f].sort_values("Max_Dia"), ax_max, True),
            (df[df['Fecha_Grafico']==f].sort_values("Min_Dia"), ax_min, False)
        ]:
            usados = []
            for _, row in sub_df.iterrows():
                val = row['Max_Dia'] if is_max else row['Min_Dia']
                offset = 16
                while any(abs(offset - u) < 22 for u in usados):
                    offset += 22
                label_smart(ax, row['Fecha_Grafico'], val, val,
                            COLORES.get(int(row['Anio']), "grey"), offset)
                usados.append(offset)

    # Rangos
    ax_max.set_ylim(df['Max_Dia'].min() - 2, df['Max_Dia'].max() + 7)
    ax_min.set_ylim(df['Min_Dia'].min() - 4, df['Min_Dia'].max() + 6)

    ax_max.set_ylabel('Máxima °C', fontsize=15)
    ax_min.set_ylabel('Mínima °C', fontsize=15)

    # Eje X completo
    rango = pd.date_range(df['Fecha_Grafico'].min(), df['Fecha_Grafico'].max())
    ax_min.set_xticks(rango)
    ax_min.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))

    plt.xticks(rotation=45, ha='right', fontsize=13)

    fig.suptitle(
        'HISTÓRICO DE TEMPERATURA DIARIA (MAX-MIN) – LOS BRUJOS',
        fontsize=36, color='red', y=0.98
    )

    # Leyenda
    parches = [mpatches.Patch(color=COLORES.get(a), label=f"Año {a}") for a in ANIOS_PRESENTES]

    fig.legend(
        handles=parches,
        loc='lower center',
        bbox_to_anchor=(0.5, 0.02),
        ncol=len(ANIOS_PRESENTES),
        fontsize=18,
        frameon=True,
        shadow=True
    )

    plt.subplots_adjust(top=0.91, bottom=0.15, left=0.06, right=0.98)

    # Mostrar
    st.pyplot(fig)

    # ─── DESCARGA IMAGEN HD ───
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)

    st.download_button(
        label="📥 Descargar imagen HD",
        data=buf,
        file_name="reporte_temperaturas_hd.png",
        mime="image/png"
    )

    # ─── DESCARGA CSV ───
    st.download_button(
        "📥 Descargar CSV",
        df.to_csv(index=False),
        "datos_los_brujos.csv"
    )

else:
    st.warning("⚠️ No hay datos disponibles.")