import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv  # .env dosyasını okumak için
import asyncio
import traceback  # Added for error details

# .env dosyasını yükle
load_dotenv()

# Required permissions
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True  # Required for voice channel activities

# Bot object
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print('------')
    
    # Default status message (e.g., with watching type)
    await bot.change_presence(activity=nextcord.Activity(
        type=nextcord.ActivityType.watching,
        name="Try !play and !help commands"
    ))
    
    # Automatic loading of extensions
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Extension {filename} loaded!')
            except Exception as e:
                print(f'❌ Failed to load extension {filename}!')
                print(f'Error: {str(e)}')
                print('Error details:')
                traceback.print_exc()

# Event triggered when a user joins a voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    # If user is joining a voice channel
    if before.channel is None and after.channel is not None:
        # If the user is boosting the server (premium_since is not None)
        if member.premium_since is not None:
            # Capitalize the first letter of the username
            name = member.name.capitalize()
            new_status = f"Welcome {name}"
            # Update status message (using nextcord.Game might show as "playing")
            await bot.change_presence(activity=nextcord.Game(name=new_status))
            print(f"Status updated: {new_status}")
            
            # Wait for 10 seconds
            await asyncio.sleep(10)
            
            # Return to default activity
            await bot.change_presence(activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="Try !play and !help commands"
            ))

# Run the bot
TOKEN = os.getenv('DISCORD_TOKEN')  # Token'ı .env get from file
if not TOKEN:
    raise ValueError("Please define the DISCORD_TOKEN variable in the .env file!")
    
bot.run(TOKEN) 