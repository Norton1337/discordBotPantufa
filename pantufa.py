import discord
import random
import json
import tweepy
import datetime
from datetime import date
from datetime import datetime
import calendar
import asyncio
from binance.client import Client
from binance.enums import *
from discord import Intents
from discord.ext import tasks, commands
from discord.ext.commands import MemberConverter
from discord.ext.commands import VoiceChannelConverter
from discord.ext.commands import RoleConverter


with open('private.json', 'r+', encoding='utf-8') as json_file:
    private = json.load(json_file)

twitterApiKey = private["private"]["tweepy"]["twitterApiKey"]
twitterSecretKey = private["private"]["tweepy"]["twitterSecretKey"]

twtAccessToken = private["private"]["tweepy"]["twtAccessToken"]
twtAccessTokenSecret = private["private"]["tweepy"]["twtAccessTokenSecret"]
twitterBearerToken = private["private"]["tweepy"]["twitterBearerToken"]
twitterId = private["private"]["tweepy"]["twitterId"]

api_key = private["private"]["binance"]["api_key"]
api_secret = private["private"]["binance"]["api_secret"]


realWallet = [0 for _ in range(6)]
whereWallet = ["" for _ in range(6)]

clientB = Client(api_key, api_secret)
account = clientB.get_account()
wallet = []

auth = tweepy.OAuthHandler(twitterApiKey, twitterSecretKey)
auth.set_access_token(twtAccessToken, twtAccessTokenSecret)
api = tweepy.API(auth)

client = commands.Bot(command_prefix='-', intents=Intents.all())
client.remove_command("help")

memberConverter = MemberConverter()
channelConverter = VoiceChannelConverter()
roleConverter = RoleConverter()

chooseUser = ['null' for _ in range(10)]
chooseUserRating = [0.0 for _ in range(10)]

SRGS = private["private"]["SRGS"]
QFCHESS = private["private"]["QFCHESS"]

"""####################################### vv Binance Functions vv ##################################################"""


def minAmount(coin):
    price = getPrice(coin)
    coinsInfo = clientB.get_symbol_info(coin)
    minPrice = coinsInfo["filters"][3]["minNotional"]
    return float(minPrice) / price


def buyCoin(coin, amount):
    price = getPrice(coin)
    lowestAmount = minAmount(coin)
    print(amount * price)
    print(amount)
    print(lowestAmount)
    if amount >= lowestAmount:
        try:
            order = clientB.create_order(
                symbol=coin,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=format(amount, ".1f")
            )
            with open('private.json', 'r+', encoding='utf-8') as transactionFile:
                information = json.load(transactionFile)
                information["transactions"].append({"transactionId": len(information["transactions"]),
                                                    "dateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    "coinPair": coin,
                                                    "side": "Buy",
                                                    "averagePrice": price,
                                                    "amountCrypto": amount,
                                                    "amountCur": amount * price})
                transactionFile.seek(0)
                json.dump(information, transactionFile, indent=4)
                transactionFile.truncate()
            print("Just BOUGHT {} coins at {}€, {}€ each".format(coin, amount * price, price))
            return order
        except Exception as e:
            print(e)
    else:
        print("You need to buy {} or more at {}!".format(lowestAmount, price))


def sellCoin(coin, amount):
    price = getPrice(coin)
    try:
        order = clientB.create_order(
            symbol=coin,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=amount
        )
        with open('private.json', 'r+', encoding='utf-8') as transactionFile:
            information = json.load(transactionFile)
            information["transactions"].append({"transactionId": len(information["transactions"]),
                                                "dateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                "coinPair": coin,
                                                "side": "Sell",
                                                "averagePrice": price,
                                                "amountCrypto": amount,
                                                "amountCur": amount * price})
            transactionFile.seek(0)
            json.dump(information, transactionFile, indent=4)
            transactionFile.truncate()
        print("Just SOLD {} coins at {}€, {}€ each".format(coin, amount * price, price))
        return order
    except Exception as e:
        print(e)


def getBalance(coin):
    for k in range(len(wallet)):
        if wallet[k][0] == str(coin):
            return wallet[k]


def getAverageHigh(coin, timeAgo):
    if timeAgo == "15 min UTC":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_1MINUTE, timeAgo)
    else:
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeAgo)
    high = 0
    i = 0
    for i in range(len(klines)):
        high += float(klines[i][2])
    return high / float(i + 1)


def getAverageLow(coin, timeAgo):
    klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeAgo)
    low = 0
    i = 0
    for i in range(len(klines)):
        low += float(klines[i][3])
    return low / float(i + 1)


def isPriceBetweenAverage(avgH, avgL, coin):
    if avgH >= getPrice(coin) >= avgL:
        return "In Between"
    elif getPrice(coin) > avgH:
        return "GOING UP"
    elif getPrice(coin) < avgL:
        return "GOING DOWN"


def lastHigh(coin, timeInterval, timeStart):
    test = 0
    klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeStart)
    if timeInterval == "15m":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeStart)
    elif timeInterval == "1h":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_1HOUR, timeStart)
    elif timeInterval == "1d":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_1DAY, timeStart)
    for i in range(len(klines)):
        if float(klines[i][2]) > test:
            test = float(klines[i][2])
    return test


def lastLow(coin, timeInterval, timeStart):
    test = 9999999999
    klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeStart)
    if timeInterval == "15m":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, timeStart)
    elif timeInterval == "1h":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_1HOUR, timeStart)
    elif timeInterval == "1d":
        klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_1DAY, timeStart)
    for i in range(len(klines)):
        if float(klines[i][3]) < test:
            test = float(klines[i][3])
    return test


def setBalances():
    bal = account['balances']
    for i in bal:
        if float(i['free']) > 0:
            wallet.append([i['asset'], i['free']])


def getPrice(currency):
    prices = clientB.get_symbol_ticker()
    for i in prices:
        if i['symbol'] == currency:
            currentPrice = i['price']
            return float(currentPrice)


def getChange(coin):
    klines = clientB.get_historical_klines(coin, Client.KLINE_INTERVAL_15MINUTE, "30m")
    return 100 - (float(klines[0][4]) / float(klines[1][4]) * 100)


"""####################################### ^^ Binance Functions ^^ ##################################################"""

def saveToFile():
    with open('private.json', 'r+', encoding='utf-8') as json_files:
                json_files.seek(0)
                json.dump(private, json_files, indent=4)
                json_files.truncate()


@client.event
async def on_member_join(member: discord.Member):
    channel = client.get_channel(552955081956524052)
    greetings = ["Greetings, summoner {}!", "Hello there {}!", "Here's {}!", "Say hello to my little friend {}!",
                 "Oh hi {}!"]
    item = random.choice(greetings)
    await channel.send(item.format(member.mention))


@client.event
async def on_member_remove(member: discord.Member):
    channel = client.get_channel(552955081956524052)
    farewells = ["Hasta la vista, {}", "It will be rubbish here without you {}!",
                 "Farewell, and may the blessing of Elves and Men andn all Free Folk go with you.\n"
                 "May the stars shine upon your faces {}!","I hope our paths cross again soon {}.",
                 "Wherever you’re going, they’re lucky to have you {}!"]
    item = random.choice(farewells)
    await channel.send(item.format(member.mention))


@client.event
async def on_ready():
    activity = discord.Activity(name='Long walks on the leash', type=discord.ActivityType.watching)
    getHolidays.start()
    timer.start()
    crypto.start()
    await client.change_presence(activity=activity)
    print('Pantufa is ready.')


@client.command(aliases=['getcoin', 'getCoin', 'GetCoin', 'Getcoin'])
async def getCoinInfo(ctx, currency):
    if str(ctx.message.guild.id) != SRGS:
        return
    prices = clientB.get_symbol_ticker()
    coinInfo = clientB.get_symbol_info(currency)
    for i in prices:
        if i['symbol'] == currency:
            change = getChange(currency)
            if change < 0:
                color = discord.Color.red()
            elif change > 0:
                color = discord.Color.green()
            else:
                color = discord.Color.orange()
            currentPrice = i['price']
            embed = discord.Embed(
                title=str(coinInfo['baseAsset']),
                color=color
            )
            embed.add_field(name='1 ' + str(coinInfo['baseAsset'] + " = "),
                            value=currentPrice + " " + coinInfo['quoteAsset'], inline=False)
            embed.add_field(name='Change:',
                            value=str(format(change, ".3f") + "%"), inline=False)
            await ctx.send(embed=embed)


@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')


@client.command(aliases=['tweet', 'Tweetbot', 'tweetbot', 'Tweet', 'TweetBot'])
@commands.has_any_role(private["private"]["roles"][2])
async def tweetBot(ctx, *message):
    if str(ctx.message.guild.id) != SRGS:
        return
   
    
    substring = private["private"]["blockedWords"]
    theTweet = ""
    for i in range(len(message)):
        theTweet += message[i] + " "
    if theTweet:
        isSafe = True
        for word in range(len(substring)):
            if substring[word] in theTweet.lower():
                isSafe = False
        if isSafe:
            api.update_status(str(theTweet) + "\n-tweeted with my discord bot")
            timeline = api.user_timeline(user_id=twitterId, count=1)
            tweetID = timeline[0].id
            await ctx.send("Just tweeted! \n" + "https://twitter.com/anyuser/status/" + str(tweetID))
        else:
            await ctx.send("Yo wtf I'm not gonna tweet that")
    else:
        await ctx.send("What do you want me to tweet?")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def editUser(ctx, member: discord.Member, rate):
    if str(ctx.message.guild.id) != SRGS:
        return
    exists = False
    for user in private["scrimmageInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
    if exists:
        if 1 <= int(rate) >= 10:
            await ctx.send('Rating must be between 1 and 10!')
        else:
            tempNum = 0
            theMember = None
            for existingUsers in private["scrimmageInfo"]["players"]:
                if existingUsers["id"] == str(member):
                    theMember = existingUsers
                    break
                tempNum += 1
            lastRate = theMember["rating"]
            theMember["rating"] = rate
            await ctx.send(str(member) + "'s rating was [" + str(lastRate) + "] and now it's [" + str(rate) + "]")
            private["scrimmageInfo"]["players"][tempNum] = theMember
            saveToFile()
    else:
        await ctx.send(str(member) + " is not in the system")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def removeUser(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    exists = False
    for user in private["scrimmageInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
            tempNum = 0
            for existingUsers in private["scrimmageInfo"]["players"]:
                if existingUsers["id"] == str(member):
                    del private["scrimmageInfo"]["players"][tempNum]
                tempNum += 1
            await ctx.send(str(member) + " has been deleted")
            saveToFile()
    if not exists:
        await ctx.send(str(member) + " is not in the system")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def addUser(ctx, member: discord.Member, rating):
    if str(ctx.message.guild.id) != SRGS:
        return
    exists = False
    for user in private["scrimmageInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
    if not exists:
        if 1 < int(rating) > 10:
            await ctx.send('Rating must be between 1 and 10!')
        else:
            private["scrimmageInfo"]["players"].append({"id": str(member), "rating": rating, "totalGame": "0", "totalWins": "0"})
            await ctx.send('Player [' + str(len(private["scrimmageInfo"]["players"])) + ']: ' +
                           str(private["scrimmageInfo"]["players"][len(private["scrimmageInfo"]["players"]) - 1]["id"]) +
                           '\nRating: ' + str(private["scrimmageInfo"]["players"][len(private["scrimmageInfo"]["players"]) - 1]["rating"]) + '\n')

        saveToFile()
    else:
        await ctx.send('This players is already in the system.')


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def selectUser(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    if str(member) not in chooseUser:
        exists = False
        for user in private["scrimmageInfo"]["players"]:
            if str(member) in user["id"]:
                exists = True
        if exists:
            count = 0
            for i in range(len(chooseUser)):
                if chooseUser[i] != 'null':
                    count += 1

            if count == 10:
                await ctx.send("There are already 10 players selected!")
            else:
                for user in private["scrimmageInfo"]["players"]:
                    if str(member) in user["id"]:
                        chooseUser[count] = str(user["id"])
                        chooseUserRating[count] = user["rating"]
                await ctx.send(str(member) + ' has been selected')
        else:
            await ctx.send(str(member) + ' is not in the system')
    else:
        await ctx.send(str(member) + ' has already been chosen!')


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def removeSelectedUser(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    if str(member) in chooseUser:
        i = 0
        for i in range(len(private["scrimmageInfo"]["players"])):
            if str(member) == chooseUser[i]:
                break
        del chooseUser[i]
        del chooseUserRating[i]
        chooseUser.append("null")
        chooseUserRating.append(0)
        await ctx.send(str(member) + " has been unselected ")
    else:
        await ctx.send(str(member) + " is not in the system")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def showSelected(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    if len(chooseUser) > 0:
        embed = discord.Embed(
            title='Selected Users:',
            color=discord.Colour.blurple()
        )
        for i in range(len(chooseUser)):
            if chooseUser[i] != 'null':
                embed.add_field(name='Player [' + str(i + 1) + ']', value='`' + str(chooseUser[i]) + '`' +
                                                                          ' - Rating: ' +
                                                                          str(chooseUserRating[i]), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No user is yet chosen")


@client.command()
async def listUsers(ctx, page=None):
    if str(ctx.message.guild.id) != SRGS:
        return
    if not page:
        page = 1

    totalPages = int((len(private["scrimmageInfo"]["players"])) / 10)
    if len(private["scrimmageInfo"]["players"]) % 10 != 0:
        totalPages += 1
    if int(page) > totalPages:
        await ctx.send("There are not that many pages!")
    else:
        if len(private["scrimmageInfo"]["players"]) <= 10:
            page = 1
        amount = 0
        embed = discord.Embed(
            title='Players [Page: ' + str(page) + ' / ' + str(totalPages) + ']',
            description='',
            color=discord.Colour.dark_green()
        )
        for i in range(len(private["scrimmageInfo"]["players"])):
            amount += 1

            if (int(page) * 10 - 10) < amount < ((int(page) * 10) + 1):
                embed.add_field(name='Player [' + str(i + 1) + ']', value='`' + str(private["scrimmageInfo"]["players"][i]["id"]) + '`' +
                                                                          ' - Rating: ' +
                                                                          str(private["scrimmageInfo"]["players"][i]["rating"]),
                                inline=False)
        await ctx.send(embed=embed)


@client.command()
async def searchUser(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    holdInt = -1
    for i in range(len(private["scrimmageInfo"]["players"])):
        mentionableName = await memberConverter.convert(ctx, private["scrimmageInfo"]["players"][i]["id"])

        if member == mentionableName:
            holdInt = i
            break

    if holdInt == -1:
        await ctx.send("That user does not exist!")
    else:
        embed = discord.Embed(
            title=str(private["scrimmageInfo"]["players"][holdInt]["id"]),
            description='Rating: ' + str(private["scrimmageInfo"]["players"][holdInt]["rating"]),
            color=discord.Colour.dark_purple()
        )
        if int(private["scrimmageInfo"]["players"][holdInt]["totalGames"]) > 0:
            if ((int(private["scrimmageInfo"]["players"][holdInt]["totalWins"]) / int(private["scrimmageInfo"]["players"][holdInt]["totalGames"])) * 100) < 50:
                embed = discord.Embed(
                    title=str(private["scrimmageInfo"]["players"][holdInt]["id"]),
                    description='Rating: ' + str(private["scrimmageInfo"]["players"][holdInt]["rating"]),
                    color=discord.Colour.dark_red()
                )
            elif ((int(private["scrimmageInfo"]["players"][holdInt]["totalWins"]) /
                   int(private["scrimmageInfo"]["players"][holdInt]["totalGames"])) * 100) > 50:
                embed = discord.Embed(
                    title=str(private["scrimmageInfo"]["players"][holdInt]["id"]),
                    description='Rating: ' + str(private["scrimmageInfo"]["players"][holdInt]["rating"]),
                    color=discord.Colour.dark_green()
                )
            elif ((int(private["scrimmageInfo"]["players"][holdInt]["totalWins"]) /
                   int(private["scrimmageInfo"]["players"][holdInt]["totalGames"])) * 100) == 50:
                embed = discord.Embed(
                    title=str(private["scrimmageInfo"]["players"][holdInt]["id"]),
                    description='Rating: ' + str(private["scrimmageInfo"]["players"][holdInt]["rating"]),
                    color=discord.Colour.dark_orange()
                )

            embed.add_field(name='Stats: ', value='{0}W - {1}L \n'
                                                  ' Win Ratio {2}%'.format(private["scrimmageInfo"]["players"][holdInt]["totalWins"],
                                                                           int(private["scrimmageInfo"]["players"][holdInt]["totalGames"]) -
                                                                           int(private["scrimmageInfo"]["players"][holdInt]["totalWins"]),
                                                                           (int(private["scrimmageInfo"]["players"][holdInt]["totalWins"]) /
                                                                            int(private["scrimmageInfo"]["players"][holdInt]["totalGames"]))
                                                                           * 100))
        else:
            embed.add_field(name='Stats: ', value='No games')
        await ctx.send(embed=embed)


@client.command()
@commands.has_any_role(private["private"]["roles"][0])
async def resetStats(ctx, member: discord.Member, everyone=None):
    if str(ctx.message.guild.id) != SRGS:
        return
    if not everyone:
        for i in range(len(private["scrimmageInfo"]["players"])):
            if private["scrimmageInfo"]["players"][i]["id"] == str(member):
                private["scrimmageInfo"]["players"][i]["totalWins"] = 0
                private["scrimmageInfo"]["players"][i]["totalGames"] = 0
    if everyone == "resetEverything":
        for i in range(len(private["scrimmageInfo"]["players"])):
            private["scrimmageInfo"]["players"][i]["totalWins"] = 0
            private["scrimmageInfo"]["players"][i]["totalGames"] = 0
    await ctx.send("Stats have been reset")
    saveToFile()


blueTeam = []
redTeam = []


@client.command()
async def customSelect(ctx, team: discord.Role, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    blueRole = discord.utils.find(lambda r: r.name == 'BlueTeam', ctx.guild.roles)
    redRole = discord.utils.find(lambda r: r.name == 'RedTeam', ctx.guild.roles)

    if team == blueRole:
        if len(blueTeam) < 5:
            if str(member) not in blueTeam and str(member) not in redTeam:
                blueTeam.append(str(member))
                await ctx.send("{} added to Blue team")
            else:
                await ctx.send("User already in a team")
        else:
            await ctx.send("Blue team is full!")
    elif team == redRole:
        if len(redTeam) < 5:
            if str(member) not in blueTeam and str(member) not in redTeam:
                redTeam.append(str(member))
                await ctx.send("{} added to Red team")
            else:
                await ctx.send("User already in a team")
        else:
            await ctx.send("Red team is full!")
    else:
        await ctx.send("Unknown team")


@client.command()
async def customDeselect(ctx, team: discord.Role, member: discord.Member):
    if str(ctx.message.guild.id) != SRGS:
        return
    blueRole = discord.utils.find(lambda r: r.name == 'BlueTeam', ctx.guild.roles)
    redRole = discord.utils.find(lambda r: r.name == 'RedTeam', ctx.guild.roles)

    if team == blueRole:
        if member in team:
            blueTeam.remove(str(member))
            await ctx.send("{} has been removed from Blue Team".format(str(member)))
        else:
            await ctx.send("Can't remove {}, he is not in the Blue Team".format(str(member)))
    elif team == redRole:
        if member in team:
            redTeam.remove(str(member))
            await ctx.send("{} has been removed from Red Team".format(str(member)))
        else:
            await ctx.send("Can't remove {}, he is not in the Red Team".format(str(member)))
    else:
        await ctx.send("Unknown team")


@client.command()
async def showCustomTeams(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    embed1 = discord.Embed(
        title='Blue Team',
        description='You get first pick!',
        color=discord.Colour.blue()
    )
    embed2 = discord.Embed(
        title='Red Team',
        description='You get second pick!',
        color=discord.Colour.red()
    )
    for i in range(len(blueTeam)):
        embed1.add_field(name="Player [{}]".format(str(i + 1)), value="{}".format(blueTeam[i]))
    for i in range(len(redTeam)):
        embed2.add_field(name="Player [{}]".format(str(i + 1)), value="{}".format(redTeam[i]))
    if len(blueTeam) > 0:
        await ctx.send(embed=embed1)
    if len(redTeam) > 0:
        await ctx.send(embed=embed2)


@client.command()
async def removeCustomTeams(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    blueTeam.clear()
    redTeam.clear()
    await ctx.send("Custom teams cleared!")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def createTeams(ctx, custom=None):
    if str(ctx.message.guild.id) != SRGS:
        return
    if not custom:
        count = 0
        for i in range(10):
            if chooseUser[i] != 'null':
                count += 1
        if count == 10:
            for t in range(10):
                for y in range(10):
                    if chooseUserRating[t] == chooseUserRating[y]:
                        if random.randint(1, 2) == 2:
                            intHolder = chooseUserRating[y]
                            chooseUserRating[y] = chooseUserRating[t]
                            chooseUserRating[t] = intHolder
                            stringHolder = chooseUser[y]
                            chooseUser[y] = chooseUser[t]
                            chooseUser[t] = stringHolder

            await ctx.send('Creating Teams')
            team1 = ['null' for _ in range(5)]
            team1_rating = [0 for _ in range(5)]
            team1_count = 0

            team2 = ['null' for _ in range(5)]
            team2_rating = [0 for _ in range(5)]
            team2_count = 0

            chosen = ['null' for _ in range(10)]

            while team2_count + team1_count != 10:
                pos = 0
                number = -1
                for i in range(10):
                    if chooseUser[i] not in chosen:
                        if int(chooseUserRating[i]) > int(number):
                            number = chooseUserRating[i]
                            pos = i

                for k in range(10):
                    lVar = 0

                    while chosen[lVar] != 'null':
                        lVar += 1
                    chosen[lVar] = chooseUser[pos]

                    numb1 = 0
                    for test in range(5):
                        numb1 += int(team1_rating[test])
                    numb2 = 0
                    for test in range(5):
                        numb2 += int(team2_rating[test])

                    if numb2 >= numb1:
                        num1 = 0
                        while team1[num1] != 'null':
                            num1 += 1
                        team1[num1] = chooseUser[pos]
                        team1_rating[num1] = chooseUserRating[pos]
                        team1_count += 1
                        break
                    else:
                        num2 = 0
                        while team2[num2] != 'null':
                            num2 += 1
                        team2[num2] = chooseUser[pos]
                        team2_rating[num2] = chooseUserRating[pos]
                        team2_count += 1
                        break

            numbOne = 0
            for i in range(5):
                numbOne += int(team1_rating[i])

            numbTwo = 0
            for i in range(5):
                numbTwo += int(team2_rating[i])

            embed1 = discord.Embed(
                title='Blue Team [Rating: ' + str(numbOne / 5) + ']',
                description='You get first pick!',
                color=discord.Colour.blue()
            )
            embed1.set_footer(text='Good luck!')
            for i in range(5):
                mentionableName = await memberConverter.convert(ctx, team1[i])
                embed1.add_field(name='Player ' + str(i + 1) + ': ', value=' - ' + mentionableName.mention + " [" +
                                                                           str(team1_rating[i]) + "] ", inline=False)
            await ctx.send(embed=embed1)

            embed2 = discord.Embed(
                title='Red Team [Rating: ' + str(numbTwo / 5) + ']',
                description='You get second pick!',
                color=discord.Colour.red()
            )
            embed2.set_footer(text='Good luck!')
            for i in range(5):
                mentionableName = await memberConverter.convert(ctx, team2[i])
                embed2.add_field(name='Player ' + str(i + 1) + ': ', value=' - ' + mentionableName.mention + " ["
                                                                           + str(team2_rating[i]) + "] ", inline=False)
            await ctx.send(embed=embed2)

            blueRole = await roleConverter.convert(ctx, str(805914751523749938))
            for i in range(len(team1)):
                blueName = await memberConverter.convert(ctx, team1[i])
                await ctx.invoke(client.get_command('addUserRole'), member=blueName, role=blueRole)
            redRole = await roleConverter.convert(ctx, str(805914838794108979))
            for i in range(len(team2)):
                redName = await memberConverter.convert(ctx, team2[i])
                await ctx.invoke(client.get_command('addUserRole'), member=redName, role=redRole)
            await ctx.send("Teams assigned!")
        else:
            await ctx.send('Not enough users')

    elif custom == "custom" or custom == "Custom":
        count = len(blueTeam) + len(redTeam)
        if count == 10:
            blueRole = await roleConverter.convert(ctx, str(805914751523749938))
            for i in range(len(blueTeam)):
                blueName = await memberConverter.convert(ctx, blueTeam[i])
                await ctx.invoke(client.get_command('addUserRole'), member=blueName, role=blueRole)
            redRole = await roleConverter.convert(ctx, str(805914838794108979))
            for i in range(len(redTeam)):
                redName = await memberConverter.convert(ctx, redTeam[i])
                await ctx.invoke(client.get_command('addUserRole'), member=redName, role=redRole)
            await ctx.send("Teams assigned!")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def startGame(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    await ctx.invoke(client.get_command('clearRoles'))
    blueChannel = await channelConverter.convert(ctx, str(805915011024683019))
    redChannel = await channelConverter.convert(ctx, str(805915420065529896))
    for i in range(len(chooseUser)):
        userMember = await memberConverter.convert(ctx, chooseUser[i])
        blueRole = discord.utils.find(lambda r: r.name == 'BlueTeam', ctx.guild.roles)
        redRole = discord.utils.find(lambda r: r.name == 'RedTeam', ctx.guild.roles)
        if blueRole in userMember.roles:
            await ctx.invoke(client.get_command('moveUser'), member=userMember, channel=blueChannel)
        if redRole in userMember.roles:
            await ctx.invoke(client.get_command('moveUser'), member=userMember, channel=redChannel)

    everyone = await roleConverter.convert(ctx, str(547826903923556353))

    await blueChannel.set_permissions(everyone, read_messages=True, connect=False)
    await redChannel.set_permissions(everyone, read_messages=True, connect=False)
    await ctx.send("Jobs done!")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def clearRoles(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    blueRole = await roleConverter.convert(ctx, str(805914751523749938))
    redRole = await roleConverter.convert(ctx, str(805914838794108979))
    await ctx.send("Clearing Roles...")
    for i in range(len(private["scrimmageInfo"]["players"])):
        memberName = await memberConverter.convert(ctx, private["scrimmageInfo"]["players"][i]["id"])
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=blueRole)
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=redRole)
    for i in range(len(blueTeam)):
        memberName = await memberConverter.convert(ctx, private["scrimmageInfo"]["players"][i]["id"])
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=blueRole)
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=redRole)
    for i in range(len(redTeam)):
        memberName = await memberConverter.convert(ctx, private["scrimmageInfo"]["players"][i]["id"])
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=blueRole)
        await ctx.invoke(client.get_command('removeUserRole'), member=memberName, role=redRole)
    await ctx.send("Roles Cleared!")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def restartGame(ctx, winnerRole: discord.Role = None):
    if str(ctx.message.guild.id) != SRGS:
        return
    if winnerRole:
        for counting in range(len(chooseUser)):
            userMember = await memberConverter.convert(ctx, chooseUser[counting])
            if winnerRole in userMember.roles:
                for i in range(len(private["scrimmageInfo"]["players"])):
                    if private["scrimmageInfo"]["players"][i]["id"] == str(userMember):
                        private["scrimmageInfo"]["players"][i]["totalWins"] = int(private["scrimmageInfo"]["players"][i]["totalWins"]) + 1
            for i in range(len(private["scrimmageInfo"]["players"])):
                if private["scrimmageInfo"]["players"][i]["id"] == str(userMember):
                    private["scrimmageInfo"]["players"][i]["totalGames"] = int(private["scrimmageInfo"]["players"][i]["totalGames"]) + 1

        saveToFile()
    await ctx.invoke(client.get_command('startGame'))


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def endGame(ctx, winnerRole: discord.Role = None):
    if str(ctx.message.guild.id) != SRGS:
        return
    if winnerRole:
        for counting in range(len(chooseUser)):
            userMember = await memberConverter.convert(ctx, chooseUser[counting])
            if winnerRole in userMember.roles:
                for i in range(len(private["scrimmageInfo"]["players"])):
                    if private["scrimmageInfo"]["players"][i]["id"] == str(userMember):
                        private["scrimmageInfo"]["players"][i]["totalWins"] = int(private["scrimmageInfo"]["players"][i]["totalWins"]) + 1
            for i in range(len(private["scrimmageInfo"]["players"])):
                if private["scrimmageInfo"]["players"][i]["id"] == str(userMember):
                    private["scrimmageInfo"]["players"][i]["totalGames"] = int(private["scrimmageInfo"]["players"][i]["totalGames"]) + 1

        saveToFile()

    await ctx.invoke(client.get_command('clearRoles'))
    everyone = await roleConverter.convert(ctx, str(547826903923556353))
    blueChannel = await channelConverter.convert(ctx, str(805915011024683019))
    redChannel = await channelConverter.convert(ctx, str(805915420065529896))
    await blueChannel.set_permissions(everyone, read_messages=False, connect=False)
    await redChannel.set_permissions(everyone, read_messages=False, connect=False)


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def moveBack(ctx):
    if str(ctx.message.guild.id) != SRGS:
        return
    scrimmageChannel = await channelConverter.convert(ctx, str(805604020873986089))
    for i in range(len(chooseUser)):
        userMember = await memberConverter.convert(ctx, chooseUser[i])
        await ctx.invoke(client.get_command('moveUser'), member=userMember, channel=scrimmageChannel)
    await ctx.send("Jobs done!")


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def moveUser(ctx, member: discord.Member, channel: discord.VoiceChannel):
    if str(ctx.message.guild.id) != SRGS:
        return
    try:
        await discord.Member.move_to(member, channel)
        await ctx.send("Moved " + member.mention + " to " + channel.mention)
    except Exception as e:
        print("ERROR : " + str(e))


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def addUserRole(ctx, member: discord.Member, role: discord.Role):
    if str(ctx.message.guild.id) != SRGS:
        return
    try:
        await member.add_roles(role)
        await ctx.send("Gave the role " + role.mention + " to " + member.mention)
    except Exception as e:
        print("ERROR : " + str(e))


@client.command()
@commands.has_any_role(private["private"]["roles"][0], private["private"]["roles"][1])
async def removeUserRole(ctx, member: discord.Member, role: discord.Role):
    if str(ctx.message.guild.id) != SRGS:
        return
    try:
        await member.remove_roles(role)
        await ctx.send("Removed the role " + role.mention + " from " + member.mention)
    except Exception as e:
        print("ERROR : " + str(e))


@client.group(invoke_without_command=True)
async def help(ctx):

    if str(ctx.message.guild.id) == SRGS:
        embedSRGS = discord.Embed(title="SRGS Help", color=discord.Colour.random())
        embedSRGS.set_footer(text="User -help [command] for additional information.")
        embedSRGS.add_field(name="Moderation", value='`moveUser`, `addUserRole`, `removeUserRole`', inline=False)
        embedSRGS.add_field(name="Manage database", value='`addUser`, `editUser`, `removeUser`, `resetStats`',
                        inline=False)
        embedSRGS.add_field(name="Custom Game Related", value='`searchUser`, `listPlayers`,`selectUser`, `removeSelectedUser`,'
                                                        ' `chooseTeams`, `createTeams`, `startGame`, `clearRoles`,'
                                                        ' `restartGame`, `endGame`, `moveBack`', inline=False)
        embedSRGS.add_field(name="Other", value='`tweetBot`, `getCoinInfo`, `getTimetable`, `nextHoliday`, `holidayMonth`',inline=False)
        await ctx.send(embed=embedSRGS)

    if str(ctx.message.guild.id) == QFCHESS:
        embedQFCHESS = discord.Embed(title="QFCHESS Help", color=discord.Colour.random())
        embedQFCHESS.set_footer(text="User -help [command] for additional information.")
        embedQFCHESS.add_field(name="Chess Database", value='`addPlayer`, `editPlayer`, `removePlayer`, `searchPlayer`, `listPlayers`',
                        inline=False)
        embedQFCHESS.add_field(name="Other", value='`getCoinInfo`, `nextHoliday`, `holidayMonth`',inline=False)
        await ctx.send(embed=embedQFCHESS)


@help.command()
async def addPlayer(ctx):
    embed = discord.Embed(title="addPlayer", description="Adds the player to the database",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-addPlayer <member>`')
    await ctx.send(embed=embed)


@help.command()
async def editPlayer(ctx):
    embed = discord.Embed(title="editPlayer", description="Updates the player's stats",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-editPlayer <member> ["wins/losses/ties"]`')
    await ctx.send(embed=embed)


@help.command()
async def removePlayer(ctx):
    embed = discord.Embed(title="removePlayer", description="Removes the user from the database",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-removePlayer <member>`')
    await ctx.send(embed=embed)


@help.command()
async def searchPlayer(ctx):
    embed = discord.Embed(title="searchPlayer", description="Search information about a player",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-searchPlayer <member>`')
    await ctx.send(embed=embed)


@help.command()
async def listPlayeres(ctx):
    embed = discord.Embed(title="listPlayeres", description="Get a list with all the players",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-listPlayers`')
    await ctx.send(embed=embed)


@help.command()
async def holidayMonth(ctx):
    embed = discord.Embed(title="holidayMonth", description="Shows all holidays/events in a month",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-holidayMonth *optional:* {"month"}`',inline=False)
    await ctx.send(embed=embed)

@help.command()
async def nextHoliday(ctx):
    embed = discord.Embed(title="nextHoliday", description="Shows the next upcoming holiday/event",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-nextHoliday`',inline=False)
    await ctx.send(embed=embed)

@help.command()
async def getTimetable(ctx):
    embed = discord.Embed(title="getTimetable", description="Check a timetable",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-getTimetable ["person"] *optional:* {"day of week"}`',inline=False)
    embed.add_field(name="**Aliases**", value='`-gtt`, `-GTT`',inline=False)
    await ctx.send(embed=embed)

@help.command()
async def getCoinInfo(ctx):
    embed = discord.Embed(title="getCoinInfo", description="Get information of a cryptocurrency",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-getCoinInfo ["currency"]`',inline=False)
    embed.add_field(name="**Aliases**", value='`-getcoin`, `-getCoin`, `-GetCoin`, `-Getcoin`',inline=False)
    await ctx.send(embed=embed)

@help.command()
async def tweetBot(ctx):
    embed = discord.Embed(title="tweetBot", description="Tweet something in Norton's twitter",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-tweetBot ["Type text here"]`',inline=False)
    embed.add_field(name="**Aliases**", value='`-tweet`, `-Tweetbot`, `-tweetbot`, `-Tweet`, `-TweetBot`',inline=False)
    await ctx.send(embed=embed)

@help.command()
async def moveUser(ctx):
    embed = discord.Embed(title="moveUser", description="Moves a user to another voice channel",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-moveUser <member> ["channel"]`')
    await ctx.send(embed=embed)


@help.command()
async def addUserRole(ctx):
    embed = discord.Embed(title="addUserRole", description="Adds a role to the user",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-addUserRole <member> ["role"]`')
    await ctx.send(embed=embed)


@help.command()
async def removeUserRole(ctx):
    embed = discord.Embed(title="removeUserRole", description="Removes a role from the user",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-removeUserRole <member> ["role"]`')
    await ctx.send(embed=embed)


@help.command()
async def addUser(ctx):
    embed = discord.Embed(title="addUser", description="Adds the user to the database",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-addUser <member> [rating]`')
    await ctx.send(embed=embed)


@help.command()
async def editUser(ctx):
    embed = discord.Embed(title="editUser", description="Updates the user's rating",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-editUser <member> [new rating]`')
    await ctx.send(embed=embed)


@help.command()
async def removeUser(ctx):
    embed = discord.Embed(title="removeUser", description="Removes the user from the database",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-removeUser <member>`')
    await ctx.send(embed=embed)


@help.command()
async def resetStats(ctx):
    embed = discord.Embed(title="resetStats", description="Reset the stats from the user",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-resetStats <member>`')
    await ctx.send(embed=embed)


@help.command()
async def searchUser(ctx):
    embed = discord.Embed(title="searchUser", description="Search information about a user",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-searchUser <member>`')
    await ctx.send(embed=embed)


@help.command()
async def listUsers(ctx):
    embed = discord.Embed(title="listUsers", description="Get a list with all the users and their rating",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-listPlayers`')
    await ctx.send(embed=embed)


@help.command()
async def selectUser(ctx):
    embed = discord.Embed(title="selectUser", description="Selects a user from the database for the next custom game",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-selectUser <member>`')
    await ctx.send(embed=embed)


@help.command()
async def removeSelectedUser(ctx):
    embed = discord.Embed(title="removeSelectedUser", description="Removes a user from the selection for the next "
                                                                  "custom game", color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-removeSelectedUser <member>`')
    await ctx.send(embed=embed)


@help.command()
async def chooseTeams(ctx):
    embed = discord.Embed(title="chooseTeams", description="Select custom teams for the next custom game",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`[WORK IN PROGRESS]`')
    await ctx.send(embed=embed)


@help.command()
async def createTeams(ctx):
    embed = discord.Embed(title="createTeams", description="Creates 2 balanced teams for the 10 selected players",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-createTeams`')
    await ctx.send(embed=embed)


@help.command()
async def startGame(ctx):
    embed = discord.Embed(title="startGame", description="Moves all players to their respective channel after"
                                                         " teams being created", color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-startGame`')
    await ctx.send(embed=embed)


@help.command()
async def clearRoles(ctx):
    embed = discord.Embed(title="clearRoles", description="Clears the team roles from all the players",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-clearRoles`')
    await ctx.send(embed=embed)


@help.command()
async def restartGame(ctx):
    embed = discord.Embed(title="restartGame", description="Restarts game with the same teams",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-restartGame`')
    await ctx.send(embed=embed)


@help.command()
async def endGame(ctx):
    embed = discord.Embed(title="endGame", description="Clears everyone's team roles and deletes teams",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-endGame`')
    await ctx.send(embed=embed)


@help.command()
async def moveBack(ctx):
    embed = discord.Embed(title="moveBack", description="Moves everyone back to a common voice channel",
                          color=discord.Colour.random())
    embed.add_field(name="**Syntax**", value='`-moveBack`')
    await ctx.send(embed=embed)


@client.command(aliases=["gtt", "GTT"])
async def getTimetable(ctx, person="Paulo", weekDay=None):
    my_date = date.today()
    if weekDay is None:
        weekDay = calendar.day_name[my_date.weekday()]
    for i in range(len(private["timetable"][person])):
        if private["timetable"][person][i]["day"].lower() == weekDay.lower():
            for k in range(len(private["timetable"][person][i]["lessons"])):
                embed = discord.Embed(title=private["timetable"][person][i]["lessons"][k]["courseName"] + " [" +
                                      private["timetable"][person][i]["lessons"][k]["type"] + "]",
                                      description=" ",
                                      color=discord.Colour.random())
                embed.add_field(name="StartTime:",
                                value=private["timetable"][person][i]["lessons"][k]["startTime"])
                embed.add_field(name="EndTime:",
                                value=private["timetable"][person][i]["lessons"][k]["endTime"])
                embed.add_field(name="Teacher:",
                                value=private["timetable"][person][i]["lessons"][k]["teacher"])
                embed.add_field(name="Email:",
                                value=private["timetable"][person][i]["lessons"][k]["email"])
                if "link" in private["timetable"][person][i]["lessons"][k]:
                    embed.add_field(name="Link",
                                    value=private["timetable"][person][i]["lessons"][k]["link"], inline=False)

                await ctx.send(embed=embed)


@client.command()
async def nextHoliday(ctx):
    my_date = date.today()
    month = calendar.month_name[my_date.month]
    today = datetime.now().date()

    for i in range(len(private["holidays"])):
        if month in private["holidays"][i]:
            for k in range(len(private["holidays"][i][month])):
                thisDateArr = private["holidays"][i][month][k]["day"].split("-")
                thisDate = datetime(int(thisDateArr[0]), int(thisDateArr[1]), int(thisDateArr[2])).date()
                if thisDate > today:
                    event = private["holidays"][i][month][k]["event"]
                    longDate = date(day=int(thisDateArr[2]), month=int(thisDateArr[1]),
                                    year=int(thisDateArr[0])).strftime('%A %d %B %Y')
                    await ctx.send("`{}`'s event is:\n**{}**".format(longDate, event))
                    break
                if k == len(private["holidays"][i][month]):
                    month = calendar.month_name[my_date.month + 1]


@client.command()
async def holidayMonth(ctx, month=None):
    my_date = date.today()
    holidayExist = False
    if month is None:
        month = calendar.month_name[my_date.month]
    for i in range(len(private["holidays"])):
        if month in private["holidays"][i]:
            if len(private["holidays"][i][month]) == 0:
                await ctx.send("I have no knowledge of a holiday this month")
            else:
                embed = discord.Embed(title=" ",
                                      description=" ",
                                      color=discord.Colour.random())
                for k in range(len(private["holidays"][i][month])):
                    holidayExist = True
                    thisDateArr = private["holidays"][i][month][k]["day"].split("-")
                    longDate = date(day=int(thisDateArr[2]), month=int(thisDateArr[1]),
                                    year=int(thisDateArr[0])).strftime('%A %d %B %Y')
                    embed.add_field(name="Date: `{}`".format(longDate),
                                    value="Event: **{}**\n".format(private["holidays"][i][month][k]["event"]),
                                    inline=False)

    if holidayExist:
        await ctx.send(embed=embed)


"################################################ vv CHESS vv #######################################################"""


@client.command()
async def addPlayer(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != QFCHESS:
        return
    exists = False
    for user in private["chessInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
    if not exists:
        private["chessInfo"]["players"].append({"id": str(member), "wins": "0", "ties": "0", "losses": "0"})
        await ctx.send('Player [' + str(len(private["chessInfo"]["players"])) + ']: ' +
                       str(private["chessInfo"]["players"][len(private["chessInfo"]["players"]) - 1]["id"]))

        saveToFile()
    else:
        await ctx.send('This players is already in the system.')


@client.command()
@commands.has_any_role(private["private"]["roles"][3])
async def editPlayer(ctx, member: discord.Member, stat, number):
    if str(ctx.message.guild.id) != QFCHESS:
        return
    exists = False
    for user in private["chessInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
    stats = ["wins", "losses", "ties", "win", "lose", "tie", "lost", "draw"]
    if exists:
        valid = False
        for i in range(len(stats)):
            if str(stat) == str(stats[i]):
                valid = True
        if not valid:
            await ctx.send('Unknown Stat')
        else:
            if stat == "win":
                stat = "wins"
            if stat == "lose" or stat == "lost":
                stat = "losses"
            if stat == "tie" or stat == "draw":
                stat = "ties"

            tempNum = 0
            theMember = None
            for existingUsers in private["chessInfo"]["players"]:
                if existingUsers["id"] == str(member):
                    theMember = existingUsers
                    break
                tempNum += 1

            lastStat = theMember[stat]
            theMember[stat] = number
            await ctx.send(str(member) + "'s {} was [".format(stat) + str(lastStat) + "] and now it's [" + str(number)
                           + "]")
            private["chessInfo"]["players"][tempNum] = theMember
            saveToFile()
    else:
        await ctx.send(str(member) + " is not in the system")


@client.command()
@commands.has_any_role(private["private"]["roles"][3])
async def removePlayer(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != QFCHESS:
        return
    exists = False
    for user in private["chessInfo"]["players"]:
        if str(member) in user["id"]:
            exists = True
            tempNum = 0
            for existingUsers in private["chessInfo"]["players"]:
                if existingUsers["id"] == str(member):
                    del private["chessInfo"]["players"][tempNum]
                tempNum += 1
            await ctx.send(str(member) + " has been deleted")
            saveToFile()
    if not exists:
        await ctx.send(str(member) + " is not in the system")


@client.command()
async def listPlayers(ctx, page=None):
    if str(ctx.message.guild.id) != QFCHESS:
        return
    if not page:
        page = 1

    totalPages = int((len(private["chessInfo"]["players"])) / 10)
    if len(private["chessInfo"]["players"]) % 10 != 0:
        totalPages += 1
    if int(page) > totalPages:
        await ctx.send("There are not that many pages!")
    else:
        if len(private["chessInfo"]["players"]) <= 10:
            page = 1
        amount = 0
        embed = discord.Embed(
            title='Players [Page: ' + str(page) + ' / ' + str(totalPages) + ']',
            description='',
            color=discord.Colour.dark_green()
        )
        for i in range(len(private["chessInfo"]["players"])):
            amount += 1

            if (int(page) * 10 - 10) < amount < ((int(page) * 10) + 1):
                embed.add_field(name='Player [' + str(i + 1) + ']', value='`' + str(private["chessInfo"]["players"][i]["id"]) + '`'
                                , inline=False)
        await ctx.send(embed=embed)


@client.command()
async def searchPlayer(ctx, member: discord.Member):
    if str(ctx.message.guild.id) != QFCHESS:
        return
    holdInt = -1
    for i in range(len(private["chessInfo"]["players"])):
        mentionableName = await memberConverter.convert(ctx, private["chessInfo"]["players"][i]["id"])

        if member == mentionableName:
            holdInt = i
            break

    if holdInt == -1:
        await ctx.send("That user does not exist!")
    else:
        wins = private["chessInfo"]["players"][holdInt]["wWins"]
        ties = private["chessInfo"]["players"][holdInt]["ties"]
        losses = private["chessInfo"]["players"][holdInt]["losses"]
        totalGames = int(wins) + int(ties) + int(losses)
        embed = discord.Embed(
            title=str(private["chessInfo"]["players"][holdInt]["id"]),
            description='__**Stats:**__',
            color=discord.Colour.random()
        )
        if totalGames != 0:
            embed.add_field(name="Wins: ***{}***".format(int(wins)),
                            value="`{}% Won`".format(format((int(wins) / int(totalGames)) * 100, ".2f")),
                            inline=False)
            embed.add_field(name="Ties: ***{}***".format(int(ties)),
                            value="`{}% Tied`".format(format((int(ties) / int(totalGames)) * 100, ".2f")),
                            inline=False)
            embed.add_field(name="Losses: ***{}***".format(int(losses)),
                            value="`{}% Lost`".format(format((int(losses) / int(totalGames)) * 100, ".2f")),
                            inline=False)

        else:
            embed.add_field(name="Wins: ***0***",
                            value="`0% Won`",
                            inline=False)
            embed.add_field(name="Ties: ***0***",
                            value="`0% Tied`",
                            inline=False)
            embed.add_field(name="Losses: ***0***",
                            value="`0% Lost`",
                            inline=False)

        await ctx.send(embed=embed)


"################################################ ^^ CHESS ^^ #######################################################"""


"################################################ vv TASKS vv #######################################################"""


@tasks.loop(seconds=5)
async def crypto():
    currentPrice11 = -1
    currentPrice22 = -1
    currentPrice33 = -1
    await client.wait_until_ready()
    channel1 = client.get_channel(818807938453209098)
    message1 = await channel1.fetch_message(818808014266040340)
    message2 = await channel1.fetch_message(818808061723541514)
    message3 = await channel1.fetch_message(818808083865141298)
    prices = clientB.get_symbol_ticker()
    coin1 = "DOGEEUR"
    coin11 = "DOGEUSDT"
    coin2 = "BTCEUR"
    coin22 = "BTCUSDT"
    coin3 = "ETHEUR"
    coin33 = "ETHUSDT"
    for i in prices:
        if i['symbol'] == coin11:
            currentPrice11 = i['price']
        if i['symbol'] == coin22:
            currentPrice22 = i['price']
        if i['symbol'] == coin33:
            currentPrice33 = i['price']
    for i in prices:
        if i['symbol'] == coin1:
            try:
                coinInfo1 = clientB.get_symbol_info(coin1)
                coinInfo11 = clientB.get_symbol_info(coin11)
                change = getChange(coin1)
                if change < 0:
                    color = discord.Color.red()
                elif change > 0:
                    color = discord.Color.green()
                else:
                    color = discord.Color.orange()
                currentPrice1 = i['price']
                embed = discord.Embed(
                    title=str(coinInfo1['baseAsset']),
                    color=color
                )
                embed.add_field(name='1 ' + str(coinInfo1['baseAsset'] + " = "),
                                value=currentPrice1 + " " + "**" + coinInfo1['quoteAsset'] + "**", inline=False)
                embed.add_field(name='1 ' + str(coinInfo11['baseAsset'] + " = "),
                                value=str(currentPrice11) + " " + "**" + coinInfo11['quoteAsset'] + "**", inline=False)
                embed.add_field(name='Change:',
                                value=str(format(change, ".3f") + "%"), inline=False)
                await message1.edit(embed=embed)
            except Exception:
                pass

        if i['symbol'] == coin2:
            try:
                coinInfo2 = clientB.get_symbol_info(coin2)
                coinInfo22 = clientB.get_symbol_info(coin22)
                change = getChange(coin2)
                if change < 0:
                    color = discord.Color.red()
                elif change > 0:
                    color = discord.Color.green()
                else:
                    color = discord.Color.orange()
                currentPrice2 = i['price']
                embed = discord.Embed(
                    title=str(coinInfo2['baseAsset']),
                    color=color
                )
                embed.add_field(name='1 ' + str(coinInfo2['baseAsset'] + " = "),
                                value=currentPrice2 + " " + "**" + coinInfo2['quoteAsset'] + "**", inline=False)
                embed.add_field(name='1 ' + str(coinInfo22['baseAsset'] + " = "),
                                value=str(currentPrice22) + " " + "**" + coinInfo22['quoteAsset'] + "**", inline=False)
                embed.add_field(name='Change:',
                                value=str(format(change, ".3f") + "%"), inline=False)
                await message2.edit(embed=embed)
            except Exception:
                pass

        if i['symbol'] == coin3:
            try:
                coinInfo3 = clientB.get_symbol_info(coin3)
                coinInfo33 = clientB.get_symbol_info(coin33)
                change = getChange(coin3)
                if change < 0:
                    color = discord.Color.red()
                elif change > 0:
                    color = discord.Color.green()
                else:
                    color = discord.Color.orange()
                currentPrice3 = i['price']
                embed = discord.Embed(
                    title=str(coinInfo3['baseAsset']),
                    color=color
                )
                embed.add_field(name='1 ' + str(coinInfo3['baseAsset'] + " = "),
                                value=currentPrice3 + " " + "**" + coinInfo3['quoteAsset'] + "**", inline=False)
                embed.add_field(name='1 ' + str(coinInfo33['baseAsset'] + " = "),
                                value=str(currentPrice33) + " " + "**" + coinInfo33['quoteAsset'] + "**", inline=False)
                embed.add_field(name='Change:',
                                value=str(format(change, ".3f") + "%"), inline=False)
                await message3.edit(embed=embed)
            except Exception:
                pass


@tasks.loop(seconds=5)
async def timer():
    await client.wait_until_ready()
    msg_sent = False
    my_date = date.today()
    time = datetime.now
    hourMin = str(time().hour) + ":" + str(time().minute)
    for users in range(len(private["timetable"])):
        name = "Paulo"
        user = "<@!323213377432453140>"
        if users == 0:
            name = "Paulo"
            user = "<@!323213377432453140>"
        elif users == 1:
            name = "Marta"
            user = "<@!689581895159251011>"
        elif users == 2:
            name = "Telmo"
            user = "<@!323213166790180864>"
        elif users == 3:
            name = "2DC"
            user = "<@&820798865195532289>"
        for i in range(len(private["timetable"][name])):
            if private["timetable"][name][i]["day"] == calendar.day_name[my_date.weekday()]:
                for k in range(len(private["timetable"][name][i]["lessons"])):
                    testing = private["timetable"][name][i]["lessons"][k]["startTime"].split(":")
                    if int(testing[1]) < 5:
                        testing[0] = int(testing[0]) - 1
                        remainder = -(int(testing[1]) - 5)
                        testing[1] = 60 - remainder
                        fiveMinBefore = str(testing[0]) + ":" + str(testing[1])
                    else:
                        fiveMinBefore = str(testing[0]) + ":" + str(int(testing[1]) - 5)
                    if hourMin == fiveMinBefore:
                        channel = client.get_channel(553957090679586838)
                        if users == 3:
                             channel = client.get_channel(701806332658843689)
                        embed = discord.Embed(title=private["timetable"][name][i]["lessons"][k]["courseName"] + " [" +
                                              private["timetable"][name][i]["lessons"][k]["type"] + "]",
                                              description=" You have class in 5 minutes!!!",
                                              color=discord.Colour.random())
                        embed.add_field(name="StartTime:",
                                        value=private["timetable"][name][i]["lessons"][k]["startTime"])
                        embed.add_field(name="EndTime:",
                                        value=private["timetable"][name][i]["lessons"][k]["endTime"])
                        embed.add_field(name="Teacher:",
                                        value=private["timetable"][name][i]["lessons"][k]["teacher"])
                        embed.add_field(name="Email:",
                                        value=private["timetable"][name][i]["lessons"][k]["email"])
                        if "link" in private["timetable"][name][i]["lessons"][k]:
                            embed.add_field(name="Link",
                                            value=private["timetable"][name][i]["lessons"][k]["link"], inline=False)
                        await channel.send(user)
                        await channel.send(embed=embed)

                        msg_sent = True
    if msg_sent:
        await asyncio.sleep(60)


@tasks.loop(seconds=5)
async def binanceBot():
    pass


@tasks.loop(seconds=5)
async def getHolidays():
    my_date = date.today()
    month = calendar.month_name[my_date.month]
    today = datetime.now().date()
    channel = client.get_channel(547826904674205703)
    msg_sent = False
    for i in range(len(private["holidays"])):
        if month in private["holidays"][i]:
            for k in range(len(private["holidays"][i][month])):
                thisDateArr = private["holidays"][i][month][k]["day"].split("-")
                thisDate = datetime(int(thisDateArr[0]), int(thisDateArr[1]), int(thisDateArr[2])).date()
                if thisDate == today:
                    event = private["holidays"][i][month][k]["event"]
                    await channel.send("@everyone\nToday's event is:\n**{}**\n\nHave a nice day!!".format(event))
                    msg_sent = True
                    break
    if msg_sent:
        await asyncio.sleep(86400)

"################################################ ^^ TASKS ^^ #######################################################"""


client.run(private["private"]["discordClient"])
