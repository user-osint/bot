# utils/permissions.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import List

class PermissionManager:
    """Gestion centralisée des permissions pour les commandes du bot."""
    
    def __init__(self):
        # Structure : {nom_commande: [id_rôle1, id_rôle2]}
        self._permissions = {
            'starter': [1258695450211516480],  # Exemple d'ID de rôle
            'modérateur': [1176238735671697500], # Exemple d'ID de rôle Modération
            'admin': [1372659962228248709] # Exemple d'ID de rôle Admin
        }
        
        # Commandes publiques (accessibles à tous)
        self._public_commands = ['ping', 'help', 'spawn', 'action'] # spawn et action sont publiques

    def set_permissions(self, command_name: str, role_ids: List[int]):
        """Modifie les permissions pour une commande."""
        self._permissions[command_name] = role_ids
    
    def is_command_public(self, command_name: str) -> bool:
        """Vérifie si une commande est publique."""
        return command_name in self._public_commands
    
    async def check_permission(self, interaction: discord.Interaction, command_name: str) -> bool:
        """Vérifie si l'utilisateur a la permission pour une commande."""
        # Commandes publiques
        if self.is_command_public(command_name):
            return True
            
        # Commandes protégées
        if command_name in self._permissions:
            user_roles = [role.id for role in interaction.user.roles]
            required_roles = self._permissions[command_name]
            
            # Vérifier si l'utilisateur a au moins un des rôles requis
            if any(role_id in user_roles for role_id in required_roles):
                return True
            
            # Vérifier si l'utilisateur est administrateur du serveur
            if interaction.user.guild_permissions.administrator:
                return True
            
        # Commandes non listées ou permissions insuffisantes
        return False 

perm_manager = PermissionManager()

def permission_check(command_name: str):
    """Décorateur pour vérifier les permissions d'une commande slash."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if await perm_manager.check_permission(interaction, command_name):
            return True

        embed = discord.Embed(
            title="Logs",
            description=f"{interaction.user.mention} a essayé de faire une commande dont il n'avait pas les permissions requises.",
            color=discord.Color.red()
        )    
        # Envoyer le log au canal de logs si configuré
        logs_channel_id = 1389955672984129629 # Remplacez par l'ID de votre canal de logs
        logs = interaction.client.get_channel(logs_channel_id)
        if logs:
            await logs.send(embed=embed)
            # Optionnel: mentionner un rôle d'alerte
            # await logs.send("<@ID_ROLE_ALERTE>")

        await interaction.response.send_message(
            "❌ Permission refusée : vous n'avez pas le rôle requis pour cette commande.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)

# Décorateur pour les commandes de modération (nécessite des permissions Discord)
def mod_command_check(permission_level: str):
    """Décorateur pour vérifier les permissions de modération."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if permission_level == 'moderate_members' and interaction.user.guild_permissions.moderate_members:
            return True
        if permission_level == 'kick_members' and interaction.user.guild_permissions.kick_members:
            return True
        if permission_level == 'ban_members' and interaction.user.guild_permissions.ban_members:
            return True
        if permission_level == 'manage_messages' and interaction.user.guild_permissions.manage_messages:
            return True
        if permission_level == 'manage_roles' and interaction.user.guild_permissions.manage_roles:
            return True
        if permission_level == 'administrator' and interaction.user.guild_permissions.administrator:
            return True
        
        embed = discord.Embed(
            title="Logs",
            description=f"{interaction.user.mention} a essayé d'utiliser une commande de modération sans les permissions Discord requises ({permission_level}).",
            color=discord.Color.red()
        )    
        logs_channel_id = 1389955672984129629
        logs = interaction.client.get_channel(logs_channel_id)
        if logs:
            await logs.send(embed=embed)

        await interaction.response.send_message(
            f"❌ Permission refusée : vous n'avez pas la permission Discord '{permission_level}' pour cette commande.",
            ephemeral=True
        )
        return False
    return app_commands.check(predicate)
