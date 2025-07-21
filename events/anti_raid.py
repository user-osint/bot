import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import Optional
import json
import os
import config
from utils.helpers import log_mod_action

AUTHORIZED_USER_ID = 1222261705720205372
WHITELIST_FILE = "whitelist.json"  # Chemin vers le fichier de whitelist

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = set()
        self.load_whitelist_from_file()

    def load_whitelist_from_file(self):
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, "r") as f:
                data = json.load(f)
                self.whitelist = set(data)
                print(f"[AntiRaid] Whitelist chargée ({len(self.whitelist)} utilisateurs)")
        else:
            self.whitelist = set()

    def save_whitelist_to_file(self):
        with open(WHITELIST_FILE, "w") as f:
            json.dump(list(self.whitelist), f)

    whitelist_group = app_commands.Group(
        name="whitelist",
        description="Gestion des whitelist pour l'anti-raid"
    )

    @whitelist_group.command(name="add", description="Ajoute un utilisateur à la whitelist")
    @app_commands.describe(user="L'utilisateur à whitelister")
    async def whitelist_add(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id == AUTHORIZED_USER_ID or interaction.user.guild_permissions.administrator:
            self.whitelist.add(user.id)
            self.save_whitelist_to_file()
            await interaction.response.send_message(
                f"{user.mention} a été ajouté à la whitelist.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True
            )

    @whitelist_group.command(name="remove", description="Retire un utilisateur de la whitelist")
    @app_commands.describe(user="L'utilisateur à retirer")
    async def whitelist_remove(self, interaction: discord.Interaction, user: discord.Member):
        if interaction.user.id == AUTHORIZED_USER_ID or interaction.user.guild_permissions.administrator:
            self.whitelist.discard(user.id)
            self.save_whitelist_to_file()
            await interaction.response.send_message(
                f"{user.mention} a été retiré de la whitelist.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Vous n'avez pas la permission d'utiliser cette commande.", ephemeral=True
            )

    @whitelist_group.command(name="list", description="Affiche la liste whitelist")
    async def whitelist_list(self, interaction: discord.Interaction):
        if not self.whitelist:
            await interaction.response.send_message("La whitelist est vide.", ephemeral=True)
            return

        embed = discord.Embed(title="Liste des utilisateurs whitelistés", color=discord.Color.green())
        for user_id in self.whitelist:
            user = await self.bot.fetch_user(user_id)
            embed.add_field(name=str(user), value=f"ID: {user_id}", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def is_whitelisted(self, member: discord.Member) -> bool:
        return member.id in self.whitelist

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if await self.is_whitelisted(message.author):
            return

        now = datetime.now()
        user_id = message.author.id
        config.MESSAGE_HISTORY[user_id].append(now)

        if len(config.MESSAGE_HISTORY[user_id]) == config.MESSAGE_HISTORY[user_id].maxlen:
            time_diff = (now - config.MESSAGE_HISTORY[user_id][0]).total_seconds()
            if time_diff < config.SPAM_TIME_WINDOW:
                try:
                    await message.delete()
                    if message.guild.me.guild_permissions.moderate_members:
                        await message.author.timeout(timedelta(minutes=1), reason="Spam de messages")
                        await log_mod_action(message.guild, "Timeout (Anti-Spam)", message.author, "Anti-Raid Bot", "Spam de messages détecté.")
                        await message.channel.send(f"{message.author.mention} a été mis en sourdine pour 1 minute pour spam.", delete_after=5)
                except discord.Forbidden:
                    print(f"Impossible de timeout {message.author} pour spam.")

        if message.mentions:
            config.MENTION_HISTORY[user_id].append(now)
            if len(config.MENTION_HISTORY[user_id]) == config.MENTION_HISTORY[user_id].maxlen:
                time_diff = (now - config.MENTION_HISTORY[user_id][0]).total_seconds()
                if time_diff < config.SPAM_TIME_WINDOW:
                    try:
                        await message.delete()
                        if message.guild.me.guild_permissions.moderate_members:
                            await message.author.timeout(timedelta(minutes=5), reason="Spam de mentions")
                            await log_mod_action(message.guild, "Timeout (Anti-Mentions)", message.author, "Anti-Raid Bot", "Spam de mentions détecté.")
                            await message.channel.send(f"{message.author.mention} a été mis en sourdine pour 5 minutes pour spam de mentions.", delete_after=5)
                    except discord.Forbidden:
                        print(f"Impossible de timeout {message.author} pour spam de mentions.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        account_age = datetime.utcnow() - member.created_at
        if account_age < timedelta(days=7):
            quarantine_role = member.guild.get_role(config.QUARANTINE_ROLE_ID)
            if quarantine_role:
                try:
                    await member.add_roles(quarantine_role, reason="Nouveau compte suspect")
                    await log_mod_action(member.guild, "Quarantaine", member, "Anti-Raid Bot", f"Compte créé il y a {account_age.days} jours.")
                except discord.Forbidden:
                    print(f"Impossible d'ajouter le rôle à {member.display_name}.")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.check_nuke_action(channel.guild, None, "channel_create")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.check_nuke_action(channel.guild, None, "channel_delete")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self.check_nuke_action(role.guild, None, "role_create")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.check_nuke_action(role.guild, None, "role_delete")

    async def check_nuke_action(self, guild: discord.Guild, actor: Optional[discord.User], action_type: str):
        # Récupérer l'auteur si non fourni
        if actor is None:
            if "channel_create" in action_type:
                log_action = discord.AuditLogAction.channel_create
            elif "channel_delete" in action_type:
                log_action = discord.AuditLogAction.channel_delete
            elif "role_create" in action_type:
                log_action = discord.AuditLogAction.role_create
            elif "role_delete" in action_type:
                log_action = discord.AuditLogAction.role_delete
            else:
                return

            try:
                async for entry in guild.audit_logs(limit=1, action=log_action):
                    actor = entry.user
                    break
            except discord.Forbidden:
                print("Impossible de lire les logs d'audit.")
                return

        if not actor or actor.bot or actor.id in self.whitelist:
            return

        now = datetime.now()
        actor_id = actor.id
        action_key = f"{actor_id}-{action_type}"
        config.NUKE_ACTIONS[action_key].append(now)

        threshold = config.NUKE_THRESHOLD_CHANNELS if "channel" in action_type else config.NUKE_THRESHOLD_ROLES

        if len(config.NUKE_ACTIONS[action_key]) >= threshold:
            time_diff = (now - config.NUKE_ACTIONS[action_key][0]).total_seconds()
            if time_diff < config.NUKE_TIME_WINDOW:
                await log_mod_action(guild, "ANTI-NUKE ALERTE", actor, "Anti-Raid Bot", f"{len(config.NUKE_ACTIONS[action_key])} actions suspectes en {time_diff:.2f}s.")

                member = guild.get_member(actor_id)
                if member and member.guild_permissions.administrator:
                    try:
                        roles_to_remove = [role for role in member.roles if role.id != guild.id]
                        await member.remove_roles(*roles_to_remove, reason="Détection Anti-Nuke")
                        await log_mod_action(guild, "ANTI-NUKE ACTION", actor, "Anti-Raid Bot", "Rôles administratifs supprimés.")
                    except discord.Forbidden:
                        await log_mod_action(guild, "ANTI-NUKE ÉCHEC", actor, "Anti-Raid Bot", "Impossible de retirer les rôles.")

                config.NUKE_ACTIONS[action_key].clear()

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
