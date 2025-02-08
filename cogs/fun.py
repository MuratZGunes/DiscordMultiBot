import nextcord
from nextcord.ext import commands, tasks
import random
import aiohttp
import asyncio
import datetime

# Bot owner check
def is_me(ctx):
    print(f"Checking if user ID {ctx.author.id} is the bot owner.")
    return ctx.author.id == 263973476623187969  # Replace this number with your Discord ID

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.alarm_task = None  # to hold alarm task

    @commands.command(name="roll", aliases=["dice"])
    async def roll_dice(self, ctx, number: int = 6):
        """Rolls a dice. Default is 6-sided, but you can specify any number."""
        if number <= 0:
            await ctx.send("Please enter a positive number!")
            return
        result = random.randint(1, number)
        await ctx.send(f"🎲 Rolled: **{result}** (1-{number})")

    @commands.command(name="choose", aliases=["random", "select"])
    async def choose(self, ctx, *choices: str):
        """Randomly chooses from given options."""
        if len(choices) < 2:
            embed = nextcord.Embed(
                title="Error!",
                description="You must provide at least 2 options!\nExample usage: `!choose pizza hamburger pasta`",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=embed)
            return

        selected = random.choice(choices)
        embed = nextcord.Embed(
            title="🎉 Choice Made!",
            color=nextcord.Color.green()
        )
        embed.add_field(
            name="Given Options", 
            value="\n".join(f"**{i+1}.** {choice}" for i, choice in enumerate(choices)), 
            inline=False
        )
        embed.add_field(
            name="My Choice", 
            value=f"👉 **{selected}**", 
            inline=False
        )
        embed.set_footer(text="Random selection made.")
        await ctx.send(embed=embed)

    @commands.command(name="flip", aliases=["coinflip", "coin"])
    async def coinflip(self, ctx):
        """Flips a coin."""
        result = random.choice(["Heads", "Tails"])
        await ctx.send(f"🪙 Coin flipped: **{result}**!")

    @commands.command(name="joke", aliases=["telljoke"])
    async def tell_joke(self, ctx):
        """Tells a random joke."""
        jokes = [
            "Why are computer hackers always hungry? Because they're always looking for 'cookies'!",
            "Why did the computer go to the doctor? Because it had a virus!",
            "Why was the math book sad? Because it had too many problems!",
            "Why don't programmers like nature? It has too many bugs!",
            "What did the computer do at lunchtime? Had a byte!"
        ]
        await ctx.send(f"😄 {random.choice(jokes)}")

    @commands.command(name="8ball", aliases=["fortune"])
    async def magic_8ball(self, ctx, *, question: str):
        """Answers your questions using Magic 8 Ball."""
        responses = [
            "It is certain!",
            "It is decidedly so.",
            "Without a doubt!",
            "Yes, definitely!",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        await ctx.send(f"🎱 Question: {question}\nAnswer: **{random.choice(responses)}**")

    @commands.command(name="rps", aliases=["rockpaperscissors"])
    async def rock_paper_scissors(self, ctx, choice: str = None):
        """Single player rock-paper-scissors game. Your choice is shown with emojis."""
        valid = ["rock", "paper", "scissors"]
        emojis = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        if choice is None or choice.lower() not in valid:
            await ctx.send("Please make a valid choice: rock, paper, or scissors! Example: `!rps rock`")
            return

        user_choice = choice.lower()
        bot_choice = random.choice(valid)

        if user_choice == bot_choice:
            result = "🤝 It's a tie!"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "🎉 You win!"
        else:
            result = "😔 You lose!"

        await ctx.send(
            f"You: **{user_choice} {emojis[user_choice]}** - "
            f"Bot: **{bot_choice} {emojis[bot_choice]}**\n\n"
            f"Result: **{result}**"
        )

    @commands.command(name="cat")
    async def cat(self, ctx):
        """Sends a random cat photo."""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
                if resp.status != 200:
                    await ctx.send("Couldn't fetch cat photo!")
                    return
                data = await resp.json()
                if data:
                    await ctx.send(data[0]["url"])
                else:
                    await ctx.send("No cat photo found!")

    @commands.command(name="dog")
    async def dog(self, ctx):
        """Sends a random dog photo."""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                if resp.status != 200:
                    await ctx.send("Couldn't fetch dog photo!")
                    return
                data = await resp.json()
                if data and data.get("message"):
                    await ctx.send(data["message"])
                else:
                    await ctx.send("No dog photo found!")

    @commands.command(name="fact")
    async def random_fact(self, ctx):
        """Gives a random fact."""
        facts = [
            "The blue whale is the largest animal on Earth.",
            "The human brain has about 100 billion nerve cells.",
            "Venus is the hottest planet in our Solar System.",
            "Earth orbits the Sun at 107,000 km per hour.",
            "Cats can sleep up to 16 hours a day."
        ]
        await ctx.send(f"🤓 {random.choice(facts)}")

    @commands.command(name="emoji", aliases=["randomemoji"])
    async def random_emoji(self, ctx):
        """Sends a random emoji."""
        emojis = ["😀", "😂", "😎", "😍", "🤖", "👻", "🎃", "🚀"]
        await ctx.send(random.choice(emojis))

    async def alarm_loop(self, ctx, hour: int, minute: int):
        """Checks every second until the specified time to send DM."""
        while True:
            now = datetime.datetime.now()
            if now.hour == hour and now.minute == minute:
                try:
                    if ctx.author.dm_channel is None:
                        await ctx.author.create_dm()
                    await ctx.author.dm_channel.send(f"⏰ **{ctx.author.display_name}**, alarm time!")
                except nextcord.Forbidden:
                    await ctx.send(f"⏰ {ctx.author.mention}, alarm time!")
                break
            await asyncio.sleep(1)

    @commands.command(name="alarm", aliases=["setalarm"])
    async def startalarm(self, ctx, time: str = None):
        """Sets an alarm. When the specified time (HH:MM format) comes, alerts via DM.
        
        Example usage:
        `!alarm 14:30`
        
        **Note:** The alarm is set for you."""
        if time is None:
            await ctx.send("❌ Please enter the alarm time in this format: `!alarm HH:MM`\nExample: `!alarm 14:30`")
            return

        try:
            hour_str, minute_str = time.split(":")
            hour = int(hour_str)
            minute = int(minute_str)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                await ctx.send("❌ Invalid time format! Hour must be 0-23, minute must be 0-59.")
                return

            await ctx.send(f"✅ **{ctx.author.display_name}**, alarm set for {hour:02d}:{minute:02d}!")
            self.bot.loop.create_task(self.alarm_loop(ctx, hour, minute))
        except ValueError:
            await ctx.send("❌ Invalid time format! Please use `HH:MM` format.\nExample: `!alarm 14:30`")

    @commands.command(name="lovemeter")
    async def lovemeter(self, ctx, *, name: str = None):
        """Shows how much the specified person loves you.
        
        Example usage:
        `!lovemeter John`
        """
        if name is None:
            await ctx.send("❌ Please enter a name! Example: `!lovemeter John`")
            return
        
        love_percentage = random.randint(1, 100)
        hearts = "❤️" * (love_percentage // 10)
        
        embed = nextcord.Embed(
            title="💘 Love Meter",
            description=f"**{name}** loves you **{love_percentage}%**!\n\n{hearts}",
            color=nextcord.Color.from_rgb(255, 105, 180)
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(is_me)
    async def purge(self, ctx, amount: str = None, day: int = None, month: int = None, year: int = datetime.date.today().year):
        """
        Deletes specific number of messages or messages after a specific date.
        
        Usage:
        1. Delete by number:
           Example: `!purge 10`
           Description: Deletes last 10 messages (excluding command message).
        
        2. Delete by date:
           Example: `!purge / 15 8 2023`
           Description: Deletes messages after August 15, 2023.
        """
        if amount is None:
            await ctx.send(
                "❌ Please enter an amount or use `/` for date.\n"
                "Example: `!purge 10` or `!purge / 15 8 2023`"
            )
            return

        # If using date option
        if amount == "/":
            if day is None or month is None:
                await ctx.send("❌ Please provide complete date information. Example: `!purge / 15 8 2023`")
                return
            cutoff = datetime.datetime(year, month, day)
            deleted = await ctx.channel.purge(after=cutoff)
            confirm_msg = await ctx.send(f"✅ {len(deleted)} messages after {cutoff.strftime('%d/%m/%Y')} were deleted.")
            await asyncio.sleep(3)
            await confirm_msg.delete()
        else:
            try:
                amt = int(amount)
                # Adding +1 to limit because command message is included
                deleted = await ctx.channel.purge(limit=amt+1)
                confirm_msg = await ctx.send(f"✅ Last {len(deleted)-1} messages were deleted.")
                await asyncio.sleep(3)
                await confirm_msg.delete()
            except ValueError:
                await ctx.send("❌ Please enter a valid number or use `/` for date.")

def setup(bot):
    bot.add_cog(Fun(bot))
