import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator
import pandas as pd
import io

st.set_page_config(layout="wide")

# 🔥 CALIDAD
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

# ─── CARGA ───
df = pd.read_csv("datos_actualizados.csv", encoding="utf-8-sig")

df["Anio"] = pd.to_numeric(df["Anio"], errors="coerce")
df["Max_Dia"] = pd.to_numeric(df["Max_Dia"], errors="coerce")
df["Min_Dia"] = pd.to_numeric(df["Min_Dia"], errors="coerce")
df["Fecha_Grafico"] = pd.to_datetime(df["Fecha_Grafico"], errors="coerce")

df = df.dropna()
df["Anio"] = df["Anio"].astype(int)

# ─── FILTROS ───
st.sidebar.title("Filtros")

anios_sel = st.sidebar.multiselect(
    "Años",
    sorted(df["Anio"].unique()),
    default=sorted(df["Anio"].unique())
)

meses = {
    1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
    7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"
}

mes_sel = st.sidebar.multiselect(
    "Meses",
    list(meses.keys()),
    default=list(meses.keys()),
    format_func=lambda x: meses[x]
)

df = df[df["Anio"].isin(anios_sel)]
df = df[df["Fecha_Grafico"].dt.month.isin(mes_sel)]

COLORES = {2023:"#FFC107", 2024:"#8BC34A", 2025:"#009688", 2026:"#E64A19"}
ANOS_PRESENTES = sorted(df['Anio'].unique())

def label_smart(ax, x, y, val, color, offset_y):
    ax.annotate(
        f" {val} ", xy=(x, y), xytext=(0, offset_y),
        textcoords="offset points", ha='center', va='center',
        fontsize=11, fontweight='bold', color='white',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=color, edgecolor='none', alpha=0.9),
        zorder=10
    )

fig, (ax_max, ax_min) = plt.subplots(2,1,figsize=(22,12),dpi=300,sharex=True)

# ─── ESTILO ───
for ax in [ax_max, ax_min]:
    ax.grid(True, linestyle=':', alpha=0.3)
    ax.yaxis.set_major_locator(MultipleLocator(4))

    # 🔥 BORDES COMPLETOS
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.2)

    fechas_unicas = df['Fecha_Grafico'].dt.normalize().unique()

    # 🔥 DOMINGOS
    for f in fechas_unicas:
        if pd.Timestamp(f).replace(year=2026).weekday() == 6:
            ax.axvline(f, linestyle='--', alpha=0.4)

# ─── LÍNEAS ───
for ano in ANOS_PRESENTES:
    df_a = df[df['Anio']==ano].sort_values("Fecha_Grafico")
    color = COLORES.get(ano)

    ax_max.plot(df_a['Fecha_Grafico'], df_a['Max_Dia'], color=color, lw=3.5, marker='o')
    ax_min.plot(df_a['Fecha_Grafico'], df_a['Min_Dia'], color=color, lw=3.5, marker='s')

# ─── ETIQUETAS ───
for f in df['Fecha_Grafico'].unique():
    for sub_df, ax, is_max in [
        (df[df['Fecha_Grafico']==f].sort_values("Max_Dia"), ax_max, True),
        (df[df['Fecha_Grafico']==f].sort_values("Min_Dia"), ax_min, False)
    ]:
        usados=[]
        for _,row in sub_df.iterrows():
            val=row['Max_Dia'] if is_max else row['Min_Dia']
            offset=16
            while any(abs(offset-u)<22 for u in usados):
                offset+=22
            label_smart(ax,row['Fecha_Grafico'],val,val,COLORES[row['Anio']],offset)
            usados.append(offset)

ax_max.set_ylabel('Máxima °C')
ax_min.set_ylabel('Mínima °C')

ax_min.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
plt.xticks(rotation=45)

fig.suptitle('HISTÓRICO DE TEMPERATURA – LOS BRUJOS', fontsize=30, color='red')

# ─── LEYENDA ───
parches=[mpatches.Patch(color=COLORES[a],label=f"Año {a}") for a in ANOS_PRESENTES]
fig.legend(handles=parches, loc='lower center', ncol=len(ANOS_PRESENTES))

st.pyplot(fig)

# ─── DESCARGA HD ───
buffer=io.BytesIO()
fig.savefig(buffer, format="png", dpi=300, bbox_inches='tight')
buffer.seek(0)

st.download_button(
    "📥 Descargar imagen HD",
    data=buffer,
    file_name="grafico_hd.png",
    mime="image/png"
)