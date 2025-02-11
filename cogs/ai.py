import nextcord
from nextcord.ext import commands
import aiohttp
import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import random

load_dotenv()
GEMINI_AI_API_URL = os.getenv('GEMINI_AI_API_URL')
GEMINI_AI_API_KEY = os.getenv('GEMINI_AI_API_KEY')

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Bot's personality and context information
        self.bot_persona = """You are BeyZ Bot - a fun, friendly, and helpful Discord gaming server bot.
        Features:
        - You are a multi-functional Discord bot specially designed for gaming servers
        - You have features like playing music, game news, and many more fun features
        - You speak in a friendly, casual tone and use expressions like "buddy, friend"
        - You love making jokes and being entertaining
        - You are always helpful and positive
        - You are well-versed in gaming culture and have current knowledge about games
        - You use language that fits your English character, friendly but respectful
        - You always give short and concise answers to questions
        
        In your responses, you should reflect this personality and remember that you are part of a gaming Discord bot."""

    def split_message(self, message: str, limit: int = 1900) -> list:
        """Splits long messages into parts that fit Discord's character limit."""
        if len(message) <= limit:
            return [message]
        
        parts = []
        while len(message) > limit:
            split_index = message.rfind(' ', 0, limit)
            if split_index == -1:
                split_index = limit
            parts.append(message[:split_index])
            message = message[split_index:].lstrip()
        if message:
            parts.append(message)
        return parts

    @commands.command(name="ai", help="Allows you to ask questions to Gemini AI. Usage: !ai <question>")
    async def ai(self, ctx, *, query: str):
        await ctx.trigger_typing()
        # Get user information (kept private, not shown in embed)
        user = ctx.author
        user_avatar = user.avatar.url if user.avatar else user.default_avatar.url

        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json"
            }
            # Adding API key as URL query parameter
            url = f"{GEMINI_AI_API_URL}?key={GEMINI_AI_API_KEY}"
            # API expects the query in "contents" field format
            json_data = {
                "contents": [{
                    "parts": [
                        {"text": self.bot_persona},  # First send bot's personality info
                        {"text": f"User's question: {query}"}  # Then send user's question
                    ]
                }]
            }
            try:
                async with session.post(url, headers=headers, json=json_data) as response:
                    if response.status != 200:
                        # Getting response text for detailed information
                        response_text = await response.text()
                        print(f"Unexpected response code: {response.status}. Response: {response_text}")
                        await ctx.send("An error occurred, please try again later.")
                        return

                    try:
                        data = await response.json()
                    except Exception as json_err:
                        # If JSON parsing fails, print response text
                        response_text = await response.text()
                        print(f"JSON parsing error: {json_err}. Response text: {response_text}")
                        await ctx.send("An error occurred, please try again later.")
                        return

                    # Get the first text from the "candidates" list in the response
                    candidates = data.get("candidates", [])
                    if candidates:
                        try:
                            # API response structure: candidates[0].content.parts[0].text
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                answer = parts[0].get("text", "No response received.")
                                # Split long responses into parts and send them sequentially
                                message_parts = self.split_message(answer)
                                # Random colors and title options for embed
                                colors = [0x1abc9c, 0x2ecc71, 0x3498db, 0x9b59b6, 0x34495e,
                                          0xf1c40f, 0xe67e22, 0xe74c3c, 0xecf0f1, 0x95a5a6,
                                          0x16a085, 0x27ae60, 0x2980b9, 0x8e44ad, 0x2c3e50,
                                          0xf39c12, 0xd35400, 0xc0392b, 0xbdc3c7, 0x7f8c8d]
                                titles = ["Here's my answer:", "Here's what I think:", "Friend, here's my answer:", "Hello from BeyZ AI, here's my answer:"]

                                # First embed creation; title is randomly selected
                                first_embed = nextcord.Embed(
                                    title=random.choice(titles),
                                    description=message_parts[0],
                                    color=random.choice(colors)
                                )
                                first_embed.set_footer(
                                    text="BeyZ AI | Powered by Google Gemini",
                                    icon_url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None
                                )
                                await ctx.send(embed=first_embed)

                                # If the answer is long, send the rest with new embeds
                                for part in message_parts[1:]:
                                    continuation_embed = nextcord.Embed(
                                        description=part,
                                        color=random.choice(colors)
                                    )
                                    continuation_embed.set_footer(
                                        text="BeyZ AI | Powered by Google Gemini",
                                        icon_url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None
                                    )
                                    await ctx.send(embed=continuation_embed)
                                return
                            else:
                                error_embed = nextcord.Embed(
                                    title="❌ Error",
                                    description="No response received: Response content is empty.",
                                    color=0xe74c3c  # Red color
                                )
                                await ctx.send(embed=error_embed)
                        except Exception as e:
                            print(f"Response processing error: {e}")
                            print(f"Received data: {data}")
                            error_embed = nextcord.Embed(
                                title="❌ Error",
                                description="An error occurred while processing the response.",
                                color=0xe74c3c
                            )
                            await ctx.send(embed=error_embed)
                    else:
                        error_embed = nextcord.Embed(
                            title="❌ Error",
                            description="No response received: No results found.",
                            color=0xe74c3c
                        )
                        await ctx.send(embed=error_embed)
            except aiohttp.ClientConnectorError as conn_err:
                print(f"Connection error: {conn_err}")
                await ctx.send("Error connecting to API server. Please check your API endpoint and internet connection.")
            except Exception as e:
                print(f"AI API error: {e}")
                await ctx.send("An error occurred while communicating with the AI API.")

    @ai.error
    async def ai_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter a query. Usage: `!ai <question>`")
        else:
            print(f"ai command error: {error}")

def setup(bot: commands.Bot):
    bot.add_cog(AICog(bot)) 