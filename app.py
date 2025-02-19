import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pprint

from datetime import datetime
import pandas as pd
import json

# Components
from components import *
from backend import validation, load_local_data, temporal_df, total_df

"""
Paso 1: Traerse o crear los datos
"""

"""
Paso 3: Definicion de la app
"""
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.COSMO],
    prevent_initial_callbacks=True,
)
app.title = "MSIET Colmenares"
server = app.server

body = html.Div(
    [
        dbc.Row(  # Title and presentation. (It takes all the screen)
            [
                dbc.Col(
                    [html.Div(children=[mainHeader])], xs=10, sm=10, md=10, lg=10, xl=10
                ),
            ],
            justify="center",
        ),
        dbc.Row(  # Selector and outputs. Horizontal Layout
            [
                dbc.Col(  # Left-layout
                    [
                        html.Div(  # Inputs
                            children=[
                                selectores1,
                                selectores2,
                                selectores3,
                                selectores4,
                                selectores5,
                                selectores6,
                                botonCalcular,
                            ]
                        )
                    ],
                    xs=10,
                    sm=10,
                    md=10,
                    lg=4,
                    xl=4,
                ),
                dbc.Col(  # Right-layout
                    [
                        html.Div(children=[aux_output]),  # Auxiliary Output
                        dbc.Spinner(
                            [
                                html.Div(  # Output
                                    children=[
                                        graph_tabs,
                                    ]
                                )
                            ],
                            fullscreen=True,
                            color="info",
                            size="lg",
                        ),
                    ],
                    xs=10,
                    sm=10,
                    md=10,
                    lg=6,
                    xl=6,
                ),
            ],
            justify="center",
        ),
    ]
)


############################# CALL THE APP ####################################

# Main Call for App
app.layout = html.Div(children=[body])


######################## CALLBACKS DE ENTRADA #################################
# Este callback nos va a asegurar que estemos tomando los datos desde el frontend
# y me los va a presentar en un diccionario
@app.callback(
    Output("output-selectores", "data"),
    [
        Input("selector1-tarifa-state", "value"),
        Input("selector2-P1C", "value"),
        Input("selector2-P2C", "value"),
        Input("selector2-P3C", "value"),
        Input("selector2-P4C", "value"),
        Input("selector2-P5C", "value"),
        Input("selector2-P6C", "value"),
        Input("selector3-table-potencia", "data"),
        Input("selector3-table-energia", "data"),
        Input("selector4-margen-potencia", "value"),
        Input("selector4-contador", "value"),
        Input("selector5-imp-elect", "value"),
        Input("selector5-imp-iva", "value"),
        Input("selector6-datepicker", "start_date"),
        Input("selector6-datepicker", "end_date"),
    ],
)
def build_input_dict(
    tarifa,
    p1c,
    p2c,
    p3c,
    p4c,
    p5c,
    p6c,
    rows_potencia,
    rows_energia,
    margen_pot,
    alquiler_cont,
    imp_elect,
    iva,
    start_date,
    end_date,
):

    # Limpiamos los valores del datatable
    for row in rows_potencia:
        del row["Concepto"]
    for row in rows_energia:
        del row["Concepto"]

    # Procesamos la salida del datepicker
    if start_date is not None:
        start_datetime = datetime.fromisoformat(start_date)
        start_date_string = start_datetime.strftime("%Y-%m-%d")
    if end_date is not None:
        end_datetime = datetime.fromisoformat(end_date)
        end_date_string = end_datetime.strftime("%Y-%m-%d")
    else:
        start_date_string, end_date_string = "2021-06-01", "2021-08-31"

    # Construimos el diccionario de salida
    input_dict = {
        "tarifa": tarifa,
        "potencias": {
            "P1": p1c,
            "P2": p2c,
            "P3": p3c,
            "P4": p4c,
            "P5": p5c,
            "P6": p6c,
        },
        "peajes_potencia": rows_potencia[0],
        "cargos_potencia": rows_potencia[1],
        "peajes_energia": rows_energia[0],
        "cargos_energia": rows_energia[1],
        "margen_potencia": margen_pot,
        "alquiler_contador": alquiler_cont,
        "imp_electrico": imp_elect,
        "iva": iva,
        "start_date": start_date_string,
        "end_date": end_date_string,
    }

    # return html.Div([
    #     html.P("Datos de entrada"),
    #     html.Pre( pprint.pformat(input_dict))
    # ])
    return json.dumps(input_dict)


###################### CALLBACK FRONTEND (FORMATOS) ###########################

# CALLBACK 1: Si se selecciona la tarifa 2.0TD no se pueden cargar potencia en P3C~P6C
@app.callback(
    [
        Output("selector2-P1C", "disabled"),
        Output("selector2-P2C", "disabled"),
        Output("selector2-P3C", "disabled"),
        Output("selector2-P4C", "disabled"),
        Output("selector2-P5C", "disabled"),
        Output("selector2-P6C", "disabled"),
        Output("selector3-table-potencia", "data"),
        Output("selector3-table-energia", "data"),
    ],
    [
        Input("selector1-tarifa-state", "value"),
    ],
)
def restringir_potencias(tarifa):
    if tarifa == "2.0TD":
        disabled_pot = [False, False, True, True, True, True]
        table1 = CargosPeajes_enPotencia("2.0TD").to_dict("records")
        table2 = CargosPeajes_enEnergia("2.0TD").to_dict("records")
        out = disabled_pot + [table1] + [table2]
        return out
    elif tarifa == "3.0TD":
        disabled_pot = [False, False, False, False, False, False]
        table1 = CargosPeajes_enPotencia("3.0TD").to_dict("records")
        table2 = CargosPeajes_enEnergia("3.0TD").to_dict("records")
        out = disabled_pot + [table1] + [table2]
        return out


# CALLBACK 2: Permitir cargar curvas
# @app.callback(
#
# )

######################## CALLBACKS DE BACKEND #################################

# CALLBACK 1: Pasan los valores a la función principal al pulsar el botón
@app.callback(
    [
        Output("output-alerts", "children"),
        Output("output-tiempo-graph", "data"),
    ],
    [
        Input("submit-button", "n_clicks"),
    ],
    State("output-selectores", "data"),
)
def alertas_y_calculos(clicks, data):
    # ejecutar backend
    print("Comprobación...")
    inputs = json.loads(data)
    print(inputs)
    alerts, flag_continue = validation(inputs)

    if flag_continue:  # Si todo está bien
        # se cargan los datos disponibles en base de datos ()
        gen, prices, profiles, co2_taxes, gas_index = load_local_data(joined=False)
        # se calcular las componentes finales y se regresa un único dataframe
        dia_dia = temporal_df(inputs, gen, prices, profiles, co2_taxes, gas_index)

        data_temporal = dia_dia.to_json(orient="split")

        card_output = [  # Alerts que no me dajan seguir
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Validación satisfactoria", className="card-title"),
                    ]
                ),
                id="validation-status",
                color="success",
                inverse=True,
            )
        ]
        return [card_output, data_temporal]  # Nothing to do here

    else:  # Si algo falla. Regresa componentes
        print(inputs)
        data_output = json.dumps({})
        card_output = [  # Alerts que no me dajan seguir
            dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Alertas de validación", className="card-title"),
                        html.Ul([html.Li(alert) for alert in alerts]),
                    ]
                ),
                id="validation-status",
                color="warning",
                inverse=True,
            )
        ]

        return [card_output, data_output]


######################## CALLBACKS DE GRAFICACION ################################


@app.callback(
    [
        Output("output-desglose", "children"),
        Output("components-graph", "figure"),
    ],
    [Input("validation-status", "color")],
    [State("output-selectores", "data"), State("output-tiempo-graph", "data")],
)
def graph_components(status, inputs, temporal_df):
    if status == "warning":
        print("No se grafica1")
    elif status == "success":
        print("Graficando1")
        inputs = json.loads(inputs)

        all_variables = pd.read_json(temporal_df, orient="split")
        curva_consumo = all_variables.iloc[:, 0:4]
        prices = all_variables.iloc[:, 4:12]  # Solo suma de componentes

        df_out, dict_out = total_df(inputs, curva_consumo, prices)

        # Construir desglose
        desglose = build_deglose(inputs, dict_out)

        # Print Figure and Modify it
        fig = px.bar(
            df_out.reset_index(),
            x="Concepto",
            y="Euros",
            #color="Concepto",
            text="Porcent",
        )
        fig.update_traces(
            textposition="outside", 
            texttemplate="%{text:.2%}",
            marker = dict( color = ['#008000', '#C00001', '#FFC001', '#000000', '#D9D9D9', '#305496' ]),

        )
        return desglose, fig


@app.callback(
    Output("consumption-graph", "figure"),
    [Input("validation-status", "color")],
    State("output-tiempo-graph", "data"),
)
def graph_consumo(status, temporal_df):  # slice the whole dataframe DF[0:20]
    if status == "warning":
        print("No se grafica2")
    elif status == "success":
        print("Graficando2")
        # Utilizar una funcion de backend para traer la data que nos interesa
        all_variables = pd.read_json(temporal_df, orient="split")
        curva_consumo = all_variables.iloc[:, 0:4]

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0,
            specs=[[{"rowspan": 2}], [{}], [{}]],
        )

        fig.add_trace(
            go.Scatter(
                x=curva_consumo.index,
                y=curva_consumo.Consumo * 1000,
                name="Consumo",
                customdata=curva_consumo.weekday,
                hovertemplate="<b>Consumo: %{y:.2f} W.hora<br>"
                + "Día: %{customdata}<br>"
                + "Fecha: %{x}<br>"
                + "<extra></extra>",
            ),
            row=1,
            col=1,
        )
        curva_consumo["val"] = 1
        color = ["", "red", "gold", "green", "pink", "lightyellow", "lightgreen"]
        for periodo in curva_consumo.Periodos.unique():
            fig.add_trace(
                go.Bar(
                    x=curva_consumo.loc[curva_consumo["Periodos"] == periodo].index,
                    y=curva_consumo.loc[curva_consumo["Periodos"] == periodo].val,
                    showlegend=True,
                    name=f"Periodo {periodo}",
                    marker_color=color[periodo],
                    offset=0,
                ),
                row=3,
                col=1,
            )
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)

        return fig


@app.callback(
    Output("market-graph", "figure"),
    [Input("validation-status", "color")],
    State("output-tiempo-graph", "data"),
)
def graph_market(status, temporal_df):  # slice the whole dataframe DF[0:20]
    if status == "warning":
        print("No se grafica3")
    elif status == "success":
        print("Graficando3")
        # Utilizar una funcion de backend para traer la data que nos interesa
        all_variables = pd.read_json(temporal_df, orient="split")
        prices = all_variables.iloc[:, 4:12]
        taxes = all_variables.iloc[:, 35:36]
        gas = all_variables.iloc[:, 36:37]

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            specs=[[{}], [{"rowspan": 2}], [{}]],
        )

        for item in prices.drop("Suma Componentes Precio", axis=1).columns:
            fig.add_trace(
                go.Scatter(
                    x=prices.index,
                    y=prices[item],
                    name=item,
                    mode="lines",
                    line={"width": 0},
                    stackgroup="pric",
                ),
                row=2,
                col=1,
            )

        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices["Suma Componentes Precio"],
                name="Suma Total",
                line={"color": "darkgray"},
            ),
            row=2,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=gas.index,
                y=gas["MIBGAS Index"],
                name="MIBGAS",
                hoverinfo="y",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=taxes.index,
                y=taxes["EUA"],
                name="Derechos C02",
                hoverinfo="y",
            ),
            row=1,
            col=1,
        )

        fig.update_layout(title_text="Componente Precio y CO2", hovermode="x unified")

        fig.update_yaxes(
            title_text="<b>EUR/Ton CO2</b>",
            row=1,
            col=1,
        )
        fig.update_yaxes(title_text="<b>EUR/MW.h</b>", row=2, col=1)

        return fig


@app.callback(
    Output("generation-graph", "figure"),
    [Input("validation-status", "color")],
    State("output-tiempo-graph", "data"),
)
def graph_generation(status, temporal_df):  # slice the whole dataframe DF[0:20]
    if status == "warning":
        print("No se grafica4")
    elif status == "success":
        print("Graficando4")
        # Utilizar una funcion de backend para traer la data que nos interesa
        all_variables = pd.read_json(temporal_df, orient="split")
        prices = all_variables.iloc[:, 4:12]
        generation = all_variables.iloc[:, 12:35]

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.01,
            specs=[[{}], [{"rowspan": 2}], [{}]],
        )

        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices["Suma Componentes Precio"],
                name="Precio EUR/MW.h",
                hoverinfo="y",
                legendgroup="Fixed",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=generation.index,
                y=generation["Total"],
                name="Demanda Total",
                line={"color": "black"},
                hoverinfo="y",
                legendgroup="Fixed",
            ),
            row=2,
            col=1,
        )

        Renovables = [
            "Consumo bombeo",
            "Nuclear",
            "Biogás",
            "Biomasa",
            "Energía residual",
            "Eólica terrestre",
            "Corrección eólica",
            "Océano y geotérmica",
            "Hidráulica UGH",
            "Hidráulica no UGH",
            "Turbinación bombeo",
            "Solar fotovoltáica",
            "Solar térmica",
        ]

        NoRenovables = [
            "Enlace Baleares",
            "Residuos domésticos y similares",
            "Residuos varios",
            "Derivados del petróleo ó carbón",
            "Subproductos minería",
            "Hulla antracita",
            "Hulla sub-bituminosa",
            "Cogeneración",
            "Ciclo combinado",
        ]

        scale = px.colors.sequential.Blugrn
        scale = scale * 3 # allow the scale to be repeated
        scale_iter = iter(scale)
        for tecnologia in Renovables:
            fig.add_trace(
                go.Scatter(
                    x=generation.index,
                    y=generation[tecnologia],
                    name=tecnologia,
                    mode="lines",
                    line={"width": 0, "color": f"{next(scale_iter)}"},
                    stackgroup="gen",
                    legendgroup="Renovable",
                    legendgrouptitle_text="Renovables",
                    hovertemplate="<b>%{y:.2f} MW.hora<br>",
                ),
                row=2,
                col=1,
            )
        
        scale = px.colors.sequential.YlOrRd
        scale = scale * 3 # allow the scale to be repeated
        scale_iter = iter(scale)
        for tecnologia in NoRenovables:
            fig.add_trace(
                go.Scatter(
                    x=generation.index,
                    y=generation[tecnologia],
                    name=tecnologia,
                    mode="lines",
                    line={"width": 0, "color": f"{next(scale_iter)}"},
                    stackgroup="gen",
                    legendgroup="No Renovables",
                    legendgrouptitle_text="No Renovables",
                    hovertemplate="<b>%{y:.2f} MW.hora<br>",
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            title_text="Demanda y Precio",
            legend=dict(
                orientation="v",
                yanchor="top",
            ),
            height=1000,
        )

        fig.update_yaxes(
            title_text="<b>EUR/MWh</b>",
            row=1,
            col=1,
        )
        fig.update_yaxes(title_text="<b>kW.h</b>", range=[-5000, 45000], row=2, col=1)

        return fig


##########################################
############# ENTRY POINT ################
##########################################
if __name__ == "__main__":
    app.run_server(debug=True)
