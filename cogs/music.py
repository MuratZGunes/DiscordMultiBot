import re
import time
import asyncio
import nextcord
from nextcord.ext import commands
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global data structures
song_queues = {}       # {guild_id: [songs]}
song_loop = {}         # {guild_id: bool}
current_song = {}      # {guild_id: song dictionary}
song_counter = 0       # For unique id
command_channels = {}  # {guild_id: TextChannel}

# Additional global structures for Spotify playlists:
spotify_playlist_offsets = {}   # {guild_id: current offset}
spotify_playlist_totals = {}    # {guild_id: total song count}
spotify_playlist_ids = {}       # {guild_id: playlist id}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'ignoreerrors': True,
    'no_warnings': True
}

def extract_spotify_playlist_id(url: str) -> str:
    pattern = r"(?:playlist/|spotify:playlist:)([A-Za-z0-9]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

async def update_duration(message, song, voice_client):
    duration = song.get("duration")
    if not duration:
        return
    # Her oynatma başladığında gerçek zaman damgası kaydediliyor.
    song["start_time"] = time.time()
    while True:
        if not voice_client.is_connected():
            break
        if voice_client.is_playing() and not voice_client.is_paused():
            elapsed = time.time() - song["start_time"]
        else:
            elapsed = 0
        remaining = int(duration - elapsed)
        if remaining < 0:
            remaining = 0
        minutes, seconds = divmod(remaining, 60)
        total_minutes, total_seconds = divmod(duration, 60)
        base = message.embeds[0].description.split("\nStatus:")[0]
        new_desc = f"{base}\nStatus: **Playing**\nTime Remaining: **{minutes:02d}:{seconds:02d}** / **{total_minutes:02d}:{total_seconds:02d}**"
        embed = message.embeds[0]
        embed.description = new_desc
        try:
            await message.edit(embed=embed)
        except Exception:
            break
        await asyncio.sleep(2)

class PlaylistSkipView(nextcord.ui.View):
    def __init__(self, guild_id: int, ctx: commands.Context, songs: list, timeout=120):
        super().__init__(timeout=timeout)
        self.guild_id = guild_id
        self.ctx = ctx
        self.playlist_songs = songs.copy()
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for i, song in enumerate(self.playlist_songs, start=1):
            label = f"{i}: {song['title'][:20]}"
            btn = nextcord.ui.Button(label=label, style=nextcord.ButtonStyle.secondary, custom_id=str(i))
            btn.callback = self.button_callback
            self.add_item(btn)

    async def button_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if not spotify_playlist_ids.get(self.guild_id):
            try:
                await interaction.followup.send("Playlist mode disabled.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        try:
            index = int(interaction.data["custom_id"]) - 1
        except Exception:
            return
        if index < 0 or index >= len(self.playlist_songs):
            try:
                await interaction.followup.send("Invalid song number.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        queue = song_queues.get(self.guild_id, [])
        del queue[:index]
        if self.ctx.guild.voice_client:
            self.ctx.guild.voice_client.stop()
        try:
            await interaction.followup.send(f"Skipped to song {index+1}.", ephemeral=True)
        except nextcord.NotFound:
            pass
        new_snapshot = queue[:5]
        self.playlist_songs = new_snapshot.copy()
        self.update_buttons()
        if new_snapshot:
            try:
                await interaction.message.edit(content="Playlist skip options updated:", view=self)
            except nextcord.NotFound:
                pass
        else:
            try:
                await interaction.message.edit(content="Playlist skip options removed.", view=None)
            except nextcord.NotFound:
                pass

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

class SongControlView(nextcord.ui.View):
    def __init__(self, guild_id: int, song_id: int, ctx: commands.Context, show_skip: bool = True, timeout=60, active: bool = True):
        super().__init__(timeout=timeout)
        self.guild_id = guild_id
        self.song_id = song_id
        self.ctx = ctx
        self.active = active
        self.message = None
        if active:
            if show_skip:
                skip_button = nextcord.ui.Button(label="▶", style=nextcord.ButtonStyle.primary)
                skip_button.callback = self.skip_callback
                self.add_item(skip_button)
            stop_button = nextcord.ui.Button(label="Song Stop", style=nextcord.ButtonStyle.danger)
            stop_button.callback = self.stop_callback
            self.add_item(stop_button)
            # loop butonuna custom_id "loop" ekleniyor
            loop_button = nextcord.ui.Button(label="Loop: Off", style=nextcord.ButtonStyle.secondary, custom_id="loop")
            loop_button.callback = self.loop_callback
            self.add_item(loop_button)
        else:
            for item in self.children:
                item.disabled = True

    async def skip_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = self.ctx.guild.voice_client
        if not vc:
            for child in self.children:
                child.disabled = True
            try:
                await interaction.followup.send("Bot is not in voice channel. Buttons disabled.", ephemeral=True)
            except nextcord.NotFound:
                pass
            await interaction.message.edit(view=self)
            return
        if not interaction.user.voice or interaction.user.voice.channel != vc.channel:
            try:
                await interaction.followup.send("You must be in the same voice channel.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        current = current_song.get(self.ctx.guild.id, {})
        if current.get("msg"):
            embed = current["msg"].embeds[0]
            base = embed.description.split("\nStatus:")[0]
            embed.description = f"{base}\nStatus: **Skipped**"
            try:
                await current["msg"].edit(embed=embed)
            except Exception:
                pass
        if current.get("song_id") == self.song_id:
            vc.stop()
            for child in self.children:
                child.disabled = True
            try:
                await interaction.message.edit(content="Skipped to song.", view=self)
            except nextcord.NotFound:
                pass
        else:
            queue = song_queues.get(self.guild_id, [])
            index = next((i for i, s in enumerate(queue) if s.get("song_id") == self.song_id), None)
            if index is None:
                try:
                    await interaction.followup.send("Song is already playing or not found.", ephemeral=True)
                except nextcord.NotFound:
                    pass
                return
            del queue[:index]
            if vc.is_playing():
                vc.stop()
                for child in self.children:
                    child.disabled = True
                try:
                    await interaction.message.edit(content="Skipped to song.", view=self)
                except nextcord.NotFound:
                    pass
            else:
                try:
                    await interaction.followup.send("No song currently playing.", ephemeral=True)
                except nextcord.NotFound:
                    pass

    async def stop_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = self.ctx.guild.voice_client
        if not vc:
            for child in self.children:
                child.disabled = True
            try:
                await interaction.followup.send("Bot is not in voice channel. Buttons disabled.", ephemeral=True)
            except nextcord.NotFound:
                pass
            await interaction.message.edit(view=self)
            return
        current = current_song.get(self.ctx.guild.id)
        if current and current.get("msg"):
            msg = current["msg"]
            embed = msg.embeds[0]
            base = embed.description.split("\nStatus:")[0]
            embed.description = f"{base}\nStatus: **Stopped** (Stopped by: {interaction.user.display_name})"
            embed.set_footer(text=f"Stopped by: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            try:
                await msg.edit(embed=embed)
            except Exception:
                pass
        if self.ctx.voice_client:
            await self.ctx.voice_client.disconnect()
        song_queues.pop(self.guild_id, None)
        song_loop[self.guild_id] = False
        current_song.pop(self.guild_id, None)
        spotify_playlist_ids.pop(self.guild_id, None)
        spotify_playlist_offsets.pop(self.guild_id, None)
        spotify_playlist_totals.pop(self.guild_id, None)
        try:
            await interaction.followup.send(f"Music stopped by {interaction.user.display_name} and bot disconnected.", ephemeral=True)
        except nextcord.NotFound:
            pass
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

    async def loop_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = self.ctx.guild.voice_client
        if not vc:
            for child in self.children:
                child.disabled = True
            try:
                await interaction.followup.send("Bot is not in voice channel. Buttons disabled.", ephemeral=True)
            except nextcord.NotFound:
                pass
            await interaction.message.edit(view=self)
            return
        if not interaction.user.voice or interaction.user.voice.channel != vc.channel:
            try:
                await interaction.followup.send("You must be in the same voice channel.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        current_state = song_loop.get(self.guild_id, False)
        song_loop[self.guild_id] = not current_state
        new_state = song_loop[self.guild_id]
        for item in self.children:
            if item.custom_id == "loop":
                item.label = "Loop: Active" if new_state else "Loop: Off"
        try:
            await interaction.followup.send(f"Loop mode {'enabled' if new_state else 'disabled'}.", ephemeral=True)
        except nextcord.NotFound:
            pass
        await interaction.message.edit(view=self)

    async def on_timeout(self):
        # Eğer bu view'deki şarkı artık oynatılmıyorsa butonları devre dışı bırak
        if current_song.get(self.guild_id, {}).get("song_id") != self.song_id:
            for item in self.children:
                item.disabled = True
            if self.message:
                try:
                    await self.message.edit(view=self)
                except Exception:
                    pass

class QueuedSongControlView(nextcord.ui.View):
    def __init__(self, guild_id: int, song_id: int, ctx: commands.Context, timeout=60):
        super().__init__(timeout=timeout)
        self.guild_id = guild_id
        self.song_id = song_id
        self.ctx = ctx
        self.message = None
        play_button = nextcord.ui.Button(label="▶ Play", style=nextcord.ButtonStyle.primary)
        play_button.callback = self.play_callback
        self.add_item(play_button)

    async def play_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        vc = self.ctx.guild.voice_client
        if not vc:
            for child in self.children:
                child.disabled = True
            try:
                await interaction.followup.send("Bot is not in voice channel.", ephemeral=True)
            except nextcord.NotFound:
                pass
            await interaction.message.edit(view=self)
            return
        if not interaction.user.voice or interaction.user.voice.channel != vc.channel:
            try:
                await interaction.followup.send("You must be in the same voice channel.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        queue = song_queues.get(self.guild_id, [])
        index = next((i for i, s in enumerate(queue) if s.get("song_id") == self.song_id), None)
        if index is None:
            try:
                await interaction.followup.send("Song not found.", ephemeral=True)
            except nextcord.NotFound:
                pass
            return
        del queue[:index]
        if vc.is_playing():
            vc.stop()  # play_next tetiklenecek
            try:
                await interaction.followup.send("Skipping to next song.", ephemeral=True)
            except nextcord.NotFound:
                pass
        else:
            try:
                await interaction.followup.send("No song currently playing.", ephemeral=True)
            except nextcord.NotFound:
                pass

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')
        ))

    async def disable_current_song(self, guild, reason: str):
        song = current_song.get(guild.id)
        if song and song.get("msg"):
            msg = song["msg"]
            view = msg.view
            if view:
                for child in view.children:
                    child.disabled = True
            embed = msg.embeds[0]
            embed.description += f"\n\n**Bot Left Channel:** {reason}"
            try:
                await msg.edit(embed=embed, view=view)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is None or after.channel is not None:
            return
        vc = member.guild.voice_client
        if vc is None:
            return
        if before.channel.id == vc.channel.id:
            members = before.channel.members
            human_count = sum(1 for m in members if not m.bot)
            if human_count == 0:
                await vc.disconnect()
                song_queues.pop(member.guild.id, None)
                song_loop[member.guild.id] = False
                current_song.pop(member.guild.id, None)
                spotify_playlist_offsets.pop(member.guild.id, None)
                spotify_playlist_totals.pop(member.guild.id, None)
                spotify_playlist_ids.pop(member.guild.id, None)
                text_channel = command_channels.get(member.guild.id, member.guild.text_channels[0])
                await self.disable_current_song(member.guild, "Automatically left because no users remained in voice channel.")
                embed = nextcord.Embed(
                    title="👋 Auto Disconnect",
                    description="Left the voice channel because no users remained.",
                    color=0xFFD700
                )
                await text_channel.send(embed=embed)

    async def play_song(self, ctx, song, reuse: bool = False):
        command_channels[ctx.guild.id] = ctx.channel
        vc = ctx.voice_client
        if not vc:
            if ctx.author.voice:
                vc = await ctx.author.voice.channel.connect()
            else:
                embed = nextcord.Embed(title="⚠️ Error", description="You need to join a voice channel first.", color=0xFF0000)
                await ctx.send(embed=embed)
                return

        global song_counter
        song["start_time"] = time.time()
        if "song_id" not in song:
            song["song_id"] = song_counter
            song_counter += 1
        current_song[ctx.guild.id] = song

        if spotify_playlist_ids.get(ctx.guild.id):
            reuse = True

        if song["platform"] == "spotify":
            title_text = "<:spotify:1335002498590572646> Spotify"
            color = 0x1DB954
        else:
            title_text = "<:youtube:1335002540445663302> YouTube"
            color = 0xFF0000

        desc = (
            f"Now Playing: [{song['title']}]({song['display_url']})\n\n"
            f"Status: **Playing**\n"
            "Time Remaining: **00:00** / **00:00**"
        )
        embed = nextcord.Embed(
            title=title_text,
            description=desc,
            color=color
        )
        requester = song.get("requested_by", {})
        embed.set_footer(text=f"Requested by: {requester.get('name','')}", icon_url=requester.get("avatar", ""))
        if not reuse:
            view = SongControlView(ctx.guild.id, song["song_id"], ctx, show_skip=False, active=True)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            song["msg"] = msg
            asyncio.create_task(update_duration(msg, song, vc))
        else:
            if current_song.get(ctx.guild.id) and current_song[ctx.guild.id].get("msg"):
                msg = current_song[ctx.guild.id]["msg"]
                try:
                    await msg.edit(embed=embed)
                except Exception:
                    pass
                song["msg"] = msg
                asyncio.create_task(update_duration(msg, song, vc))
            else:
                view = SongControlView(ctx.guild.id, song["song_id"], ctx, show_skip=False, active=True)
                msg = await ctx.send(embed=embed, view=view)
                view.message = msg
                song["msg"] = msg
                asyncio.create_task(update_duration(msg, song, vc))
        try:
            source = nextcord.FFmpegPCMAudio(song["stream_url"], executable="ffmpeg", **FFMPEG_OPTIONS)
        except Exception:
            await ctx.send("FFmpeg ile ilgili bir hata oluştu. Lütfen FFmpeg'in yüklü ve PATH'e ekli olduğundan emin ol.")
            return

        def after_playing(error):
            async def after_tasks():
                try:
                    msg = song.get("msg")
                    if msg and msg.view:
                        for child in msg.view.children:
                            child.disabled = True
                        await msg.edit(view=msg.view)
                except Exception:
                    pass
                try:
                    if song_loop.get(ctx.guild.id, False):
                        await self.play_song(ctx, current_song[ctx.guild.id], reuse=True)
                    else:
                        await self.play_next(ctx)
                except Exception:
                    pass
            asyncio.run_coroutine_threadsafe(after_tasks(), self.bot.loop)
        vc.play(source, after=after_playing)

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        if spotify_playlist_ids.get(guild_id):
            if len(song_queues.get(guild_id, [])) < 5:
                await self.load_next_spotify_songs(ctx)
        if guild_id not in song_queues or not song_queues[guild_id]:
            current_song.pop(guild_id, None)
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            return
        next_song = song_queues[guild_id].pop(0)
        await self.play_song(ctx, next_song)

    async def load_next_spotify_songs(self, ctx):
        guild_id = ctx.guild.id
        offset = spotify_playlist_offsets.get(guild_id, 0)
        total = spotify_playlist_totals.get(guild_id, 0)
        if offset >= total:
            return
        eksik = 5 - len(song_queues.get(guild_id, []))
        limit = min(eksik, total - offset)
        try:
            data = self.sp.playlist_tracks(spotify_playlist_ids[guild_id], limit=limit, offset=offset)
            spotify_playlist_offsets[guild_id] = offset + limit
        except Exception:
            return
        items = data.get("items", [])
        if not items:
            return
        songs = []
        loop_ev = asyncio.get_event_loop()
        for item in items:
            track = item.get("track")
            if not track:
                continue
            track_name = track.get("name")
            artists = track.get("artists", [])
            artist_name = artists[0].get("name") if artists else ""
            query = f"{track_name} {artist_name}"
            try:
                result = await loop_ev.run_in_executor(
                    None, lambda: youtube_dl.YoutubeDL(ydl_opts).extract_info(f"ytsearch:{query}", download=False)
                )
                if result and "entries" in result and result["entries"]:
                    entry = next((e for e in result["entries"] if e and e.get("url")), None)
                    if entry:
                        song = {
                            "platform": "spotify",
                            "title": entry.get("title", track_name),
                            "display_url": entry.get("webpage_url", query),
                            "stream_url": entry.get("url"),
                            "duration": entry.get("duration", 0),
                            "requested_by": {
                                "name": ctx.author.display_name,
                                "avatar": ctx.author.display_avatar.url
                            }
                        }
                        songs.append(song)
            except Exception:
                continue
        song_queues[guild_id].extend(songs)
        if song_queues[guild_id]:
            view = PlaylistSkipView(guild_id, ctx, songs=song_queues[guild_id][:5])
            view.message = None
            current = current_song.get(guild_id, {})
            if current.get("msg"):
                try:
                    await current["msg"].edit(view=view)
                except Exception:
                    pass

    async def process_youtube_playlist(self, ctx, search: str):
        ydl_playlist_opts = ydl_opts.copy()
        ydl_playlist_opts["playlistend"] = 5
        loop_ev = asyncio.get_event_loop()
        try:
            data = await loop_ev.run_in_executor(
                None, lambda: youtube_dl.YoutubeDL(ydl_playlist_opts).extract_info(search.strip(), download=False)
            )
        except Exception:
            embed = nextcord.Embed(title="⚠️ Error", description="Could not fetch YouTube playlist.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        if "entries" not in data or not data["entries"]:
            embed = nextcord.Embed(title="⚠️ Error", description="Playlist is empty or could not be fetched.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        entries = data["entries"]
        songs = []
        for entry in entries:
            if not entry:
                continue
            song = {
                "platform": "youtube",
                "title": entry.get("title", "Song"),
                "display_url": entry.get("webpage_url", search.strip()),
                "stream_url": entry.get("url"),
                "duration": entry.get("duration", 0),
                "requested_by": {
                    "name": ctx.author.display_name,
                    "avatar": ctx.author.display_avatar.url
                }
            }
            songs.append(song)
        embed = nextcord.Embed(
            title="🎶 Playlist Added",
            description=f"{len(songs)} songs (first 5) added to queue.",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        guild_id = ctx.guild.id
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            if songs:
                first_song = songs.pop(0)
                await self.play_song(ctx, first_song)
        if guild_id not in song_queues:
            song_queues[guild_id] = []
        song_queues[guild_id].extend(songs)
        if song_queues[guild_id]:
            view = PlaylistSkipView(guild_id, ctx, songs=song_queues[guild_id][:5])
            await ctx.send("Click buttons to skip to songs in playlist:", view=view)

    async def process_spotify_playlist(self, ctx, search: str):
        search = search.strip()
        playlist_id = extract_spotify_playlist_id(search)
        if not playlist_id:
            embed = nextcord.Embed(title="⚠️ Error", description="Please enter a valid Spotify playlist URL.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        try:
            full_playlist = self.sp.playlist(playlist_id)
            total_tracks = full_playlist.get("tracks", {}).get("total", 0)
            spotify_playlist_totals[ctx.guild.id] = total_tracks
            spotify_playlist_ids[ctx.guild.id] = playlist_id
            data = self.sp.playlist_tracks(playlist_id, limit=5, offset=0)
            spotify_playlist_offsets[ctx.guild.id] = 5
        except Exception:
            embed = nextcord.Embed(title="⚠️ Error", description="Could not fetch Spotify playlist.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        items = data.get("items", [])
        if not items:
            embed = nextcord.Embed(title="⚠️ Error", description="Spotify playlist is empty.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        songs = []
        loop_ev = asyncio.get_event_loop()
        for item in items:
            track = item.get("track")
            if not track:
                continue
            track_name = track.get("name")
            artists = track.get("artists", [])
            artist_name = artists[0].get("name") if artists else ""
            query = f"{track_name} {artist_name}"
            try:
                result = await loop_ev.run_in_executor(
                    None, lambda: youtube_dl.YoutubeDL(ydl_opts).extract_info(f"ytsearch:{query}", download=False)
                )
                if result and "entries" in result and result["entries"]:
                    entry = next((e for e in result["entries"] if e and e.get("url")), None)
                    if entry:
                        song = {
                            "platform": "spotify",
                            "title": entry.get("title", track_name),
                            "display_url": entry.get("webpage_url", query),
                            "stream_url": entry.get("url"),
                            "duration": entry.get("duration", 0),
                            "requested_by": {
                                "name": ctx.author.display_name,
                                "avatar": ctx.author.display_avatar.url
                            }
                        }
                        songs.append(song)
            except Exception:
                continue

        embed = nextcord.Embed(
            title="🎶 Playlist Added",
            description=f"{len(songs)} songs (first 5) added to queue.",
            color=0x1DB954
        )
        await ctx.send(embed=embed)
        guild_id = ctx.guild.id
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            if songs:
                first_song = songs.pop(0)
                await self.play_song(ctx, first_song)
        if guild_id not in song_queues:
            song_queues[guild_id] = []
        song_queues[guild_id].extend(songs)
        if song_queues[guild_id]:
            view = PlaylistSkipView(guild_id, ctx, songs=song_queues[guild_id][:5])
            current = current_song.get(guild_id, {})
            if current.get("msg"):
                try:
                    await current["msg"].edit(content="Playlist skip options updated:", view=view)
                except Exception:
                    pass
            else:
                await ctx.send("Click buttons to skip to songs in playlist:", view=view)

    @commands.command()
    async def join(self, ctx):
        command_channels[ctx.guild.id] = ctx.channel
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            embed = nextcord.Embed(title="✅ Connected", description="Joined the voice channel.", color=0x00FF00)
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="⚠️ Error", description="You need to join a voice channel first.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        command_channels[ctx.guild.id] = ctx.channel
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            song_queues.pop(ctx.guild.id, None)
            song_loop[ctx.guild.id] = False
            current_song.pop(ctx.guild.id, None)
            spotify_playlist_offsets.pop(ctx.guild.id, None)
            spotify_playlist_totals.pop(ctx.guild.id, None)
            spotify_playlist_ids.pop(ctx.guild.id, None)
            await self.disable_current_song(ctx.guild, "Bot left the channel by command.")
            embed = nextcord.Embed(title="👋 Disconnected", description="Left the voice channel.", color=0x00FF00)
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(title="⚠️ Error", description="Bot is not in a voice channel.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.command(name="p", aliases=["play", "song"])
    async def p(self, ctx, *, search: str):
        search = search.strip()
        command_channels[ctx.guild.id] = ctx.channel
        global song_counter
        guild_id = ctx.guild.id
        if guild_id not in song_queues:
            song_queues[guild_id] = []
        if spotify_playlist_ids.get(guild_id):
            spotify_playlist_ids.pop(guild_id, None)
            spotify_playlist_offsets.pop(guild_id, None)
            spotify_playlist_totals.pop(guild_id, None)
            if current_song.get(guild_id) and current_song[guild_id].get("msg"):
                try:
                    await current_song[guild_id]["msg"].edit(view=None)
                except Exception:
                    pass

        # Şarkı yükleniyor embed'i turuncu renkte (0xFFA500)
        loading_embed = nextcord.Embed(title="Loading", description="Please wait, preparing your song...", color=0xFFA500)
        loading_msg = await ctx.send(embed=loading_embed)

        if ("open.spotify.com/playlist/" in search) or search.startswith("spotify:playlist:"):
            await loading_msg.delete()
            await self.process_spotify_playlist(ctx, search)
            return

        if (("open.spotify.com" in search and "/track/" in search) or search.startswith("spotify:track:")):
            platform = "spotify"
            try:
                search = search.replace("/intl-tr", "").strip()
                m = re.search(r"track/([a-zA-Z0-9]+)", search)
                if m:
                    track_id = m.group(1).strip()
                else:
                    track_id = search.split("spotify:track:")[1].strip()
                track = self.sp.track(track_id)
                title = track['name']
                artist = track['artists'][0]['name']
                query = f"{title} {artist}"
                display_url = search
            except Exception:
                await loading_msg.delete()
                embed = nextcord.Embed(title="⚠️ Error", description="Could not fetch Spotify song.", color=0xFF0000)
                await ctx.send(embed=embed)
                return
        elif search.startswith("http"):
            platform = "youtube"
            query = search.strip()
            display_url = search.strip()
        else:
            platform = "youtube"
            query = search
            display_url = None
        loop_ev = asyncio.get_event_loop()
        try:
            data = await loop_ev.run_in_executor(
                None, lambda: youtube_dl.YoutubeDL(ydl_opts).extract_info(query, download=False)
            )
        except Exception:
            await loading_msg.delete()
            embed = nextcord.Embed(title="⚠️ Error", description="Song not found or could not be downloaded.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        await loading_msg.delete()
        if 'entries' in data:
            if not data['entries']:
                embed = nextcord.Embed(title="⚠️ Error", description="Searched song not found.", color=0xFF0000)
                await ctx.send(embed=embed)
                return
            data = data['entries'][0]
        stream_url = data.get('url')
        if not stream_url:
            embed = nextcord.Embed(title="⚠️ Error", description="Could not get stream URL.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        song_title = data.get('title', 'Song')
        if display_url is None:
            display_url = data.get("webpage_url", "https://www.youtube.com")
        song = {
            "platform": platform,
            "title": song_title,
            "display_url": display_url,
            "stream_url": stream_url,
            "duration": data.get("duration", 0),
            "requested_by": {
                "name": ctx.author.display_name,
                "avatar": ctx.author.display_avatar.url
            }
        }
        if ctx.voice_client and ctx.voice_client.is_playing():
            duration_minutes = song["duration"] // 60
            duration_seconds = song["duration"] % 60
            song["song_id"] = song_counter
            song_counter += 1
            song_queues[guild_id].append(song)
            position = len(song_queues[guild_id])
            embed = nextcord.Embed(
                title=(f"{'<:spotify:1335002498590572646>' if platform=='spotify' else '<:youtube:1335002540445663302>'} Added to Queue"),
                description=(f"[{song_title}]({display_url}) added to queue.\nPosition: **{position}**\nDuration: **{duration_minutes:02d}:{duration_seconds:02d}**"),
                color=0x1DB954 if platform=='spotify' else 0xFF0000
            )
            embed.set_footer(text=f"Added by: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
            view = QueuedSongControlView(guild_id, song["song_id"], ctx)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
        else:
            await self.play_song(ctx, song)

def setup(bot):
    bot.add_cog(Music(bot))
