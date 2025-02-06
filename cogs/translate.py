import nextcord
from nextcord.ext import commands
import aiohttp
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException
from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES
from datetime import datetime
from langdetect import detect

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Map language codes to their English names
        self.language_names = {
            'en': 'English', 'fr': 'French', 'de': 'German', 'es': 'Spanish',
            'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'pl': 'Polish',
            'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese',
            'ar': 'Arabic', 'tr': 'Turkish', 'el': 'Greek', 'vi': 'Vietnamese'
        }

    def get_language_name(self, code):
        return self.language_names.get(code.lower(), code)

    def get_language_code(self, language):
        # Use GOOGLE_LANGUAGES_TO_CODES to find the language code
        language = language.lower()
        for lang, code in GOOGLE_LANGUAGES_TO_CODES.items():
            if lang.lower() == language or code.lower() == language:
                return code
        return None

    @commands.command(name="translate")
    async def translate(self, ctx, target_lang: str = None, *, text: str = None):
        """Translates text to the specified language.
        Usage: !translate [target_language] [text]
        Example: !translate spanish Hello, how are you?"""
        
        if target_lang is None or text is None:
            help_embed = nextcord.Embed(
                title="🌍 How to Use Translation Command?",
                description="This command allows you to translate text into different languages!",
                color=nextcord.Color.blue()
            )
            
            help_embed.add_field(
                name="📝 Basic Usage",
                value="```!translate [target_language] [text_to_translate]```",
                inline=False
            )
            
            help_embed.add_field(
                name="✨ Example Usage",
                value=(
                    "```!translate french Hello, how are you?\n"
                    "!translate spanish I love programming\n"
                    "!translate japanese Good morning\n"
                    "!translate german What's your name?```"
                ),
                inline=False
            )
            
            help_embed.add_field(
                name="🗣️ Popular Language Codes",
                value=(
                    "🇬🇧 English: `english` or `en`\n"
                    "🇪🇸 Spanish: `spanish` or `es`\n"
                    "🇫🇷 French: `french` or `fr`\n"
                    "🇩🇪 German: `german` or `de`\n"
                    "🇯🇵 Japanese: `japanese` or `ja`\n"
                    "🇨🇳 Chinese: `chinese` or `zh`\n"
                    "🇰🇷 Korean: `korean` or `ko`\n"
                    "🇹🇷 Turkish: `turkish` or `tr`"
                ),
                inline=False
            )
            
            help_embed.add_field(
                name="💡 Tips",
                value=(
                    "• Source language is automatically detected!\n"
                    "• You can use language names (`spanish`, `french` etc.)\n"
                    "• You can use language codes (`es`, `fr` etc.)\n"
                    "• Case-insensitive input is supported"
                ),
                inline=False
            )
            
            help_embed.set_footer(text="🤔 For more language codes: https://cloud.google.com/translate/docs/languages")
            await ctx.send(embed=help_embed)
            return

        # Find target language code
        target_code = self.get_language_code(target_lang)
        if not target_code:
            await ctx.send(f"❌ Error: '{target_lang}' is not a supported language.")
            return

        try:
            async with ctx.typing():
                # Detect source language
                detected_lang = detect(text)
                
                # Perform translation
                translator = GoogleTranslator(source='auto', target=target_code)
                translated_text = translator.translate(text)
                
                source_lang_name = self.get_language_name(detected_lang)
                target_lang_name = self.get_language_name(target_code)
                
                embed = nextcord.Embed(
                    title="🌐 Translation Result",
                    color=nextcord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(name=f"📝 Original Text ({source_lang_name})", value=f"```{text}```", inline=False)
                embed.add_field(name=f"🔄 Translation ({target_lang_name})", value=f"```{translated_text}```", inline=False)
                embed.set_footer(text=f"Requested by: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
                
                await ctx.send(embed=embed)

        except Exception as e:
            error_embed = nextcord.Embed(
                title="❌ Error!",
                description=f"An error occurred during translation: {str(e)}",
                color=nextcord.Color.red()
            )
            await ctx.send(embed=error_embed)

def setup(bot):
    bot.add_cog(Translate(bot))
    return bot 