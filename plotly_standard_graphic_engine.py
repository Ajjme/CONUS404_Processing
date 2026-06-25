import plotly.graph_objects as go
import plotly.io as pio

def get_cadence_plotly_template():
    colors = {
        'teal': '#2F8F7F', 'grey': '#333333', 'tan': '#D9A341',
        'blue': '#205196', 'light_blue': '#6FA8DC', 'ice_blue': '#E9ECEF',
        'red': '#AA2634'
    }
    
    template = go.layout.Template()
    template.layout = go.Layout(
        colorway=[colors['teal'], colors['blue'], colors['tan'], colors['light_blue']],
        font=dict(family="Inter, system-ui, sans-serif", color=colors['grey'], size=12),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(
            showgrid=True, gridcolor=colors['ice_blue'],
            linecolor='#CCCCCC', zeroline=False, title_font=dict(size=13, color=colors['grey'])
        ),
        yaxis=dict(
            showgrid=True, gridcolor=colors['ice_blue'],
            linecolor='#CCCCCC', zeroline=False, title_font=dict(size=13, color=colors['grey'])
        ),
        margin=dict(t=50, b=50, l=60, r=30)
    )
    return template

# Set as default globally for all plotly instances
pio.templates["cadence_theme"] = get_cadence_plotly_template()
pio.templates.default = "cadence_theme"