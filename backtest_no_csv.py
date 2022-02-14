from binance.enums import *
from collections import deque
import csv
import os.path
import argparse, sys
from datetime import timedelta, datetime

from back.position import Position
from strategy.pivot import PivotStrategy

from utils.arguments import Argument
from utils.log import Logger
from parameters import *
from client.order import *

logger = Logger()

parser = argparse.ArgumentParser(description='Set your Symbol, TradeAmount, PivotStep, DeltaPivot, DeltaSL, DeltaTrigger, StopLoss, Testnet. Example: "main.py -s BTCUSDT"')
parser.add_argument('-s', '--symbol', default="BTCUSDT", help='str, Pair for trading e.g. "-s BTCUSDT"')
parser.add_argument('-a', '--amount', default=5000.0, type=float, help='float, Amount in USDT to trade e.g. "-a 50"')
parser.add_argument('-ps', '--pivotstep', default=5, type=int, help='int, Left/Right candle count to calculate Pivot e.g. "-ps 5"')
parser.add_argument('-d', '--delta', default=0, type=float, help='float, delta to determine trend e.g. "-d 10.0"')
parser.add_argument('-dsl', '--deltasl', default=0.2, type=float, help='float, delta SL to calculate with HH, LL. its value is percentage e.g. "-dsl 0.0005"')
parser.add_argument('-dt', '--deltatrigger', default=0.05, type=float, help='float, delta percent to calculate trigger open order. its value is percentage e.g. "-dt 0.15"')
parser.add_argument('-sl', '--stoploss', default=0.6, type=float, help='float, Percentage Stop Loss"-sl 0.4" ')
parser.add_argument('-tp', '--takeprofit', default=0.6, type=float, help='float, Percentage of Take Profit"-sl 0.8" ')
parser.add_argument('-st', '--starttime', required=True, type=int, help='long, timestamp milliseconds for start time"-sl 1635768000000" ')
parser.add_argument('-du', '--duration', required=True, type=int, help='int, duration as days to test"-sl 30" ')
parser.add_argument('-i', '--interval', default=1, type=int, help='int, time interval as minute"-i 1" ')
parser.add_argument('-test', '--testnet',  action="store_true", help='Run script in testnet or live mode.')
parser.add_argument('-backtest', '--backtest',  action="store_true", help='Run script in backtest')
args = parser.parse_args()

class BackTest():
    def __init__(self):
        self.client = BinanceClient(args).client
        self.args = args
        date = datetime.utcfromtimestamp(self.args.starttime / 1000)
        self.year = date.year
        self.month = date.month
        self.trades = []

        self.position = Position(self.args.amount)
        self.ps = PivotStrategy(self.args, position=self.position)

    def main(self):
        startTime = self.args.starttime
        startTimes = []
        for _ in range(30):
            startTimes.append(startTime)
            startTime = int(startTime + timedelta(hours=24).total_seconds() * 1000)
        for s in startTimes:
            result = self.process_trade(s)
            self.trades.append(result)
        self.sum_trades()
    def process_trade(self, startTime):
        maxLimit = int(1440 / self.args.interval)
        res = self.client.futures_klines(symbol=self.args.symbol, interval=str(self.args.interval) + "m", startTime=startTime, limit=maxLimit)
        if res and len(res) > 0:
            self.position.initialize_positions()
            for row in res:
                self.ps.handle_kline_msg({
                    "k": {
                        "x": True,
                        "o": row[1],
                        "h": row[2],
                        "l": row[3],
                        "c": row[4],
                    }
                })
            totalTradeCount, pnl, totalFee, successCount, failureCount = self.position.calculate_pnl()
            logger.info("Total Trades: " + str(totalTradeCount))
            logger.info_magenta("Total PnL: " + str(pnl))
            logger.info_blue("Total Fees: " + str(totalFee))
            logger.success("Total Success: " + str(successCount))
            logger.error("Total Failure: " + str(failureCount))
            humanTime = datetime.utcfromtimestamp(startTime / 1000)
            return (
                self.args.symbol,
                self.args.interval,
                self.args.amount,
                self.args.pivotstep,
                self.args.delta,
                self.args.deltasl,
                self.args.deltatrigger,
                self.args.takeprofit,
                self.args.stoploss,
                startTime,
                humanTime,
                totalTradeCount,
                successCount,
                failureCount,
                totalFee,
                pnl
            )
    def sum_trades(self):
      total_pnl = 0
      total_fee = 0
      for trade in self.trades:
        total_fee = total_fee + trade[14]
        total_pnl = total_pnl + trade[15]
      result = total_pnl + total_fee
      logger.info_magenta(f"Tested {self.year}_{self.month}...")
      logger.info(f"{total_pnl} {total_fee} {result}")
      return total_pnl, total_fee, result

if __name__ == "__main__":
    if args.starttime == None:
        logger.error("Please Check Start Time e.g. -st 1635768000000")
        logger.error("exit!")
        sys.exit()
    if args.duration == None:
        logger.error("Please duration e.g. -du 30")
        logger.error("exit!")
        sys.exit()
    else:
        Argument().set_args(args)
        BackTest().main()