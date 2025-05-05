# Planning for Financial Data Tools


## Backtesting
- replay (stream) historical data. Decide whether to go long or short. You have to define a take profit level and a stop loss level and if you see iether of those you have to get out of the trade. 
Position sizing.
At some point, we want more advanced exit strategies. E.g. you may have a take profit level to sell your position. 
Position sizing and exit strategies are most likely where you get your edge. This is the "art". 


## Paper trading
each bullet is a tool

### long trading strategy:
 - buy to open
 - sell to close

### short selling strategy:
 - sell to open
 - buy to close

### Misc
- generate pre-market report (maybe use webscraping mcp server from anthropic)
- check open positions
- check daily P&L
- check daily data usage
- generate daily report (end of market report)
