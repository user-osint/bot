# cogs/general.py
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio 
from datetime import datetime, time, timedelta
import config
from utils.permissions import permission_check
from utils.helpers import send_session_update, reconnect_voice_channel
from views.ticket_views import TeamSelectView

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ouvrir", description="Ouvrir une session")
    @permission_check('starter')
    async def ouvrir_session(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await send_session_update(self.bot, "ouvert")
        if result.get("status") == "success":
            await interaction.followup.send("Session ouverte.", ephemeral=True)
        else:
            await interaction.followup.send(f"Erreur: {result.get('message')}", ephemeral=True)

    @app_commands.command(name="fermer", description="Fermer les session")
    @permission_check('starter')
    async def fermer_session(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await send_session_update(self.bot, "fermé")
        if result.get("status") == "success":
            await interaction.followup.send("Session fermée.", ephemeral=True)
        else:
            await interaction.followup.send(f"Erreur: {result.get('message')}", ephemeral=True)

    @app_commands.command(name="relancer", description="Relancer la session")
    @permission_check('starter')
    async def pause_session(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        result = await send_session_update(self.bot, "relancer")
        if result.get("status") == "success":
            await interaction.followup.send("Session relancer.", ephemeral=True)
        else:
            await interaction.followup.send(f"Erreur: {result.get('message')}", ephemeral=True)

    @app_commands.command(name="spawn", description="Commande à faire quand vous êtes au spawn")
    async def spawn(self, interaction: discord.Interaction, pseudo_fortnite: str):
        embed = discord.Embed(
            title="Spawn",
            description=f"Il y a {pseudo_fortnite} au spawn. Son discord est : {interaction.user.mention}",
            color=discord.Color.blue()
        )
        spawn_channel = self.bot.get_channel(config.CHANNEL_IDS[0])
        if spawn_channel:
            await interaction.response.send_message("Message envoyé", ephemeral=True)
            await spawn_channel.send(embed=embed)
        else:
            await interaction.response.send_message("Salon de spawn introuvable.", ephemeral=True)

    @app_commands.command(name="action", description="Faire une action en session")
    async def action(self, interaction: discord.Interaction, action: str):
        embed = discord.Embed(
            title="Action",
            description=f"{interaction.user.mention} est en train de faire : *__{action}__*",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Secure.Contain.Protect.")
        action_channel = self.bot.get_channel(config.CHANNEL_IDS[1])
        if action_channel:
            await interaction.response.send_message("Message envoyé", ephemeral=True)
            await action_channel.send(embed=embed)
        else:
            await interaction.response.send_message("Salon d'action introuvable.", ephemeral=True)

    @commands.command(name='rejoin')
    async def manual_rejoin(self, ctx):
        """Commande manuelle pour forcer la reconnexion au salon vocal"""
        result = await reconnect_voice_channel(self.bot)
        await ctx.send(result.get("message"))

    @app_commands.command(name="add", description="Ajoute au ticket")
    async def add_to_channel(self, interaction: discord.Interaction, member: discord.Member):
        target_channel = interaction.channel
        
        if not target_channel.permissions_for(interaction.user).manage_channels:
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission de gérer ce salon",
                ephemeral=True
            )
            return
        
        try:
            await target_channel.set_permissions(
                member,
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
            
            await interaction.response.send_message(
                f"✅ {member.mention} a été ajouté à {target_channel.mention}",
                ephemeral=False
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas les permissions nécessaires",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Une erreur est survenue: {str(e)}",
                ephemeral=True
            )  

    @app_commands.command(name="ticketsetup", description="Configurer le système de tickets")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Conctater le staff/animation/administration",
            description="Sélectionnez une équipe à contacter :",
            color=discord.Color.green()
        )
        try:
            await interaction.channel.send(embed=embed, view=TeamSelectView())
            await interaction.response.send_message("✅ Système configuré", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas la permission d'envoyer un message ici.", ephemeral=True)
        
    @app_commands.command(name="close", description="Fermer ce ticket")
    @commands.has_permissions(manage_channels=True)
    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith(('ticket-', 'closed-')):
            await interaction.response.send_message("❌ Ceci n'est pas un ticket", ephemeral=True)
            return
        
        try:
            ticket_creator_id = int(interaction.channel.topic.split("par ")[1])
            team_type = interaction.channel.name.split("-")[0]
            
            allowed = (
                interaction.user.id == ticket_creator_id or
                any(role.id == config.TEAMS.get(team_type, {}).get("role_id") for role in interaction.user.roles) or
                interaction.user.guild_permissions.administrator
            )
            
            if not allowed:
                await interaction.response.send_message("❌ Vous n'avez pas la permission de fermer ce ticket", ephemeral=True)
                return
            
            await interaction.response.send_message("✅ Ticket supprimé")
            await interaction.channel.delete()
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur: {str(e)}", ephemeral=True)
            print(f"Erreur fermeture ticket: {e}")

async def setup(bot):
    await bot.add_cog(General(bot))
