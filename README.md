A versatile Discord bot that offers various features including music playback, giveaways, and content creation.

## Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/DiscordMultiBot.git
cd DiscordMultiBot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

4. Edit the `.env` file and add your credentials:
```
# Discord Bot Token
DISCORD_TOKEN=your_token_here

# Spotify API Credentials (Required for music features)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
```

5. Run the bot:
```bash
python main.py
```

## Spotify API Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Log in or create an account
3. Click "Create an App"
4. Fill in the application details
5. Copy the generated Client ID and Client Secret to your `.env` file

## Security Guidelines

### API Keys and Tokens
- Never commit your `.env` file to version control
- Keep your bot token and API keys private
- Regularly rotate your API keys and tokens
- Use environment variables for all sensitive data

### Best Practices
- Always use `.env.example` as a template, never with real credentials
- Check your git history to ensure no tokens were accidentally committed
- If you suspect your tokens are compromised, regenerate them immediately
- Keep your dependencies updated to patch security vulnerabilities

### Setting Up Securely
1. Create a new Discord application and bot token for each deployment
2. Use separate Spotify API credentials for development and production
3. Set up proper Discord bot permissions - only request what you need
4. Monitor your bot's usage for any suspicious activity

## Features

- Music playback (YouTube and Spotify support)
- Giveaway system
- Content creation tools
- Game deals tracking (Epic Games and Steam)
- And more...

## Commands

### Music Commands 🎵
| Command | Description |
|---------|-------------|
| `!play <song/url>` | Plays a song or adds it to queue |

![Music Commands](https://github.com/user-attachments/assets/212b7080-43a9-4a52-9ede-5d68362ddf5c)

### Giveaway Commands 🎉
| Command | Description |
|---------|-------------|
| `!giveaway <duration> <prize>` | Starts a new giveaway |

Duration format:
- `s`: seconds
- `m`: minutes
- `h`: hours
- `d`: days

Example: `!giveaway 1h PlayStation 5`

![Giveaway Commands](https://github.com/user-attachments/assets/8aafc146-704e-4fe4-b610-117dfd3e90fc)

### Event Creation Commands 📅
| Command | Description |
|---------|-------------|
| `!createevent <duration> <event name>` | Creates a new event |

Duration format:
- `d`: days
- `h`: hours
- `m`: minutes

Example: `!createevent 1d2h30m Movie Night`

![Event Creation Commands](https://github.com/user-attachments/assets/68d9e6b2-7726-4c92-811f-74f8230b5913)

![Event Creation Commands2](https://github.com/user-attachments/assets/8481a12f-fddd-4e08-95d3-77e7d408fca9)

![Event Creation Commands3](https://github.com/user-attachments/assets/6b3803fe-2641-4d0f-93f2-c5ce131ecbd2)

### Game Deals Commands 🎮
| Command | Description |
|---------|-------------|
| `!gamedeals` or `!deals` | Shows current game deals from Epic Games and Steam |

Features:
- Automatically tracks free games on Epic Games Store
- Lists top discounted games on Steam
- Shows prices in both USD and TRY
- Auto-updates every 24 hours
- Posts updates in dedicated 'game-deals' channel
- Manual command for instant deal checks

Example Output:
```
🎮 Current Game Deals
💰 USD/TRY: 31.50₺
🔄 Updates: Daily
⏰ Last Check: 15:30 06.02.2024

🎁 EPIC - [Game Name]
GET IT FREE
[View on Epic Games Store]

🔥 STEAM - [Game Name]
Discount: 75%
~$59.99~ $14.99 = 472.19₺
[View on Steam]
```

### RPS Commands ✌️
| Command | Description |
|---------|-------------|
| `!playrps` or `!rps_game` | Start a two-player Rock Paper Scissors game |

Game Features:
- Play between two players
- Easy selection with buttons (🪨 Rock, 📄 Paper, ✂️ Scissors)
- Real-time result display with emojis
- Private choice selection for each player
- Play again option after each game
- 60-second timeout for inactive games
- Prevents same player from making multiple choices
- Shows player mentions in results

![image](https://github.com/user-attachments/assets/6f4d2387-728d-4bf8-b549-21371be93c7a)

![image](https://github.com/user-attachments/assets/57cdb58f-89e5-43aa-880f-ef0a6f6d2673)

![image](https://github.com/user-attachments/assets/6bc48f94-3487-4cb1-b71f-4c51130bed2d)

### Translation Commands 🌐
| Command | Description |
|---------|-------------|
| `!translate <target_language> <text>` | Translates text to the specified language |

Features:
- Automatic source language detection
- Support for multiple languages
- Real-time translation
- Detailed output with language names

Examples:
```
!translate spanish Hello, how are you?
!translate japanese Good morning
!translate turkish I love programming
```

Supported Languages:
- 🇬🇧 English (en)
- 🇪🇸 Spanish (es)
- 🇫🇷 French (fr)
- 🇩🇪 German (de)
- 🇯🇵 Japanese (ja)
- 🇨🇳 Chinese (zh)
- 🇰🇷 Korean (ko)
- 🇹🇷 Turkish (tr)
And many more...

### Word Game Commands 🎯
| Command | Description |
|---------|-------------|
| `!kelime` | Shows help message for word game |
| `!kelime başlat` | Starts a new word game |

Game Features:
- Each word forms a chain by starting with the last letter of the previous word
- Turkish dictionary validation through TDK API
- Automatic Turkish character handling
- Used word tracking
- Real-time feedback with reactions
- Persistent game state across bot restarts
- Dedicated game channels with auto-setup
- Multi-server support

Game Rules:
1. Each word must start with the last letter of the previous word
2. Words must be valid Turkish words (checked via TDK dictionary)
3. Words cannot be repeated in the same game
4. No need to use any prefix, just type the word
5. Bot provides instant feedback with reactions

Example Gameplay:
```
Bot: merhaba
Player 1: araba
Player 2: araç
Player 3: çamur
...
```

Channel Setup:
- Create a channel with "kelime-türetme" in its name
- Bot will automatically detect and set it up
- Or use any channel and start the game with `!kelime başlat`

![Ekran görüntüsü 2025-02-10 170346](https://github.com/user-attachments/assets/248ddeba-94e2-4e1d-aac0-479461dc0602)

### Fun Commands 🎮
| Command | Description |
|---------|-------------|
| `!roll [number]` | Rolls a dice (default: 6-sided) |
| `!choose <option1> <option2> ...` | Randomly selects from given options |
| `!flip` | Flips a coin |
| `!joke` | Tells a random joke |
| `!8ball <question>` | Gives Magic 8-ball answers |
| `!cat` | Sends a random cat photo |
| `!dog` | Sends a random dog photo |
| `!fact` | Shares a random interesting fact |
| `!emoji` | Sends a random emoji |
| `!alarm HH:MM` | Sets an alarm for specified time via DM |
| `!lovemeter <name>` | Shows how much the specified person loves you |

Example Usage:
```
!roll 20          # Rolls a 20-sided dice
!choose pizza hamburger pasta  # Randomly selects one
!alarm 14:30      # Sets an alarm for 14:30
!lovemeter John   # Shows how much John loves you
```

## Add the Bot to Your Server

Want to add **Discord Multi Bot** to your server? Click the link below and grant the necessary permissions:

[Add to Discord](https://discord.com/oauth2/authorize?client_id=1334217291679924245&permissions=8&integration_type=0&scope=bot)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---
