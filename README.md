# Stock Manager

## Description
A simple Python desktop app for monitoring the stock market and the prices of individual stocks in the user's posession.
Uses data from ![stooq](https://stooq.com).
This app does not access your account on any broker websites.
The user has to manually import all the changes he does online.

## Features
- monitoring the stock market
- keeping track of your shares
- calculating the gains on individual shares and on groups of shares
- currently supported markets (all the market data available on ![stooq](https://stooq.com))
    - US
    - PL
    - HU 

## Usage

### Home screen
The home screen presents all the options on the left navigation bar.
In the top left corner you can select the market to operate within.

![](https://media.discordapp.net/attachments/420283310833664002/938099803370442792/unknown.png)

### Adding shares
Adding shares requires the name of the stock, the buying price of the stock and the number of shares.

![](https://media.discordapp.net/attachments/420283310833664002/938099853857271868/unknown.png)

### Selling stocks
In order to record the selling of shares, pick the stock name from the drop-down menu and enter the selling price and the number of shares.

![](https://media.discordapp.net/attachments/420283310833664002/938099879882919936/unknown.png)

### Summary
Daily summary of income.
This process requires many queries sent to stooq, so this may take a while.
There is a daily limit of queries from stooq.
If the user surpasses the limit, the last recorded summary will be displayed.

![](https://media.discordapp.net/attachments/420283310833664002/938099914498539590/unknown.png) //summary

### Transaction history
Displays all transactions recorded within the app.

![](https://media.discordapp.net/attachments/420283310833664002/938099944479404082/unknown.png) //history

### Price history
Displays the price history of the selected stock.

![](https://media.discordapp.net/attachments/420283310833664002/938100165766676540/unknown.png) //price

### Account
Balances in all supported currencies.
Based on the buying and selling prices.

![](https://media.discordapp.net/attachments/420283310833664002/938100231738900570/unknown.png) //acc

### Settings
Theme settings.

![](https://media.discordapp.net/attachments/420283310833664002/938100283903459379/unknown.png) //theme