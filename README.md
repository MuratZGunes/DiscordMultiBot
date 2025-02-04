# Discord Multi Bot

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

![Music Commands](https://i.imgur.com/example1.png)

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

![Giveaway Commands](https://i.imgur.com/example2.png)

### Event Creation Commands 📅
| Command | Description |
|---------|-------------|
| `!createevent <duration> <event name>` | Creates a new event |

Duration format:
- `d`: days
- `h`: hours
- `m`: minutes

Example: `!createevent 1d2h30m Movie Night`

![Event Creation Commands](https://i.imgur.com/example3.png)

## Add the Bot to Your Server

Want to add **Discord Multi Bot** to your server? Click the link below and grant the necessary permissions:

[Add to Discord](https://discord.com/oauth2/authorize?client_id=1334217291679924245&permissions=8&integration_type=0&scope=bot)

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

This means you can:
- Use this software for commercial purposes
- Modify the source code
- Distribute the software
- Patent the software

But you must:
- Include the original source code when you distribute
- Document any changes you make
- Use the same license for any derivative works
- State significant changes made to the software

