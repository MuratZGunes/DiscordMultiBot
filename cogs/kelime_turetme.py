import nextcord
from nextcord.ext import commands
import json
import os
import random
import aiohttp
import asyncio
from datetime import datetime

class WordGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
        self.used_words = {}
        self.last_word = {}  # Stores the last confirmed word for each server
        self.word_channel_id = {}
        self.starting_words = ["merhaba", "arkadaş", "sevgi", "dostluk", "mutluluk"]
        self.session = None
        self.load_settings()

    def load_settings(self):
        """Load server settings and game state"""
        if not os.path.exists('data/kelimeler'):
            os.makedirs('data/kelimeler', exist_ok=True)
        
        self.settings_file = 'data/kelimeler/server_settings.json'
        if not os.path.exists(self.settings_file):
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                for guild_id, data in settings.items():
                    guild_id = int(guild_id)
                    self.word_channel_id[guild_id] = data.get('channel_id')
                    self.used_words[guild_id] = set(data.get('used_words', []))
                    self.last_word[guild_id] = data.get('last_word')
                    if data.get('game_active', False):
                        self.active_games[guild_id] = True
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self, guild_id):
        """Save server settings and game state"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            guild_id_str = str(guild_id)
            settings[guild_id_str] = {
                'channel_id': self.word_channel_id.get(guild_id),
                'used_words': list(self.used_words.get(guild_id, set())),
                'game_active': guild_id in self.active_games,
                'last_word': self.last_word.get(guild_id)
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")

    async def send_error_embed(self, message, title, description):
        """Send error message as a personalized embed"""
        embed = nextcord.Embed(
            title=title,
            description=description,
            color=0xff0000
        )
        await message.channel.send(embed=embed, reference=message, mention_author=True, delete_after=5)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """When a new channel is created, if it's a word-türetme channel, automatically set it up"""
        if isinstance(channel, nextcord.TextChannel) and "kelime-türetme" in channel.name.lower():
            guild_id = channel.guild.id
            self.word_channel_id[guild_id] = channel.id
            self.save_settings(guild_id)
            
            embed = nextcord.Embed(
                title="🎮 Kelime Türetme Kanalı Tespit Edildi!",
                description=f"Bu kanal otomatik olarak kelime türetme oyun kanalı olarak ayarlandı!\n"
                           f"Oyunu başlatmak için `!kelime` yazabilirsiniz.",
                color=0x00ff00
            )
            await channel.send(embed=embed)

    @commands.command(name="kelime")
    async def kelime_help(self, ctx, arg=None):
        """Kelime oyunu komutları"""
        if arg and arg.lower() == "başlat":
            # Oyunu başlat
            guild_id = ctx.guild.id

            # Kanal ayarlı değilse, otomatik olarak mevcut kanalı ayarla
            if guild_id not in self.word_channel_id:
                self.word_channel_id[guild_id] = ctx.channel.id
                self.save_settings(guild_id)

            # Yanlış kanalda kullanılırsa uyar
            if ctx.channel.id != self.word_channel_id[guild_id]:
                await ctx.send(f"❌ Bu komut sadece <#{self.word_channel_id[guild_id]}> kanalında kullanılabilir!")
                return

            # Zaten aktif oyun varsa bilgi ver
            if guild_id in self.active_games:
                embed = nextcord.Embed(
                    title="🎮 Kelime Türetme Oyunu",
                    description="Oyun zaten aktif durumda! Son kullanılan kelimeden devam edebilirsiniz.",
                    color=0x00ff00
                )
                last_word = self.last_word.get(guild_id, random.choice(self.starting_words))
                embed.add_field(
                    name="Son Kelime",
                    value=f"**{last_word}**\n"
                          f"**{last_word[-1].upper()}** harfi ile başlayan bir kelime yazın!",
                    inline=False
                )
                await ctx.send(embed=embed)
                return

            # Yeni oyun başlat
            start_word = random.choice(self.starting_words)
            self.active_games[guild_id] = True
            if guild_id not in self.used_words:
                self.used_words[guild_id] = set()
            self.used_words[guild_id].add(start_word)
            self.last_word[guild_id] = start_word  # Son kelimeyi kaydet
            self.save_settings(guild_id)

            embed = nextcord.Embed(
                title="🎮 Kelime Türetme Oyunu Başladı!",
                description="Oyun kuralları:\n"
                           "• Son kelimenin son harfi ile başlayan kelimeler yazın\n"
                           "• Kelimeler Türkçe olmalı\n"
                           "• Aynı kelime tekrar kullanılamaz\n"
                           "• Prefix kullanmadan direkt kelime yazabilirsiniz",
                color=0x00ff00
            )
            embed.add_field(
                name="🎯 Başlangıç Kelimesi",
                value=f"**{start_word}**\n"
                      f"**{start_word[-1].upper()}** harfi ile başlayan bir kelime yazın!",
                inline=False
            )
            await ctx.send(embed=embed)
        else:
            # Yardım mesajını göster
            embed = nextcord.Embed(
                title="🎲 Kelime Türetme Oyunu - Nasıl Oynanır?",
                description="Eğlenceli kelime türetme oyununa hoş geldiniz!\n\n"
                           "**Komutlar:**\n"
                           "`!kelime başlat` - Yeni bir oyun başlatır\n"
                           "`!kelime` - Bu yardım mesajını gösterir\n\n"
                           "**Oyun Kuralları:**\n"
                           "• Son kelimenin son harfi ile başlayan kelimeler yazın\n"
                           "• Kelimeler Türkçe olmalı\n"
                           "• Aynı kelime tekrar kullanılamaz\n"
                           "• Prefix kullanmadan direkt kelime yazabilirsiniz",
                color=0x4287f5
            )
            
            embed.add_field(
                name="🎯 Örnek Oynanış",
                value="Bot: **merhaba**\n"
                      "Oyuncu 1: **araba**\n"
                      "Oyuncu 2: **ayva**\n"
                      "Oyuncu 3: **armut**\n"
                      "...",
                inline=False
            )
            
            embed.add_field(
                name="💡 İpuçları",
                value="• Oyun otomatik olarak bulunduğunuz kanalda başlar\n"
                      "• Kelimeler TDK sözlüğünde kontrol edilir\n"
                      "• Doğru kelimeler için ✅ emoji'si konur\n"
                      "• Yanlış kelimeler için özel uyarılar verilir",
                inline=False
            )
            
            embed.add_field(
                name="🏆 Başarı Kriterleri",
                value="• Kelimenin TDK sözlüğünde olması\n"
                      "• Son harfle başlayan yeni kelime yazılması\n"
                      "• Daha önce kullanılmamış olması",
                inline=False
            )
            
            embed.set_footer(text="İyi eğlenceler! 🎲")
            await ctx.send(embed=embed)

    async def send_notification(self, message, title, description, color=0xff0000, emoji="❌"):
        """Send a notification message"""
        try:
            # Send error message first
            notification = nextcord.Embed(
                title=f"{emoji} {title}",
                description=description,
                color=color
            )
            await message.reply(embed=notification, delete_after=5)
            
            # Then delete the incorrect word
            await asyncio.sleep(0.5)  # Short wait for message visibility
            await message.delete()
        except Exception as e:
            print(f"Notification error: {e}")
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        if guild_id not in self.word_channel_id or message.channel.id != self.word_channel_id[guild_id]:
            return

        if guild_id not in self.active_games:
            return

        # Komutları yoksay
        if message.content.startswith(('!', '?', '/', '.')):
            return

        word = message.content.lower().strip()
        
        # Son kelimeyi al
        last_word = self.last_word.get(guild_id, random.choice(self.starting_words))
        last_letter = last_word[-1]
        
        # Türkçe karakter düzeltmeleri
        if last_letter == 'ğ':
            last_letter = 'g'
        elif last_letter == 'ı':
            last_letter = 'i'
        elif last_letter == 'ü':
            last_letter = 'u'
        elif last_letter == 'ş':
            last_letter = 's'
        elif last_letter == 'ç':
            last_letter = 'c'
        elif last_letter == 'ö':
            last_letter = 'o'

        # Yeni kelimenin ilk harfini kontrol et
        first_letter = word[0]
        # Türkçe karakter düzeltmeleri
        if first_letter == 'ğ':
            first_letter = 'g'
        elif first_letter == 'ı':
            first_letter = 'i'
        elif first_letter == 'ü':
            first_letter = 'u'
        elif first_letter == 'ş':
            first_letter = 's'
        elif first_letter == 'ç':
            first_letter = 'c'
        elif first_letter == 'ö':
            first_letter = 'o'

        if first_letter != last_letter:
            await self.send_notification(
                message,
                "Yanlış Harf!",
                f"'{last_word}' kelimesinin son harfi '{last_letter.upper()}' ile başlayan bir kelime yazmalısın!",
                color=nextcord.Color.red(),
                emoji="❌"
            )
            return

        # Kelime daha önce kullanılmış mı kontrol et
        if word in self.used_words[guild_id]:
            await self.send_notification(
                message,
                "Kelime Tekrarı!",
                f"'{word}' kelimesi daha önce kullanıldı! Başka bir kelime dene.",
                color=nextcord.Color.orange(),
                emoji="🔄"
            )
            return

        # Kelime doğrulama
        try:
            is_valid = await self.check_word(word)
            if not is_valid:
                await self.send_notification(
                    message,
                    "Geçersiz Kelime!",
                    f"'{word}' kelimesi TDK sözlüğünde bulunamadı! Türkçe bir kelime kullan.",
                    color=nextcord.Color.red(),
                    emoji="📖"
                )
                return
        except Exception as e:
            await self.send_notification(
                message,
                "Bağlantı Hatası!",
                "TDK sözlüğüne şu anda ulaşılamıyor. Biraz bekleyip tekrar dene!",
                color=nextcord.Color.gold(),
                emoji="⚠️"
            )
            return

        # Kelimeyi kabul et ve sadece emoji koy
        self.used_words[guild_id].add(word)
        self.last_word[guild_id] = word  # Son kelimeyi güncelle
        self.save_settings(guild_id)
        await message.add_reaction("✅")

    async def create_session(self):
        """Create a new aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })

    async def close_session(self):
        """Close current session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def cog_unload(self):
        """Clean up session when cog is unloaded"""
        if self.session:
            asyncio.create_task(self.close_session())

    async def check_word(self, word):
        """Check word in TDK dictionary"""
        # Basic validations first
        if not word.isalpha():  # Should only contain letters
            return False
            
        if len(word) < 2:  # Should be at least 2 letters
            return False
            
        # Reject if contains non-Turkish characters
        turkish_letters = set('abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ')
        if not all(letter in turkish_letters for letter in word):
            return False

        max_retries = 5  # Maximum number of retries
        retry_delay = 2  # Delay between retries (seconds)

        for attempt in range(max_retries):
            try:
                await self.create_session()
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Origin': 'https://sozluk.gov.tr',
                    'Referer': 'https://sozluk.gov.tr/',
                    'Connection': 'keep-alive'
                }
                
                url = f'https://sozluk.gov.tr/gts?ara={word}'
                async with self.session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        try:
                            # Get response as text first
                            text = await response.text()
                            
                            # If contains "error", word not found
                            if '"error":"Sonuç bulunamadı"' in text:
                                return False
                                
                            # If contains "madde" and the word, it exists
                            if '"madde":' in text and f'"madde":"{word.lower()}"' in text.lower():
                                return True
                                
                            return False
                            
                        except Exception as e:
                            print(f"JSON parsing error: {e}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                            continue
                    else:
                        print(f"HTTP Error Code: {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                        continue
                    
            except Exception as e:
                print(f"TDK API error (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                continue
        
        # If all attempts failed
        raise Exception("Cannot connect to TDK API. Please try again later.")

def setup(bot):
    bot.add_cog(WordGame(bot)) 