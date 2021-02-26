"""
Ispirato a:
https://www.nytimes.com/2021/02/21/insider/covid-500k-front-page.html

Dati da:
https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/
dati-regioni/dpc-covid19-ita-regioni.csv

Anomalie nei dati:
2020/08/15    155 decessi Emilia Romagna
2020/06/23    466 decessi cumulati Trento
2020/06/24    405 decessi cumulati Trento

I dati della Protezione Civile iniziano il 24 febbraio con 7 decessi,
6 in Lombardia e 1 in Veneto, ma il primo decesso di cui si ha notizia
è il 2020/02/21 in Veneto
"""
import locale
import math
import pandas as pd
import numpy as np
import plotly.graph_objects as go

np.random.seed(seed=2020)
dimensione_punto = 4
opacita = 0.5
intervallo = 10000
molt_larghezza = 1.4

locale.setlocale(locale.LC_ALL, "")

# scarica i dati della protezione civile
url = (
    "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/"
    "dati-regioni/dpc-covid19-ita-regioni.csv"
)
"""
ifile = Path("dati") / "bollettini" / "dpc-italia.csv"
"""
dfi = pd.read_csv(url)
# somma i decessi di tutte le regioni per ogni giorno
deceduti_italia = dfi.groupby(["data"], as_index=False)["deceduti"].sum()
# da somma cumulata deceduti a deceduti per giorno
deceduti_italia["deceduti_per_giorno"] = deceduti_italia.deceduti.diff()
# deceduti del primo giorno = deceduti cumulati
deceduti_italia.iloc[0, 2] = deceduti_italia.iloc[0, 1]
deceduti_italia["deceduti_per_giorno"] = deceduti_italia[
    "deceduti_per_giorno"
].astype(int)
# aggiungi data formattata: 20 marzo 2020
deceduti_italia["dataf"] = pd.to_datetime(
    deceduti_italia.data, format="%Y/%m/%d"
).dt.strftime("%d %b %Y")
# numero massimo di decessi in un giorno
massimo_decessi = deceduti_italia["deceduti_per_giorno"].max()
# totale decessi da inizio pandemia
totale_decessi = deceduti_italia.iloc[-1, 1]
# cambia ordine delle righe, date più recenti all'inizio
deceduti_italia = deceduti_italia[::-1]
deceduti_italia.reset_index(inplace=True, drop=True)

# creazione array passato a plotly go.scatter
# array con una riga per ogni decesso e due colonne
# - offset (coordinata x nel grafico)
#   offset è calcolato distribuendo in modo casuale i decessi del giorno
#   su valori che vanno da zero a massimo_decessi
# - data ( coordinata y nel grafico)
punti = np.full((totale_decessi, 2), 0, dtype=np.uint16)
decessi = list(deceduti_italia["deceduti_per_giorno"])
ypos = 0
for idd, decessi_giorno in enumerate(decessi):
    if decessi_giorno >= 0:
        # print(idd, ypos, flush=True)
        punti[ypos : ypos + decessi_giorno, 1] = idd
        punti[ypos : ypos + decessi_giorno, 0] = np.random.randint(
            0, int(molt_larghezza * massimo_decessi), decessi_giorno
        )
    ypos += decessi_giorno

# annotazioni
fine = intervallo * math.ceil(totale_decessi / intervallo)
inizio, delta = intervallo, intervallo
offset_diecimila_precedente = 365
# print(inizio, delta, fine)
posizione = []
testo_sinistra = []
testo_destra = []
righe_decessi = list(range(inizio, fine, delta))
righe_decessi.append(totale_decessi)
# ciclo di creazione delle annotazioni
# for val in range(inizio, fine, delta):
for idx, val in enumerate(righe_decessi):
    indice = deceduti_italia[deceduti_italia["deceduti"] < val].index[0] - 1
    riga = deceduti_italia.loc[indice, :]
    posizione.append(riga.name)
    testo = (
        f'<span style="color:red;font-size:10;">'
        f"{riga.dataf}</span><br>"
        f"<span style="
        f'"color:red;font-size:12;font-weight:bold;text-align:left;">'
        f"{riga.deceduti}</span>"
    )
    testo_sinistra.append(testo)
    testo = (
        ""
        if idx == (len(righe_decessi) - 1)
        else (
            f'<span style="color:red;font-size:10;">'
            f"10000 decessi in<br>"
            f"{offset_diecimila_precedente - riga.name} giorni</span>"
        )
    )
    testo_destra.append(testo)
    offset_diecimila_precedente = riga.name

# ultima riga


# crea il grafico
trace = go.Scattergl(
    x=punti[:, 0],
    y=punti[:, 1],
    mode="markers",
    marker_symbol="circle",
    marker=dict(
        size=dimensione_punto,
        color="#050505",
        opacity=opacita,
    ),
    hoverinfo="skip",
)
titolo = (
    '<span style="font-size:20">Morti per Covid in Italia</span>'
    '<br><span style="font-size:14">'
    "Ogni punto rappresenta un decesso</span>"
)
fig = go.Figure(data=[trace])
fig.update_layout(
    width=1000,
    height=1200,
    title=dict(text=titolo, x=0.5, y=0.92),
    plot_bgcolor="white",
    xaxis=dict(showticklabels=False, showgrid=False),
    yaxis=dict(showticklabels=False, showgrid=False),
)
# linee orizzontali
for pos in posizione:
    fig.add_shape(
        type="line",
        xref="x",
        yref="y",
        x0=-160,
        y0=pos,
        x1=molt_larghezza * massimo_decessi + 170,
        y1=pos,
        line=dict(color="red", width=1),
    )

# annotazioni al superamento di multipli di 10000 decessi
posizione = [item + 8 for item in posizione]
for pos, testos, testod in zip(posizione, testo_sinistra, testo_destra):
    fig.add_annotation(x=-90, y=pos, text=testos, showarrow=False)
    fig.add_annotation(
        x=molt_larghezza * massimo_decessi + 100,
        y=pos,
        text=testod,
        showarrow=False,
    )
fig.show()
fig.write_html("decessi_italia.html")
