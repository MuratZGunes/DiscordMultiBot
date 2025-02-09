import nextcord
from nextcord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime, timedelta
import pytz
import os
import asyncio
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
CONFIG = {
    "DATA_FOLDER": "data/game_deals",
    "LAST_CHECK_FILE": "last_check.json",
    "MESSAGE_IDS_FILE": "message_ids.json",
    "CURRENCY_API_URL": f"https://v6.exchangerate-api.com/v6/{os.getenv('EXCHANGE_RATE_API_KEY')}/pair/USD/TRY",
    "EPIC_GAMES_API": "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions",
    "STEAM_API": "https://store.steampowered.com/api/featuredcategories",
    "TIMEZONE": "Europe/Istanbul",
    "REFRESH_INTERVAL_HOURS": 24,
    "MAX_STEAM_DEALS": 5,
    "EMBED_COLORS": {
        "INFO": 0x2F3136,
        "EPIC": 0x0CB5ED,
        "STEAM": 0xFF0000,
        "ERROR": 0xFF0000
    }
}

class GameDeals(commands.Cog):
    """
    A Discord bot cog that tracks and shares game deals from Epic Games and Steam.
    Features:
    - Tracks free games on Epic Games Store
    - Lists discounted games on Steam
    - Maintains current USD/TRY exchange rate
    - Auto-updates every 24 hours
    - Posts updates in the 'game-deals' channel
    - Provides manual command for instant deal checks
    """
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tz = pytz.timezone(CONFIG["TIMEZONE"])
        self.usd_to_try: Optional[float] = None
        self.last_check: Optional[datetime] = None
        
        # File paths
        os.makedirs(CONFIG["DATA_FOLDER"], exist_ok=True)
        self.last_check_path = os.path.join(CONFIG["DATA_FOLDER"], CONFIG["LAST_CHECK_FILE"])
        self.message_ids_path = os.path.join(CONFIG["DATA_FOLDER"], CONFIG["MESSAGE_IDS_FILE"])
        
        # Load data
        self.message_ids: Dict[str, List[int]] = self._load_data(self.message_ids_path, default={"channel_messages": {}})
        self._load_last_check()
        
        # Start tasks
        self.update_exchange_rate.start()
        
        # Calculate time since last check and schedule next check
        if self.last_check:
            now = datetime.now(self.tz)
            time_since_last_check = now - self.last_check
            hours_since_last_check = time_since_last_check.total_seconds() / 3600
            
            if hours_since_last_check < CONFIG["REFRESH_INTERVAL_HOURS"]:
                self.check_game_deals.change_interval(hours=CONFIG["REFRESH_INTERVAL_HOURS"] - hours_since_last_check)
            else:
                self.check_game_deals.change_interval(hours=CONFIG["REFRESH_INTERVAL_HOURS"])
        else:
            self.check_game_deals.change_interval(hours=CONFIG["REFRESH_INTERVAL_HOURS"])
        
        self.check_game_deals.start()

    def _load_data(self, path: str, default: dict) -> dict:
        """Load JSON data from file or return default if file doesn't exist"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _save_data(self, data: dict, path: str) -> None:
        """Save data to JSON file"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_last_check(self) -> None:
        """Load the timestamp of the last deals check"""
        data = self._load_data(self.last_check_path, default={"last_check": None})
        if data["last_check"]:
            naive_dt = datetime.strptime(data["last_check"], '%Y-%m-%d %H:%M')
            self.last_check = self.tz.localize(naive_dt)

    def _should_check(self) -> bool:
        """Determine if it's time to check for new deals"""
        if not self.last_check:
            return True
        now = datetime.now(self.tz)
        time_diff = now - self.last_check
        return time_diff.total_seconds() >= CONFIG["REFRESH_INTERVAL_HOURS"] * 3600

    async def _delete_old_messages(self, channel: nextcord.TextChannel) -> None:
        """Delete previous deal messages from the channel"""
        if str(channel.id) not in self.message_ids["channel_messages"]:
            return
            
        try:
            for msg_id in self.message_ids["channel_messages"][str(channel.id)]:
                try:
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                except nextcord.NotFound:
                    continue
        except nextcord.HTTPException as e:
            print(f"Error deleting messages: {e}")
        finally:
            self.message_ids["channel_messages"][str(channel.id)] = []
            self._save_data(self.message_ids, self.message_ids_path)

    def _create_loading_embed(self) -> nextcord.Embed:
        """Create an embed for the loading message"""
        embed = nextcord.Embed(
            title="🎮 Loading Game Deals",
            description="Please wait...",
            color=CONFIG["EMBED_COLORS"]["INFO"]
        )
        embed.set_thumbnail(url="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif")
        return embed

    async def _fetch_epic_games(self, session: aiohttp.ClientSession) -> List[nextcord.Embed]:
        """Fetch and format free games from Epic Games Store"""
        try:
            async with session.get(CONFIG["EPIC_GAMES_API"]) as resp:
                if resp.status != 200:
                    return []
                
                data = await resp.json()
                embeds = []
                
                for game in data['data']['Catalog']['searchStore']['elements']:
                    promotions = game.get('promotions')
                    if not promotions:
                        continue
                        
                    offers = promotions.get('promotionalOffers') or promotions.get('upcomingPromotionalOffers')
                    if not offers:
                        continue
                        
                    title = game.get('title', 'Unknown Game')
                    
                    # Create Epic Games URL
                    product_slug = game.get('productSlug', '')
                    offer_mappings = game.get('offerMappings', [])
                    page_slug = game.get('urlSlug', '')
                    
                    if product_slug:
                        url = f"https://store.epicgames.com/en-US/p/{product_slug}"
                    elif offer_mappings and offer_mappings[0].get('pageSlug'):
                        url = f"https://store.epicgames.com/en-US/p/{offer_mappings[0]['pageSlug']}"
                    elif page_slug:
                        url = f"https://store.epicgames.com/en-US/p/{page_slug}"
                    else:
                        url = f"https://store.epicgames.com/en-US/p/{game.get('id', '')}"
                    
                    image_url = next((img['url'] for img in game.get('keyImages', []) if img.get('type') == 'Thumbnail'), None)
                    
                    embed = nextcord.Embed(
                        title=f"🎁 EPIC - {title}",
                        description=f"**GET IT FREE**\n[View on Epic Games]({url})",
                        color=CONFIG["EMBED_COLORS"]["EPIC"]
                    )
                    if image_url:
                        embed.set_thumbnail(url=image_url)
                    embeds.append(embed)
                
                return embeds
        except Exception as e:
            print(f"Epic Games error: {e}")
            return []

    async def _fetch_steam_deals(self, session: aiohttp.ClientSession) -> List[nextcord.Embed]:
        """Fetch and format deals from Steam"""
        try:
            async with session.get(f"{CONFIG['STEAM_API']}?cc=us") as resp:
                if resp.status != 200:
                    return []
                
                data = await resp.json()
                embeds = []
                
                for item in data.get('specials', {}).get('items', [])[:CONFIG["MAX_STEAM_DEALS"]]:
                    title = item.get('name', 'Unknown Game')
                    discount = item.get('discount_percent', 0)
                    final_price = item.get('final_price', 0) / 100
                    original_price = item.get('original_price', 0) / 100
                    header_image = item.get('header_image', '')
                    app_id = item.get('id', '')
                    
                    # Calculate price in TRY
                    try_final_price = final_price * self.usd_to_try if self.usd_to_try else None
                    
                    description = (
                        f"**Discount:** {discount}%\n"
                        f"~~${original_price:.2f}~~ **${final_price:.2f}**"
                    )
                    
                    if try_final_price is not None:
                        description += f" = **{try_final_price:.2f}₺**\n"
                    else:
                        description += "\n"
                    
                    description += f"[View on Steam](https://store.steampowered.com/app/{app_id})"
                    
                    embed = nextcord.Embed(
                        title=f"🔥 STEAM - {title}",
                        description=description,
                        color=CONFIG["EMBED_COLORS"]["STEAM"]
                    )
                    if header_image:
                        embed.set_thumbnail(url=header_image)
                    embeds.append(embed)
                
                return embeds
        except Exception as e:
            print(f"Steam error: {e}")
            return []

    async def _send_deals(self, channel: nextcord.TextChannel) -> None:
        """Send game deals to the specified channel"""
        await self._delete_old_messages(channel)
        
        loading_msg = await channel.send(embed=self._create_loading_embed())
        self.message_ids["channel_messages"].setdefault(str(channel.id), []).append(loading_msg.id)
        
        async with aiohttp.ClientSession() as session:
            epic_embeds, steam_embeds = await asyncio.gather(
                self._fetch_epic_games(session),
                self._fetch_steam_deals(session)
            )
            
            main_embed = nextcord.Embed(
                title="🎮 Current Game Deals",
                color=CONFIG["EMBED_COLORS"]["INFO"]
            )
            main_embed.description = (
                f"**💰 USD/TRY:** `{self.usd_to_try:.2f}₺`\n" if self.usd_to_try else "**💰 USD/TRY:** `Updating...`\n"
            ) + (
                f"**🔄 Updates:** Daily\n"
                f"**⏰ Last Check:** {datetime.now(self.tz).strftime('%H:%M  %d.%m.%Y')}"
            )
            main_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/613455122261082116/1336927954114187374/DALLE_2025-02-06_08.07.12_-_An_image_showcasing_discounts_on_Steam_and_Epic_Games_with_sale_banners_on_both_platforms._The_image_features_colorful_eye-catching_promotional_elem.webp?ex=67a596af&is=67a4452f&hm=28e427f60710cf7748cd2df9aeb42e5c530515e43b59f5e6bc09ccff8b52b0e5&")
            
            await loading_msg.edit(embed=main_embed)
            
            for embed in epic_embeds + steam_embeds:
                msg = await channel.send(embed=embed)
                self.message_ids["channel_messages"][str(channel.id)].append(msg.id)
            
            self._save_data(self.message_ids, self.message_ids_path)

    async def _send_deals_command(self, channel: nextcord.TextChannel) -> None:
        """Send game deals in response to a command without deleting previous messages"""
        async with aiohttp.ClientSession() as session:
            epic_embeds, steam_embeds = await asyncio.gather(
                self._fetch_epic_games(session),
                self._fetch_steam_deals(session)
            )
            
            main_embed = nextcord.Embed(
                title="🎮 Current Game Deals",
                color=CONFIG["EMBED_COLORS"]["INFO"]
            )
            main_embed.description = (
                f"**💰 USD/TRY:** `{self.usd_to_try:.2f}₺`\n" if self.usd_to_try else "**💰 USD/TRY:** `Updating...`\n"
            ) + (
                f"**🔄 Updates:** Daily\n"
                f"**⏰ Last Check:** {datetime.now(self.tz).strftime('%H:%M  %d.%m.%Y')}"
            )
            main_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/613455122261082116/1336927954114187374/DALLE_2025-02-06_08.07.12_-_An_image_showcasing_discounts_on_Steam_and_Epic_Games_with_sale_banners_on_both_platforms._The_image_features_colorful_eye-catching_promotional_elem.webp?ex=67a596af&is=67a4452f&hm=28e427f60710cf7748cd2df9aeb42e5c530515e43b59f5e6bc09ccff8b52b0e5&")
            
            await channel.send(embed=main_embed)
            for embed in epic_embeds + steam_embeds:
                await channel.send(embed=embed)

    @tasks.loop(hours=CONFIG["REFRESH_INTERVAL_HOURS"])
    async def check_game_deals(self):
        """Periodic task to check and post game deals"""
        try:
            if self._should_check():
                print(f"[{datetime.now(self.tz).strftime('%H:%M %d.%m.%Y')}] Checking game deals...")
                for guild in self.bot.guilds:
                    channel = nextcord.utils.get(guild.text_channels, name="game-deals")
                    if channel:
                        try:
                            await self._send_deals(channel)
                            print(f"[{guild.name}] Game deals updated!")
                        except Exception as e:
                            print(f"[{guild.name}] Error: {e}")
                
                self.last_check = datetime.now(self.tz)
                self._save_data({"last_check": self.last_check.strftime('%Y-%m-%d %H:%M')}, self.last_check_path)
        except Exception as e:
            print(f"Error checking game deals: {e}")

    @tasks.loop(hours=24)
    async def update_exchange_rate(self):
        """Update USD to TRY exchange rate"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(CONFIG["CURRENCY_API_URL"]) as resp:
                    data = await resp.json()
                    if data.get("result") == "success":
                        self.usd_to_try = data["conversion_rate"]
        except Exception as e:
            print(f"Exchange rate update error: {e}")

    @check_game_deals.before_loop
    @update_exchange_rate.before_loop
    async def wait_for_ready(self):
        """Wait for the bot to be ready before starting tasks"""
        await self.bot.wait_until_ready()

    @commands.command(name="gamedeals", aliases=["deals"])
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def game_deals(self, ctx: commands.Context):
        """Show current game deals"""
        await self._send_deals_command(ctx.channel)

    def cog_unload(self):
        """Clean up tasks when cog is unloaded"""
        self.check_game_deals.cancel()
        self.update_exchange_rate.cancel()

def setup(bot: commands.Bot):
    """Add the GameDeals cog to the bot"""
    bot.add_cog(GameDeals(bot))