import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
import pandas as pd
import io

# ─── CONFIGURACIÓN ───
st.set_page_config(layout="wide")

# 🔥 CALIDAD GLOBAL
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['text.antialiased'] = True
plt.rcParams['lines.antialiased'] = True

# ─── CARGA DE DATOS ───
df = pd.read_csv("datos_actualizados.csv", encoding="utf-8-sig")

# Limpiar tipos
df["Anio"] = pd.to_numeric(df["Anio"], errors="coerce")
df["Max_Dia"] = pd.to_numeric(df["Max_Dia"], errors="coerce")
df["Min_Dia"] = pd.to_numeric(df["Min_Dia"], errors="coerce")
df["Fecha_Grafico"] = pd.to_datetime(df["Fecha_Grafico"], errors="coerce")

df = df.dropna()
df["Anio"] = df["Anio"].astype(int)

# ─── FILTROS ───
st.sidebar.title("Filtros")

anios_sel = st.sidebar.multiselect(
    "Seleccionar años",
    sorted(df["Anio"].unique()),
    default=sorted(df["Anio"].unique())
)

fecha_min = df["Fecha_Grafico"].min()
fecha_max = df["Fecha_Grafico"].max()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    [fecha_min, fecha_max]
)

# Aplicar filtros
df = df[df["Anio"].isin(anios_sel)]

if len(rango_fechas) == 2:
    df = df[
        (df["Fecha_Grafico"] >= pd.to_datetime(rango_fechas[0])) &
        (df["Fecha_Grafico"] <= pd.to_datetime(rango_fechas[1]))
    ]

# ─── COLORES ───
COLORES = {2023: "#FFC107", 2024: "#8BC34A", 2025: "#009688", 2026: "#E64A19"}
ANOS_PRESENTES = sorted(df['Anio'].unique())

# ─── ETIQUETAS ───
def label_smart(ax, x, y, val, color, offset_y):
    ax.annotate(
        f" {val} ", xy=(x, y), xytext=(0, offset_y),
        textcoords="offset points", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=color, edgecolor='none', alpha=0.9),
        zorder=10
    )

# ─── FIGURA ───
fig, (ax_max, ax_min) = plt.subplots(
    2, 1,
    figsize=(22, 12),
    dpi=300,
    sharex=True,
    gridspec_kw={'hspace': 0.18}
)

fig.patch.set_facecolor('white')

# ─── ESTILO ───
for ax in [ax_max, ax_min]:
    ax.set_facecolor('white')
    ax.grid(True, linestyle=':', alpha=0.3, color='grey', zorder=0)
    ax.yaxis.set_major_locator(MultipleLocator(4))
    ax.tick_params(axis='y', labelsize=13, labelcolor='#333333', pad=10)

    # 🔥 BORDES COMPLETOS
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.2)
        spine.set_color("#333333")

    # 🔥 LÍNEAS DE LUNES
    fechas_unicas = df['Fecha_Grafico'].dt.normalize().unique()
    for f in fechas_unicas:
        fecha_check = pd.Timestamp(f).replace(year=2026)
        if fecha_check.weekday() == 0:
            ax.axvline(f, color='#333333', linestyle=(0, (5, 5)), lw=2, alpha=0.4, zorder=1)

# ─── LÍNEAS ───
for ano in ANOS_PRESENTES:
    df_a = df[df['Anio'] == ano].sort_values("Fecha_Grafico")
    color = COLORES.get(ano, "grey")

    ax_max.plot(
        df_a['Fecha_Grafico'], df_a['Max_Dia'],
        color=color, lw=3.5,
        marker='o', markersize=8,
        markeredgecolor='white', markeredgewidth=0.5,
        antialiased=True
    )

    ax_min.plot(
        df_a['Fecha_Grafico'], df_a['Min_Dia'],
        color=color, lw=3.5,
        marker='s', markersize=7,
        markeredgecolor='white', markeredgewidth=0.5,
        antialiased=True
    )

# ─── ETIQUETAS ───
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
                        COLORES.get(row['Anio'], "grey"), offset)
            usados.append(offset)

# ─── RANGOS ───
ax_max.set_ylim(df['Max_Dia'].min() - 2, df['Max_Dia'].max() + 7)
ax_min.set_ylim(df['Min_Dia'].min() - 4, df['Min_Dia'].max() + 6)

# ─── EJES ───
ax_max.set_ylabel('Máxima °C', fontweight='bold', fontsize=15)
ax_min.set_ylabel('Mínima °C', fontweight='bold', fontsize=15)

ax_min.set_xticks(fechas_unicas)
ax_min.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
plt.xticks(rotation=45, ha='right', fontsize=13, fontweight='bold')

# ─── TÍTULO ───
fig.suptitle(
    'HISTÓRICO DE TEMPERATURA DIARIA (MAX-MIN) – LOS BRUJOS',
    fontsize=35, fontweight='bold', color='red', y=0.98
)

# ─── LEYENDA ───
parches = [mpatches.Patch(color=COLORES.get(a), label=f"Año {a}") for a in ANOS_PRESENTES]
fig.legend(
    handles=parches,
    loc='lower center',
    bbox_to_anchor=(0.5, 0.02),
    ncol=len(ANOS_PRESENTES),
    fontsize=18,
    frameon=True,
    shadow=True
)

plt.subplots_adjust(top=0.91, bottom=0.15, left=0.06, right=0.98)

# ─── MOSTRAR ───
st.pyplot(fig, clear_figure=False)

# ─── DESCARGA HD ───
buffer = io.BytesIO()
fig.savefig(buffer, format="png", dpi=300, bbox_inches='tight')
buffer.seek(0)

st.download_button(
    label="📥 Descargar imagen (Alta Calidad)",
    data=buffer,
    file_name="grafico_temperatura_hd.png",
    mime="image/png"
)