import csv
import pandas as pd
import plotly.graph_objects as go
import requests
import matplotlib.pyplot as plt
import datetime



def plot_product_chart(product, rows=None, csvPath='island-data-bottle-round-1\island-data-bottle-round-1\prices_round_1_day_0.csv'):
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


def parse_input_string(input_string,timestamp_list,price_list):
    split_input = input_string.strip().split('\n')
    for i in range(0, len(split_input), 2):
        # pprint(split_input[i])
        parts = split_input[i].split(';')
        timestamp_list.append(parts[0])
        price_list.append(float(parts[1]))
    return timestamp_list, price_list

def plot_timestamp_value(timestamps, values):
    
    # Plot the graph
    plt.plot(timestamps, values)
    plt.xlabel("Timestamp")
    plt.ylabel("Value")
    plt.show()

# Retrieving round results
auth_token = "eyJraWQiOiJ4M3NhZjFZTkNsRGwyVDljemdCR01ybnVVMlJlNDNjb1E1UGxYMWgwb2tBPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI4NzM4ZGNiMi04NzhiLTRlOGEtYWMxMC0xOWU5Nzc5YjU2NDQiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfek9mVngwcWl3IiwiY29nbml0bzp1c2VybmFtZSI6Ijg3MzhkY2IyLTg3OGItNGU4YS1hYzEwLTE5ZTk3NzliNTY0NCIsIm9yaWdpbl9qdGkiOiIyNDYxZDMyZi1hNzg4LTQyZTQtYjkzOS1mOGZjMmY1ZDNhMGYiLCJhdWQiOiIzMmM1ZGM1dDFrbDUxZWRjcXYzOWkwcjJzMiIsImV2ZW50X2lkIjoiNzMyYzZkNTEtOWU5ZS00YzE3LWFmYTgtYWQ0ODk4MmFiNmM4IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE2NzkzMzEyMjUsImV4cCI6MTY3OTQzMDk5MCwiaWF0IjoxNjc5NDI3MzkwLCJqdGkiOiJiODUwMTJiZi0wMzdlLTQ4NzItYTY2NC04OTRlYzZjZmRlYzgiLCJlbWFpbCI6Im1heC56aGFvODlAZ21haWwuY29tIn0.RKcn8vNxaogkMqIoMCab64p0pPyWCDOv3K6nx2q2R6L1rh3B_UGnjuF3WLJ16xGBa89rJaKYiNaHg1LOzyP6RVvvjmbNPrr3emflGVusRdv3aLOf3RDV27L4MzVN6VO1DPiFhnlFXcaCR-docKohktO8UdCmZ5FOq17AySlOypRli6d-YBAeNYOZYFQmnms0cnSBdnbe2iKVoOhupc82s1vd0x9tybEfTGmS7wIrbkz0kg8UUMCjH2GNaYJFWsiuPquinEl883-nbrdHz01fngN4sf-Yx4IT-EVkeJupjJRK9ZGt2eBaHP9OEsJLGhK2EexH8ULiaqjN7TV6mCGTEw"
log_id = "2a4a84b6-6066-486a-9c6d-f83fb1f539dc"
r = requests.get("https://bz97lt8b1e.execute-api.eu-west-1.amazonaws.com/prod/results/tutorial/"+log_id, headers={"Authorization":"Bearer " + auth_token})
response = r.json()
profit = response["algo"]["summary"]["profit"]
graph_log = response["algo"]["summary"]["graphLog"][15:]
print(profit)


activities_log_url = response["algo"]["summary"]["activitiesLog"]
result_csv = requests.get(activities_log_url)
result_csv = result_csv.text


timestamp, price = [], []

parse_input_string(graph_log,timestamp,price)
plot_timestamp_value(timestamp, price)

        

# # Example chart
# results_dict = {1: "results\short_and_long_term_mean_results.csv", 2: "results\order_at_limit_results.csv", 3: "results\spread-1.75.csv"}
# # calc_max_pearls_profit()
# plot_product_chart("BANANAS")
# plot_product_chart("PEARLS")
# plot_pnl_chart("PEARLS", results_dict[3])