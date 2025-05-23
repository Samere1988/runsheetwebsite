from dash import Dash, html, dcc, Input, Output
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from datetime import datetime
import os

def init_dashboard(flask_app):
    dash_app = Dash(
        server=flask_app,
        url_base_pathname='/dash_statistics/',
        title="Run Sheet Statistics",
        name="dash_statistics_app"
    )

    def load_data():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'databases', 'Run Sheet Database.db')
        if not os.path.exists(db_path):
            db_path = os.path.join(base_dir, 'databases', 'Run Sheet DataBase.db')
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM RunSheetTotals", conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%B %Y')
        df['week'] = df['date'].dt.to_period('W-MON').apply(lambda r: f"{r.start_time.date()} to {r.end_time.date()}")
        df['weekday'] = df['date'].dt.strftime('%A')
        return df

    df = load_data()
    months = df['month'].unique()

    dash_app.layout = html.Div([
        html.H1("Run Sheet Totals by Week", style={
            'color': 'white', 'fontSize': '28px', 'textAlign': 'center',
            'marginBottom': '25px', 'fontFamily': 'Poppins'
        }),

        html.Div([
            dcc.Dropdown(
                id='month-dropdown',
                options=[{'label': m, 'value': m} for m in months],
                value=months[0] if len(months) > 0 else None,
                placeholder="Select Month",
                style={'width': '280px', 'marginRight': '20px', 'color': 'white', 'backgroundColor': '#1f2937'}
            ),
            dcc.Dropdown(
                id='week-dropdown',
                options=[],
                placeholder="Select Week",
                style={'width': '280px', 'color': 'white', 'backgroundColor': '#1f2937'}
            )
        ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '30px'}),

        html.Div([
            dcc.Graph(id='weight-line-chart', config={'displayModeBar': False}, style={'height': '320px'}),
            dcc.Graph(id='bar-chart', config={'displayModeBar': False}, style={'height': '320px'})
        ], style={
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '40px',
            'maxWidth': '1000px',
            'margin': '0 auto'
        })
    ], style={
        'backgroundColor': '#0d1117',
        'color': 'white',
        'padding': '40px',
        'fontFamily': 'Poppins',
        'minHeight': '100vh',
        'boxSizing': 'border-box'
    })

    @dash_app.callback(
        Output('week-dropdown', 'options'),
        Output('week-dropdown', 'value'),
        Input('month-dropdown', 'value')
    )
    def update_weeks(selected_month):
        filtered = df[df['month'] == selected_month]
        weeks = filtered['week'].unique()
        options = [{'label': w, 'value': w} for w in weeks]
        return options, options[0]['value'] if options else None

    @dash_app.callback(
        Output('weight-line-chart', 'figure'),
        Output('bar-chart', 'figure'),
        Input('week-dropdown', 'value')
    )
    def update_charts(selected_week):
        filtered = df[df['week'] == selected_week]
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        filtered = filtered[filtered['weekday'].isin(days)].sort_values('date')

        # Line chart
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=filtered['weekday'],
            y=filtered['total_weight'],
            mode='lines+markers',
            name='Total Weight',
            line=dict(color='#00d1ff', width=3),
            marker=dict(size=7),
            fill='tozeroy',
            fillcolor='rgba(0, 209, 255, 0.15)'  # cyan fade under curve
        ))

        fig1.update_layout(
            title='Total Weight (lbs)',
            plot_bgcolor='#1a1c24',
            paper_bgcolor='#1a1c24',
            font=dict(color='white', family='Poppins'),
            margin=dict(t=40, b=30),
            yaxis=dict(tickformat=",", title="Weight (lbs)", showgrid=True, zeroline=False),
            xaxis=dict(title="Day", showgrid=False),  # no vertical grid
        )

        # Grouped Bar chart
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=filtered['weekday'],
            y=filtered['total_skids'],
            name='Total skids',
            marker_color='#3b82f6'
        ))
        fig2.add_trace(go.Bar(
            x=filtered['weekday'],
            y=filtered['total_bundles'],
            name='Total bundles',
            marker_color='#f43f5e'
        ))
        fig2.add_trace(go.Bar(
            x=filtered['weekday'],
            y=filtered['total_coils'],
            name='Total coils',
            marker_color='#facc15'
        ))
        fig2.update_layout(
            title='Skids / Bundles / Coils',
            barmode='group',  # ← now grouped instead of stacked
            plot_bgcolor='#1a1c24',
            paper_bgcolor='#1a1c24',
            font=dict(color='white', family='Poppins'),
            margin=dict(t=40, b=30),
            yaxis=dict(title="Count", showgrid=False),
            xaxis=dict(title="Day", showgrid=False),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=1.15)
        )

        return fig1, fig2

    return dash_app


