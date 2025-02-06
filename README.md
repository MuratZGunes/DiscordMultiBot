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

### RPS Commands ✌️
| Command | Description |
|---------|-------------|
| `!rps` | Start a two-player Rock Paper Scissors game |

Game Features:
- Play between two players
- Easy selection with buttons
- Real-time result display
- Option to play again

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

## Add the Bot to Your Server

Want to add **Discord Multi Bot** to your server? Click the link below and grant the necessary permissions:

[Add to Discord](https://discord.com/oauth2/authorize?client_id=1334217291679924245&permissions=8&integration_type=0&scope=bot)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---
