import csv
import pandas as pd
import plotly.graph_objects as go



def plot_product_chart(product, rows=None, csvPath='results\short_and_long_term_mean_results.csv'):
    # parsing csv for company specific data
    df = pd.read_csv(csvPath, sep=";")
    parsed = pd.DataFrame()
    parsed = pd.concat([parsed, df[df["product"] == product]])
    if rows:
        parsed.drop([2, len(parsed)])
    print(parsed)
    fig = go.Figure([go.Scatter(x=parsed['timestamp'], y=parsed['mid_price'])])
    fig.show()
        
def plot_pnl_chart(product,  csvPath, rows=None):
    # parsing csv for company specific data
    df = pd.read_csv(csvPath, sep=";")
    parsed = pd.DataFrame()
    parsed = pd.concat([parsed, df[df["product"] == product]])
    if rows:
        parsed.drop([2, len(parsed)])
    print(parsed)
    fig = go.Figure([go.Scatter(x=parsed['timestamp'], y=parsed['profit_and_loss'], name=(product + " using " + csvPath))])
    fig.show()

def calc_max_pearls_profit(csvPath="results\short_and_long_term_mean_results.csv") -> int:
    df = pd.read_csv(csvPath, sep=";")
    parsed = pd.DataFrame()
    parsed = pd.concat([parsed, df[df["product"] == "PEARLS"]])
    max_profit = 0
    for index, row in parsed.iterrows():
        
        bids = [(row["bid_price_1"], row["bid_volume_1"]), (row["bid_price_2"], row["bid_volume_2"]), (row["bid_price_3"], row["bid_volume_3"])]
        asks = [(row["ask_price_1"], row["ask_volume_1"]), (row["ask_price_2"], row["ask_volume_2"]), (row["ask_price_3"], row["ask_volume_3"])]
        for bid in bids:
            if bid[0] > 10000:
                max_profit += (bid[0] - 10000) * bid[1]
        for ask in asks:
            if ask[0] < 10000:
                max_profit += (10000 - ask[0]) * ask[1]
        #print(index, max_profit)
    print("Max Profit: ", max_profit)

        

# Example chart
results_dict = {1: "results\short_and_long_term_mean_results.csv", 2: "results\order_at_limit_results.csv", 3: "results\spread-1.75.csv"}
# calc_max_pearls_profit()
# plot_product_chart("BANANAS")
# plot_pnl_chart("PEARLS", results_dict[2])
plot_pnl_chart("PEARLS", results_dict[3])