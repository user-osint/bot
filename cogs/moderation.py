# cogs/moderation.py
import discord
from discord.ext import commands
from discord import app_commands
import config
from utils.permissions import mod_command_check
from utils.helpers import log_mod_action
from datetime import timedelta
from typing import Optional

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Expulser un membre du serveur.")
    @app_commands.describe(member="Le membre à expulser.", reason="La raison de l'expulsion.")
    @mod_command_check('kick_members')
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie."):
        if member.id == self.bot.user.id:
            await interaction.response.send_message("Je ne peux pas m'expulser moi-même !", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Vous ne pouvez pas expulser un membre ayant un rôle égal ou supérieur au vôtre.", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("Je ne peux pas expulser ce membre car son rôle est égal ou supérieur au mien.", ephemeral=True)
            return

        try:
            await member.kick(reason=reason)
            await log_mod_action(interaction.guild, "Kick", member, interaction.user.display_name, reason)
            await interaction.response.send_message(f"✅ {member.display_name} a été expulsé pour : {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour expulser ce membre.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors de l'expulsion : {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Bannir un membre du serveur.")
    @app_commands.describe(member="Le membre à bannir.", reason="La raison du bannissement.")
    @mod_command_check('ban_members')
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie."):
        if member.id == self.bot.user.id:
            await interaction.response.send_message("Je ne peux pas me bannir moi-même !", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Vous ne pouvez pas bannir un membre ayant un rôle égal ou supérieur au vôtre.", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("Je ne peux pas bannir ce membre car son rôle est égal ou supérieur au mien.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            await log_mod_action(interaction.guild, "Ban", member, interaction.user.display_name, reason)
            await interaction.response.send_message(f"✅ {member.display_name} a été banni pour : {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour bannir ce membre.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors du bannissement : {e}", ephemeral=True)

    @app_commands.command(name="unban", description="Débannir un utilisateur du serveur.")
    @app_commands.describe(user_id="L'ID de l'utilisateur à débannir.", reason="La raison du débannissement.")
    @mod_command_check('ban_members')
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Aucune raison fournie."):
        try:
            user = discord.Object(id=int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await log_mod_action(interaction.guild, "Unban", user, interaction.user.display_name, reason)
            await interaction.response.send_message(f"✅ L'utilisateur avec l'ID {user_id} a été débanni.")
        except discord.NotFound:
            await interaction.response.send_message("Cet utilisateur n'est pas banni ou l'ID est incorrect.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour débannir cet utilisateur.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("L'ID de l'utilisateur doit être un nombre valide.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors du débannissement : {e}", ephemeral=True)

    @app_commands.command(name="mute", description="Mettre un membre en sourdine (timeout).")
    @app_commands.describe(
        member="Le membre à mettre en sourdine.",
        duration="La durée de la mise en sourdine (ex: 1m, 5m, 1h, 1d, 1w). Max 28 jours.",
        reason="La raison de la mise en sourdine."
    )
    @mod_command_check('moderate_members') # Nouvelle permission
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "Aucune raison fournie."):
        if member.id == self.bot.user.id:
            await interaction.response.send_message("Je ne peux pas me mettre en sourdine moi-même !", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Vous ne pouvez pas mettre en sourdine un membre ayant un rôle égal ou supérieur au vôtre.", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("Je ne peux pas mettre en sourdine ce membre car son rôle est égal ou supérieur au mien.", ephemeral=True)
            return
        
        # Parser la durée
        time_unit = duration[-1].lower()
        time_value = int(duration[:-1])
        
        if time_unit == 's':
            delta = timedelta(seconds=time_value)
        elif time_unit == 'm':
            delta = timedelta(minutes=time_value)
        elif time_unit == 'h':
            delta = timedelta(hours=time_value)
        elif time_unit == 'd':
            delta = timedelta(days=time_value)
        elif time_unit == 'w':
            delta = timedelta(weeks=time_value)
        else:
            await interaction.response.send_message("Format de durée invalide. Utilisez (s)econdes, (m)inutes, (h)eures, (d)ays, (w)eeks (ex: 5m, 1h, 7d).", ephemeral=True)
            return

        # Discord limite les timeouts à 28 jours (4 semaines)
        if delta > timedelta(weeks=4):
            await interaction.response.send_message("La durée maximale de mise en sourdine est de 28 jours (4 semaines).", ephemeral=True)
            return

        try:
            await member.timeout_for(delta, reason=reason)
            await log_mod_action(interaction.guild, "Timeout", member, interaction.user.display_name, f"{reason} (Durée: {duration})")
            await interaction.response.send_message(f"✅ {member.display_name} a été mis en sourdine pour {duration} pour : {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas la permission `moderate_members` pour mettre ce membre en sourdine.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors de la mise en sourdine : {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="Retirer la mise en sourdine d'un membre.")
    @app_commands.describe(member="Le membre à retirer de la mise en sourdine.", reason="La raison du retrait.")
    @mod_command_check('moderate_members') # Nouvelle permission
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie."):
        if not member.is_timed_out():
            await interaction.response.send_message(f"{member.display_name} n'est pas actuellement en sourdine.", ephemeral=True)
            return

        try:
            await member.timeout_for(None, reason=reason) # Passer None pour annuler le timeout
            await log_mod_action(interaction.guild, "Untimeout", member, interaction.user.display_name, reason)
            await interaction.response.send_message(f"✅ {member.display_name} n'est plus en sourdine.")
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas la permission `moderate_members` pour retirer la mise en sourdine de ce membre.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors du retrait de la mise en sourdine : {e}", ephemeral=True)

    @app_commands.command(name="clear", description="Supprimer un nombre spécifié de messages.")
    @app_commands.describe(amount="Le nombre de messages à supprimer (max 100).", channel="Le canal où supprimer les messages (par défaut, le canal actuel).")
    @mod_command_check('manage_messages')
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100], channel: Optional[discord.TextChannel] = None):
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message("Vous ne pouvez supprimer des messages que dans un canal textuel.", ephemeral=True)
            return

        try:
            deleted = await target_channel.purge(limit=amount)
            await log_mod_action(interaction.guild, "Clear", interaction.user, interaction.user.display_name, f"{len(deleted)} messages supprimés dans #{target_channel.name}")
            await interaction.response.send_message(f"✅ {len(deleted)} messages supprimés dans {target_channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour supprimer des messages dans ce canal.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors de la suppression des messages : {e}", ephemeral=True)

    @app_commands.command(name="warn", description="Avertir un membre du serveur.")
    @app_commands.describe(member="Le membre à avertir.", reason="La raison de l'avertissement.")
    @mod_command_check('kick_members')
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison fournie."):
        if member.bot:
            await interaction.response.send_message("Vous ne pouvez pas avertir un bot.", ephemeral=True)
            return
        if member.id == interaction.user.id:
            await interaction.response.send_message("Vous ne pouvez pas vous avertir vous-même.", ephemeral=True)
            return
        if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Vous ne pouvez pas avertir un membre ayant un rôle égal ou supérieur au vôtre.", ephemeral=True)
            return

        config.warnings[member.id] += 1
        points = config.warnings[member.id]

        action_taken = "Avertissement"
        try:
            if points >= config.WARNING_POINTS_BAN:
                await member.ban(reason=f"Avertissements cumulés ({points} points): {reason}")
                action_taken = "Ban (cumul d'avertissements)"
                config.warnings.pop(member.id)
            elif points >= config.WARNING_POINTS_KICK:
                await member.kick(reason=f"Avertissements cumulés ({points} points): {reason}")
                action_taken = "Kick (cumul d'avertissements)"
            elif points >= config.WARNING_POINTS_MUTE:
                # Utiliser le timeout pour le mute via avertissement
                await member.timeout_for(timedelta(minutes=10), reason=f"Avertissements cumulés ({points} points): {reason}") # Exemple: 10 min de timeout
                action_taken = "Timeout (cumul d'avertissements)"
            
            await log_mod_action(interaction.guild, action_taken, member, interaction.user.display_name, f"Points: {points} - {reason}")
            
            try:
                await member.send(f"Vous avez été averti sur le serveur {interaction.guild.name} pour la raison suivante : '{reason}'. Vous avez maintenant {points} point(s) d'avertissement.")
            except discord.Forbidden:
                print(f"Impossible d'envoyer un message privé à {member.display_name}.")

            await interaction.response.send_message(f"✅ {member.display_name} a été averti. Points: {points}. Action prise: {action_taken}")
        except discord.Forbidden:
            await interaction.response.send_message("Je n'ai pas les permissions nécessaires pour effectuer cette action.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Une erreur est survenue lors de l'avertissement : {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
