import nextcord
from nextcord.ext import commands
import aiohttp
import json
from datetime import datetime
import pytz
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

load_dotenv()

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.exchange_api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        self.exchange_base_url = "https://v6.exchangerate-api.com/v6/"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.collectapi_key = os.getenv("COLLECT_API_KEY")
        self.goldapi_key = os.getenv("GOLD_API_KEY")
        
        # Currency information with API type and emoji
        self.currency_commands = {
            'eur': ('EUR', '💶', 0x3498db, 'fiat'),
            'euro': ('EUR', '💶', 0x3498db, 'fiat'),
            'gbp': ('GBP', '💷', 0x9b59b6, 'fiat'),
            'pound': ('GBP', '💷', 0x9b59b6, 'fiat'),
            'jpy': ('JPY', '💴', 0xe74c3c, 'fiat'),
            'yen': ('JPY', '💴', 0xe74c3c, 'fiat'),
            'try': ('TRY', '₺', 0x2ecc71, 'fiat'),
            'lira': ('TRY', '₺', 0x2ecc71, 'fiat'),
            'gold': ('gold', '🏆', 0xf1c40f, 'gold'),
            'btc': ('bitcoin', '₿', 0xf39c12, 'crypto'),
            'bitcoin': ('bitcoin', '₿', 0xf39c12, 'crypto'),
            'eth': ('ethereum', '⟠', 0x95a5a6, 'crypto'),
            'ethereum': ('ethereum', '⟠', 0x95a5a6, 'crypto'),
            'xrp': ('ripple', '✧', 0x34495e, 'crypto'),
            'ripple': ('ripple', '✧', 0x34495e, 'crypto'),
            'usdt': ('tether', '₮', 0x16a085, 'crypto'),
            'tether': ('tether', '₮', 0x16a085, 'crypto')
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.content.startswith(('!', '/', '?', '.')):
            return

        content = message.content.lower().strip()
        
        if content in self.currency_commands:
            currency_code, emoji, color, api_type = self.currency_commands[content]
            if api_type == 'fiat':
                await self.get_fiat_rate(message, currency_code, emoji, color)
            elif api_type == 'gold':
                await self.get_gold_rate(message, emoji, color)
            else:
                await self.get_crypto_rate(message, currency_code, emoji, color)

    async def get_fiat_rate(self, message, currency_code, emoji, color):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.exchange_base_url}{self.exchange_api_key}/pair/{currency_code}/USD"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data["conversion_rate"]
                        embed = nextcord.Embed(
                            title=f"{emoji} {currency_code} Exchange Rate",
                            description=f"1 {currency_code} = ${rate:.4f}",
                            color=color
                        )
                        embed.set_footer(text=f"Last update: {self.format_date(data['time_last_update_utc'])}")
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send("Error fetching exchange rate information.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {str(e)}")

    async def get_crypto_rate(self, message, currency_id, emoji, color):
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.coingecko_base_url}/simple/price?ids={currency_id}&vs_currencies=usd&include_last_updated_at=true"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate = data[currency_id]['usd']
                        last_updated = datetime.fromtimestamp(data[currency_id]['last_updated_at'], tz=pytz.utc)

                        currency_name = currency_id.upper()
                        
                        embed = nextcord.Embed(
                            title=f"{emoji} {currency_name} Exchange Rate",
                            description=f"1 {currency_name} = ${rate:,.2f}",
                            color=color
                        )
                        embed.set_footer(text=f"Last update: {last_updated.strftime('%d %B %Y, %H:%M')} UTC")
                        await message.channel.send(embed=embed)
                    else:
                        await message.channel.send("Error fetching exchange rate information.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {str(e)}")

    async def get_gold_rate(self, message, emoji, color):
        async with aiohttp.ClientSession() as session:
            try:
                # Get XAU/USD data from GoldAPI
                gold_url = "https://www.goldapi.io/api/XAU/USD"
                headers = {
                    "x-access-token": self.goldapi_key,
                    "Content-Type": "application/json"
                }
                async with session.get(gold_url, headers=headers) as gold_response:
                    if gold_response.status == 200:
                        gold_data = await gold_response.json()
                        try:
                            price_per_ounce = float(gold_data.get("price"))
                            price_per_gram = price_per_ounce / 31.1035  # convert to gram
                            timestamp = gold_data.get("timestamp")
                            
                            if timestamp:
                                last_update_time = datetime.fromtimestamp(timestamp, tz=pytz.utc)
                            else:
                                last_update_time = datetime.now(tz=pytz.utc)

                            embed = nextcord.Embed(
                                title=f"{emoji} Gold Price",
                                description=f"Per ounce: ${price_per_ounce:,.2f}\nPer gram: ${price_per_gram:,.2f}",
                                color=color
                            )
                            embed.set_footer(text=f"Last update: {last_update_time.strftime('%d %B %Y, %H:%M')} UTC")
                            await message.channel.send(embed=embed)
                        except (KeyError, ValueError, TypeError):
                            await message.channel.send("Error processing gold price data.")
                    else:
                        await message.channel.send("Error fetching gold price information.")
            except Exception as e:
                await message.channel.send(f"An error occurred: {str(e)}")

    def format_date(self, utc_date_str):
        try:
            utc_date = datetime.strptime(utc_date_str, '%a, %d %b %Y %H:%M:%S +0000')
            utc_date = pytz.utc.localize(utc_date)
            month_names = {
                1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
            }
            return f"{utc_date.day} {month_names[utc_date.month]} {utc_date.year}, {utc_date.hour:02d}:{utc_date.minute:02d} UTC"
        except Exception as e:
            return "Date information unavailable"

def setup(bot):
    bot.add_cog(Currency(bot)) 