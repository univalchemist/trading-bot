from binance import Client
from binance.enums import *
from client.order import *
import argparse, sys

from parameters import *
from utils.draw_pivot import PlotPivot
from utils.log import Logger

logger = Logger()

parser = argparse.ArgumentParser(description='Set your Symbol, TradeAmount, PivotStep, DeltaPivot, DeltaSL, DeltaTrigger, StopLoss, Testnet. Example: "main.py -s BTCUSDT"')
parser.add_argument('-s', '--symbol', default="BTCUSDT", help='str, Pair for trading e.g. "-s BTCUSDT"')
parser.add_argument('-ps', '--pivotstep', default=5, type=int, help='int, Left/Right candle count to calculate Pivot e.g. "-ps 5"')
parser.add_argument('-st', '--starttime', type=int, help='long, timestamp milliseconds for start time"-sl 1635768000000" ')
parser.add_argument('-i', '--interval', default=1, type=int, help='int, time interval as minute"-sl 1" ')
parser.add_argument('-test', '--testnet',  action="store_true", help='Run script in testnet or live mode.')
args = parser.parse_args()

client = Client(TEST_API_KEY, TEST_API_SECRET, testnet=True) if args.testnet else Client(API_KEY, API_SECRET)

def main():
  maxLimit = int(1440 / args.interval)
  res = client.futures_klines(symbol=args.symbol, interval=str(args.interval) + "m", startTime=args.starttime, limit=maxLimit)

  PlotPivot(res, args.pivotstep).draw_plot()

if __name__ == "__main__":
  main()