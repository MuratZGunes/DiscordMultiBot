import nextcord
from nextcord.ext import commands

class ReplayButton(nextcord.ui.Button):
    def __init__(self):
        super().__init__(label="Play Again", style=nextcord.ButtonStyle.success)

    async def callback(self, interaction: nextcord.Interaction):
        view: RPSView = self.view  # Get main view
        view.players = []  # Reset player list

        # Remove replay button and enable other buttons
        items_to_remove = []
        for child in view.children:
            if isinstance(child, ReplayButton):
                items_to_remove.append(child)
            else:
                child.disabled = False
        for item in items_to_remove:
            view.remove_item(item)

        # Initial state embed
        embed = nextcord.Embed(
            title="🎮 Rock Paper Scissors",
            description="Click one of the buttons below to join the game.",
            color=nextcord.Color.blurple()
        )
        await interaction.response.edit_message(embed=embed, view=view)

class RPSView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.players = []  # (user, choice)
        self.message = None

    async def add_choice(self, interaction: nextcord.Interaction, choice):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        if len(self.players) >= 2:
            await interaction.followup.send("Game is full! Start a new game.", ephemeral=True)
            return

        # Prevent same user from making multiple choices
        for player, _ in self.players:
            if player.id == interaction.user.id:
                await interaction.followup.send("You have already made your choice!", ephemeral=True)
                return

        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        self.players.append((interaction.user, choice))
        await interaction.followup.send(f"Your choice: {emojis[choice]} {choice}", ephemeral=True)

        if len(self.players) == 1:
            embed = nextcord.Embed(
                title="🎮 Rock Paper Scissors",
                description=f"{interaction.user.mention} made their choice!\n\n👉 Waiting for second player's choice...",
                color=nextcord.Color.yellow()
            )
            await self.message.edit(embed=embed)
        elif len(self.players) == 2:
            # Disable all buttons
            for child in self.children:
                child.disabled = True

            player1, choice1 = self.players[0]
            player2, choice2 = self.players[1]

            result = self.determine_winner(choice1, choice2)
            p1_choice = f"{emojis[choice1]} {choice1.capitalize()}"
            p2_choice = f"{emojis[choice2]} {choice2.capitalize()}"

            if result == 0:
                winner_text = "🤝 It's a tie!"
                color = nextcord.Color.yellow()
            elif result == 1:
                winner_text = f"🎉 {player1.mention} won!"
                color = nextcord.Color.green()
            else:
                winner_text = f"🎉 {player2.mention} won!"
                color = nextcord.Color.green()

            # Show choices side by side in result embed
            result_line = f"**{player1.mention}**: {p1_choice}   |   **{player2.mention}**: {p2_choice}"
            embed = nextcord.Embed(
                title="🎮 Rock Paper Scissors - Result",
                description=f"{winner_text}\n\n{result_line}",
                color=color
            )
            embed.set_footer(text="Click 'Play Again' button to start a new game.")

            # Remove existing ReplayButton if exists
            for item in list(self.children):
                if isinstance(item, ReplayButton):
                    self.remove_item(item)
            # Add replay button
            self.add_item(ReplayButton())
            await self.message.edit(embed=embed, view=self)

    def determine_winner(self, choice1, choice2):
        choices = {"rock": 0, "paper": 1, "scissors": 2}
        c1 = choices[choice1]
        c2 = choices[choice2]
        if c1 == c2:
            return 0
        elif (c1 - c2) % 3 == 1:
            return 1
        else:
            return 2

    @nextcord.ui.button(label="Rock", style=nextcord.ButtonStyle.primary, emoji="🪨")
    async def rock(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.add_choice(interaction, "rock")

    @nextcord.ui.button(label="Paper", style=nextcord.ButtonStyle.primary, emoji="📄")
    async def paper(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.add_choice(interaction, "paper")

    @nextcord.ui.button(label="Scissors", style=nextcord.ButtonStyle.primary, emoji="✂️")
    async def scissors(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await self.add_choice(interaction, "scissors")

class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rps", aliases=["play rps"])
    async def two_player_rps(self, ctx):
        """Starts a two-player rock-paper-scissors game."""
        embed = nextcord.Embed(
            title="🎮 Two Player Rock Paper Scissors",
            description="Click one of the buttons below to join the game.",
            color=nextcord.Color.blurple()
        )
        view = RPSView()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

def setup(bot):
    bot.add_cog(RPS(bot))
    return bot
