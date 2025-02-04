import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
import json, os, re

class EventView(nextcord.ui.View):
    def __init__(self, event_id, cog):
        super().__init__(timeout=None)
        self.event_id = event_id
        self.cog = cog

    @nextcord.ui.button(label="Attending", style=nextcord.ButtonStyle.success)
    async def participant(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        event = self.cog.events.get(self.event_id)
        if not event:
            return await interaction.response.send_message("Event not found.", ephemeral=True)
        if user_id in event["not_attending"]:
            event["not_attending"].remove(user_id)
        if user_id not in event["participants"]:
            event["participants"].append(user_id)
        self.cog.save_events()
        new_embed = await self.cog.create_embed(event)
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.defer()

    @nextcord.ui.button(label="Not Attending", style=nextcord.ButtonStyle.danger)
    async def not_attending(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        user_id = str(interaction.user.id)
        event = self.cog.events.get(self.event_id)
        if not event:
            return await interaction.response.send_message("Event not found.", ephemeral=True)
        if user_id in event["participants"]:
            event["participants"].remove(user_id)
        if user_id not in event["not_attending"]:
            event["not_attending"].append(user_id)
        self.cog.save_events()
        new_embed = await self.cog.create_embed(event)
        await interaction.message.edit(embed=new_embed, view=self)
        await interaction.response.defer()

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.events_file = 'events.json'
        self.events = {}
        self.load_events()
        self.update_embeds.start()

    def load_events(self):
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for event_id, event in data.items():
                        if 'end_time' in event:
                            event['end_time'] = datetime.fromisoformat(event['end_time'])
                        self.events[event_id] = event
            except Exception as e:
                print(f"Error loading events: {e}")
                self.events = {}

    def save_events(self):
        save_data = {}
        for event_id, event in self.events.items():
            temp = event.copy()
            temp['end_time'] = event['end_time'].isoformat()
            save_data[event_id] = temp
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=4)

    async def create_embed(self, event):
        remaining = event['end_time'] - datetime.now()
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        remaining_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m {seconds}s"
        embed = nextcord.Embed(
            title=f"🥳 {event['title']}",
            color=0x00ff99,
            timestamp=datetime.now()
        )
        if 'creator_id' in event:
            creator = self.bot.get_user(int(event['creator_id']))
            if creator:
                embed.set_thumbnail(url=creator.display_avatar.url)
        embed.add_field(name="📅 Event Time", value=f"```{event['date']} {event['time']}```", inline=False)
        embed.add_field(name="⏳ Time Remaining", value=f"```{remaining_str}```", inline=False)
        attendees = [f"<@{uid}>" for uid in event['participants']][:5]
        attendee_text = "\n".join(attendees) or "No attendees yet"
        if len(event['participants']) > 5:
            attendee_text += f"\n...and {len(event['participants'])-5} more!"
        embed.add_field(name=f"✅ Attending ({len(event['participants'])})", value=attendee_text, inline=False)
        not_attending = [f"<@{uid}>" for uid in event['not_attending']][:5]
        not_attending_text = "\n".join(not_attending) or "No one declined yet"
        if len(event['not_attending']) > 5:
            not_attending_text += f"\n...and {len(event['not_attending'])-5} more!"
        embed.add_field(name=f"❌ Not Attending ({len(event['not_attending'])})", value=not_attending_text, inline=False)
        embed.set_footer(text="Update your attendance status using the buttons below!")
        return embed

    async def create_finished_embed(self, event):
        embed = nextcord.Embed(
            title=f"❌ {event['title']} - Ended",
            color=0xff0000,
            timestamp=datetime.now()
        )
        if 'creator_id' in event:
            creator = self.bot.get_user(int(event['creator_id']))
            if creator:
                embed.set_thumbnail(url=creator.display_avatar.url)
        embed.add_field(name="📅 Event Time", value=f"```{event['date']} {event['time']}```", inline=False)
        embed.add_field(name="Status", value="This event has ended.", inline=False)
        attendees = [f"<@{uid}>" for uid in event['participants']][:5]
        attendee_text = "\n".join(attendees) or "No attendees"
        if len(event['participants']) > 5:
            attendee_text += f"\n...and {len(event['participants'])-5} more!"
        embed.add_field(name=f"✅ Attended ({len(event['participants'])})", value=attendee_text, inline=False)
        not_attending = [f"<@{uid}>" for uid in event['not_attending']][:5]
        not_attending_text = "\n".join(not_attending) or "No one declined"
        if len(event['not_attending']) > 5:
            not_attending_text += f"\n...and {len(event['not_attending'])-5} more!"
        embed.add_field(name=f"❌ Did Not Attend ({len(event['not_attending'])})", value=not_attending_text, inline=False)
        embed.set_footer(text="Event has ended!")
        return embed

    @tasks.loop(seconds=1)
    async def update_embeds(self):
        now = datetime.now()
        to_remove = []
        for event_id, event in list(self.events.items()):
            if event['end_time'] < now:
                try:
                    channel = await self.bot.fetch_channel(event['channel_id'])
                    message = await channel.fetch_message(int(event['message_id']))
                except Exception as e:
                    print(f"Could not fetch channel or message: {e}")
                    to_remove.append(event_id)
                    continue

                finished_embed = await self.create_finished_embed(event)
                try:
                    await message.edit(embed=finished_embed, view=None)
                except Exception as e:
                    print(f"Error updating message: {e}")

                # Send DM to participants (or mention in channel if DMs are closed)
                for user_id in event['participants']:
                    member = channel.guild.get_member(int(user_id))
                    if not member:
                        continue
                    notification = f"Your event {event['title']} has started!"
                    try:
                        await member.send(notification)
                    except Exception:
                        await channel.send(f"{member.mention} {notification}")
                to_remove.append(event_id)
                continue

            try:
                channel = await self.bot.fetch_channel(event['channel_id'])
                message = await channel.fetch_message(int(event['message_id']))
            except nextcord.NotFound:
                print(f"Message not found, removing event {event_id}.")
                to_remove.append(event_id)
                continue

            new_embed = await self.create_embed(event)
            try:
                view = EventView(event_id, self)
                await message.edit(embed=new_embed, view=view)
            except Exception as e:
                print(f"Error updating message: {e}")
        for event_id in to_remove:
            if event_id in self.events:
                del self.events[event_id]
        if to_remove:
            self.save_events()

    @commands.command(name="createevent")
    @commands.has_permissions(manage_events=True)
    async def createevent(self, ctx, time=None, *, title=None):
        if not time or not title:
            embed = nextcord.Embed(
                title="❌ Missing Information!",
                description=("Please use the correct format:\n`!createevent <duration> <event name>`\n\n"
                             "**Time Format:**\n`d` -> Days, `h` -> Hours, `m` -> Minutes\nExample: `1d2h30m Movie Night`"),
                color=0xff0000
            )
            return await ctx.send(embed=embed)

        time_match = re.match(r"(\d+d)?(\d+h)?(\d+m)?", time.lower())
        if not time_match:
            return await ctx.send("❌ Invalid time format! Example: `1d2h30m`")

        days = int(time_match.group(1)[:-1]) if time_match.group(1) else 0
        hours = int(time_match.group(2)[:-1]) if time_match.group(2) else 0
        minutes = int(time_match.group(3)[:-1]) if time_match.group(3) else 0

        if days + hours + minutes == 0:
            return await ctx.send("❌ Invalid duration!")

        event_time = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes)
        event_id = str(len(self.events) + 1)
        self.events[event_id] = {
            "title": title,
            "date": event_time.strftime("%d.%m.%Y"),
            "time": event_time.strftime("%H:%M"),
            "end_time": event_time,
            "creator_id": str(ctx.author.id),
            "participants": [],
            "not_attending": [],
            "message_id": None,
            "channel_id": ctx.channel.id
        }
        embed = await self.create_embed(self.events[event_id])
        view = EventView(event_id, self)
        msg = await ctx.send(embed=embed, view=view)
        self.events[event_id]["message_id"] = str(msg.id)
        self.save_events()

    @createevent.error
    async def createevent_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = nextcord.Embed(
                title="⛔ Missing Permissions!",
                description="You need appropriate permissions to use this command.",
                color=0xff0000
            )
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Events(bot))
