import nextcord
from nextcord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta

class GiveawayView(nextcord.ui.View):
    def __init__(self, end_time: datetime, prize: str):
        super().__init__(timeout=None)
        self.end_time = end_time
        self.prize = prize
        self.participants = set()
        self.message = None

    @nextcord.ui.button(label="🎉 Join", style=nextcord.ButtonStyle.blurple)
    async def join_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("You have already joined the giveaway!", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("You joined the giveaway!", ephemeral=True)
            # Update "Participants" field
            if self.message:
                embed = self.message.embeds[0]
                updated = False
                for i, field in enumerate(embed.fields):
                    if field.name == "Participants":
                        embed.set_field_at(i, name="Participants", value=str(len(self.participants)), inline=False)
                        updated = True
                        break
                if not updated:
                    embed.add_field(name="Participants", value=str(len(self.participants)), inline=False)
                await self.message.edit(embed=embed, view=self)

    async def countdown(self):
        while True:
            remaining = self.end_time - datetime.now()
            if remaining.total_seconds() <= 0:
                break
            # Update "Time Remaining" field
            if self.message:
                embed = self.message.embeds[0]
                updated = False
                for i, field in enumerate(embed.fields):
                    if field.name == "Time Remaining":
                        embed.set_field_at(i, name="Time Remaining", value=str(remaining).split('.')[0], inline=False)
                        updated = True
                        break
                if not updated:
                    embed.add_field(name="Time Remaining", value=str(remaining).split('.')[0], inline=False)
                await self.message.edit(embed=embed, view=self)
            await asyncio.sleep(5)
        # Disable buttons and select winner when time is up
        for child in self.children:
            child.disabled = True
        if self.message:
            embed = self.message.embeds[0]
            if self.participants:
                winner_id = random.choice(list(self.participants))
                winner_mention = f"<@{winner_id}>"
                embed.description += f"\n\nWinner: {winner_mention}"
                embed.color = nextcord.Color.green()
                await self.message.edit(embed=embed, view=self)
                await self.message.channel.send(f"🎉 Congratulations {winner_mention}, you won **{self.prize}**!")
            else:
                embed.description += "\n\nNo participants found."
                embed.color = nextcord.Color.red()
                await self.message.edit(embed=embed, view=self)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="giveaway")
    @commands.has_permissions(manage_messages=True)
    async def create_giveaway(self, ctx, duration: str = None, *, prize: str = None):
        """
        Starts a new giveaway.
        
        Usage: `!giveaway <duration> <prize>`
        
        Time units:
          • s: seconds
          • m: minutes
          • h: hours
          • d: days
          
        Example: `!giveaway 10s PS5`
        """
        if not duration or not prize:
            embed = nextcord.Embed(
                title="Giveaway Command Usage",
                description=(
                    "Use the following format to start a new giveaway:\n\n"
                    "`!giveaway <duration> <prize>`\n\n"
                    "**Time Units:**\n"
                    "• `s` → Seconds\n"
                    "• `m` → Minutes\n"
                    "• `h` → Hours\n"
                    "• `d` → Days\n\n"
                    "**Example:** `!giveaway 1h PlayStation 5`"
                ),
                color=nextcord.Color.blurple()
            )
            await ctx.send(embed=embed)
            return

        # Delete command message
        await ctx.message.delete()

        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = duration[-1].lower()
        if unit not in time_units:
            await ctx.send(
                "Invalid duration format!\nPlease use correct time units: s (seconds), m (minutes), h (hours), d (days).\nExample: `!giveaway 10s PS5`"
            )
            return
        try:
            number = int(duration[:-1])
        except ValueError:
            await ctx.send("Invalid duration value! Please use like the example: `!giveaway 10s PS5`")
            return

        total_seconds = number * time_units[unit]
        end_time = datetime.now() + timedelta(seconds=total_seconds)

        embed = nextcord.Embed(
            title="🎉 GIVEAWAY 🎉",
            description=f"**Prize: {prize}**\n\nClick the **🎉 Join** button below to participate.",
            color=nextcord.Color.blue()
        )
        embed.add_field(name="Participants", value="0", inline=False)
        embed.add_field(name="Time Remaining", value=str(timedelta(seconds=total_seconds)).split('.')[0], inline=False)
        view = GiveawayView(end_time, prize)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

        ctx.bot.loop.create_task(view.countdown())

    @create_giveaway.error
    async def create_giveaway_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = nextcord.Embed(
                title="Permission Error",
                description="You don't have permission to use this command!",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = nextcord.Embed(
                title="Error",
                description=f"An error occurred: {str(error)}",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Giveaway(bot))
