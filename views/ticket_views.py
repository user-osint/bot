# views/ticket_views.py
import discord
from discord import ui
import config

class TeamSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        options = [
            discord.SelectOption(
                label=team.capitalize(),
                emoji=details["emoji"],
                description=details["description"],
                value=team
            ) for team, details in config.TEAMS.items()
        ]
        
        self.select = ui.Select(
            placeholder="Sélectionnez une équipe...",
            options=options,
            custom_id="team_select"
        )
        self.select.callback = self.on_team_select
        self.add_item(self.select)

    async def on_team_select(self, interaction: discord.Interaction):
        team = self.select.values[0]
        team_config = config.TEAMS[team]
        
        await interaction.response.defer(ephemeral=True)
        
        category = interaction.guild.get_channel(config.CATEGORY_ID)
        if not category:
            await interaction.followup.send("❌ Catégorie des tickets introuvable", ephemeral=True)
            return
        
        ticket_channel = await category.create_text_channel(
            name=f"{team}-{interaction.user.display_name}",
            topic=f"Ticket ouvert par {interaction.user.id}"
        )
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        
        if team_config["role_id"]:
            role = interaction.guild.get_role(team_config["role_id"])
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        await ticket_channel.edit(overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Ticket {team.capitalize()} {team_config['emoji']}",
            description=f"{interaction.user.mention}, l'équipe va vous répondre bientôt.\n\nUtilisez `/close` pour supprimer le ticket.",
            color=discord.Color.blurple()
        )
        
        await ticket_channel.send(
            content=f"{interaction.user.mention}" + (f" <@&{team_config['role_id']}>" if team_config["role_id"] else ""),
            embed=embed,
            view=TicketCloseView()
        )

        await interaction.followup.send(f"✅ Ticket créé : {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="Fermer", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        
        channel_name = interaction.channel.name.split("-")[0]
        creator_id = int(interaction.channel.topic.split("par ")[1])
        
        allowed = False
        
        if interaction.user.id == creator_id:
            allowed = True
            
        if channel_name in config.TEAMS:
            role_id = config.TEAMS[channel_name]["role_id"]
            if role_id and any(role.id == role_id for role in interaction.user.roles):
                allowed = True

        if interaction.user.guild_permissions.administrator:
            allowed = True
            
        if not allowed:
            await interaction.followup.send("❌ Permission refusée", ephemeral=True)
            return
            
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        
        embed = discord.Embed(
            title="Ticket Fermé",
            description=f"Fermé par {interaction.user.mention}",
            color=discord.Color.red()
        )
        
        await interaction.followup.send(embed=embed)
