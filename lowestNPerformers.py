import time
import numpy as np
import pandas as pd
import pandas_datareader.data as web
from pandas_datareader._utils import RemoteDataError
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('stocks', type=int)
parser.add_argument('days', type=int)
args = parser.parse_args()

start_o = datetime(2017,3,1)
end_o = datetime(2017,10,1)
numStocks = args.stocks
numDays = args.days
investment = 1000

df = pd.read_csv('sp500.csv')
dateList = web.DataReader('SPY', 'google', start_o, end_o).index

if not os.path.exists('panelStore.h5'):
	tmp_di = {}
	for ticker in df.Symbol:
		try:
			ticker = ticker.replace('.','-')
			tmp = web.DataReader(ticker, 'google', start_o, end_o)
			if len(tmp) == 0:
				continue
			tmp['dates'] = tmp.index
			tmp_di[ticker] = tmp.reset_index(drop=True)
		except RemoteDataError:
			print 'No data for',ticker
	p = pd.Panel(tmp_di)
	p.to_hdf('panelStore.h5', 'p')
else:
	p = pd.read_hdf('panelStore.h5', 'p')

allReturns = []
for i in range(1, len(dateList)-numDays):
	endDate = datetime.strptime(datetime.strftime(dateList[i], '%Y-%m-%d'), '%Y-%m-%d')
	startDate = datetime.strptime(datetime.strftime(dateList[i-1], '%Y-%m-%d'), '%Y-%m-%d')
	returnDate = datetime.strptime(datetime.strftime(dateList[i+numDays], '%Y-%m-%d'), '%Y-%m-%d')
	print endDate

	di = {'ticker': [], 'change': []}
	for ticker in p:
		try:
			tmp = p[ticker][(p[ticker].dates >= startDate) & (p[ticker].dates <= endDate)]
			di['change'].append(tmp['Close'].iloc[-1]/tmp['Close'].iloc[0] - 1)
			di['ticker'].append(ticker)
		except IndexError:
			pass

	data = pd.DataFrame(di).sort_values('change')
	data = data[data.ticker.isin(data.ticker.head(numStocks).tolist())]

	
	returns = []
	for ticker in data.ticker:
		print ticker	
		tmp = p[ticker][(p[ticker].dates >= endDate) & (p[ticker].dates <= returnDate)]
		tmp = web.DataReader(ticker,'google', endDate, returnDate)
		returns.append((tmp['Close'].iloc[-1], tmp['Close'].iloc[0]))
		time.sleep(5)
	allReturns.append(returns)

s = pd.Series(allReturns)
returnsList = np.zeros(numDays) + investment
plotReturns = [[investment] for _ in range(numDays)]
for i, j in enumerate(s):
	stockInvestment = returnsList[i % numDays] / float(numStocks)
	tmp = 0
	for k in j:
		initialPrice = k[1]
		numStocksToBuy = round(stockInvestment / initialPrice, 0)
		mini_investment = numStocksToBuy * initialPrice
		leftovers = stockInvestment - mini_investment
		increase = mini_investment * (k[0] / k[1])
		tmp += (increase + leftovers)	
	returnsList[i % numDays] = tmp
	plotReturns[i % numDays].append(tmp)
print 'Initial investment of $%s is worth %s%% of its value' % (investment*numDays, 100*round(np.sum(returnsList) / (investment * numDays),4))

plt.figure()
for performance in plotReturns:
	plt.plot(performance)
plt.show()

