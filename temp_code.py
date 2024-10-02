import plotly.graph_objects as go

# Sample data
x = [1, 2, 3, 4, 5]
y = [10, 11, 12, 13, 14]

# Create a line chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name='Line Chart'))
fig.update_layout(title='Basic Line Chart', xaxis_title='X Axis', yaxis_title='Y Axis')
fig.show()
