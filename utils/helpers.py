# utils/helpers.py
import discord
from datetime import datetime
import config

async def log_mod_action(guild: discord.Guild, action: str, target: discord.User, moderator: str, reason: str = "Aucune raison fournie"):
    """Envoie un log d'action de modération dans le canal de logs."""
    log_channel = guild.get_channel(config.MOD_LOG_CHANNEL_ID)
    if not log_channel:
        print(f"Canal de logs de modération {config.MOD_LOG_CHANNEL_ID} introuvable.")
        return

    embed = discord.Embed(
        title=f"Action de Modération : {action}",
        color=discord.Color.red() if action in ["Ban", "Kick", "Mute"] else discord.Color.orange()
    )
    embed.add_field(name="Cible", value=f"{target.mention} ({target.id})", inline=False)
    embed.add_field(name="Modérateur", value=moderator, inline=False)
    embed.add_field(name="Raison", value=reason, inline=False)
    embed.timestamp = datetime.utcnow()

    try:
        await log_channel.send(embed=embed)
    except discord.Forbidden:
        print(f"Permissions insuffisantes pour envoyer des logs dans {log_channel.name}.")
    except Exception as e:
        print(f"Erreur lors de l'envoi du log de modération : {e}")

async def get_user_guild_roles(user_id: int, guild_id: int, bot_instance: discord.Client) -> list[int]:
    """Récupère les IDs des rôles d'un utilisateur dans un serveur donné."""
    guild = bot_instance.get_guild(guild_id)
    if not guild:
        print(f"Guilde {guild_id} introuvable pour la vérification des permissions.")
        return []
    member = guild.get_member(user_id)
    if not member:
        try:
            member = await guild.fetch_member(user_id)
        except discord.NotFound:
            print(f"Membre {user_id} introuvable dans la guilde {guild_id}.")
            return []
        except discord.Forbidden:
            print(f"Permissions insuffisantes pour fetch le membre {user_id} dans la guilde {guild_id}.")
            return []
    if member:
        return [role.id for role in member.roles]
    return []

async def reconnect_voice_channel(bot_instance: discord.Client):
    """Rejoint automatiquement le salon vocal configuré"""
    try:
        voice_channel = bot_instance.get_channel(config.VOICE_CHANNEL_ID)
        
        if not voice_channel:
            print("❌ Salon vocal introuvable - Vérifiez l'ID")
            return {"status": "error", "message": "Salon vocal introuvable - Vérifiez l'ID"}
            
        # Déconnecter si déjà connecté
        if bot_instance.voice_clients:
            for vc in bot_instance.voice_clients:
                if vc.channel.id == config.VOICE_CHANNEL_ID:
                    await vc.disconnect()
                    break
        
        voice_client = await voice_channel.connect()
        print(f"🔊 Connecté au salon vocal : {voice_channel.name}")
        return {"status": "success", "message": f"Connecté au salon vocal : {voice_channel.name}"}
        
    except Exception as e:
        print(f"❌ Erreur de connexion vocale : {str(e)}")
        return {"status": "error", "message": f"Erreur de connexion vocale : {str(e)}"}

async def send_session_update(bot_instance: discord.Client, status: str):
    """Envoie un message de mise à jour de session."""
    session_channel = bot_instance.get_channel(config.SESSION_CHANNEL_ID)
    if not session_channel:
        return {"status": "error", "message": "Canal de session introuvable."}

    embed = discord.Embed()
    guild = session_channel.guild
    icon_url = guild.icon.with_size(1024).with_format('png').url if guild.icon else None

    if status == "ouvert":
        embed.title = "Session ouverte"
        embed.description = "### Venez nous rejoindre"
        embed.color = discord.Color.green()
        embed.add_field(name="Code de la map", value="> --> Pour rejoindre le serveur il vous suffit de vous rendre sur Fortnite et de taper le code de l'ile. Le code --> __3708-1276-7647__", inline=False)
        embed.add_field(name="Statut", value="> Le statut est ouvert Signifie que vous pouvez directement rejoindre pour profiter du RP juste en rejoignant le serveur. Bonne session !", inline=False)
    elif status == "fermé":
        embed.title = "Session fermée"
        embed.description = "### Le serveur est fermé il n'est plus possible de rejoindre jusqu'à la prochaine ouverture."
        embed.color = discord.Color.red()
        embed.add_field(name="Code de la map", value="> A la prochaine ouverture il vous suffit de vous rendre sur Fortnite et de taper le code de l'ile. Le code --> __3708-1276-7647__", inline=False)
        embed.add_field(name="Statut", value="> Le statut : fermé ❌ Signifie qu'il n'y a plus de RP. On se retrouve pour une prochaine session bonne journée !", inline=False)
    elif status == "relancer":
        embed.title = "Session en relancement"
        embed.description = "### Le serveur est en train d'être relance"
        embed.color = discord.Color.yellow()
        embed.add_field(name="Code de la map", value="> Pour rejoindre la nouvelle session il vous suffit de vous rendre sur Fortnite et de taper le code de l'ile. Le code --> __3708-1276-7647__", inline=False)
        embed.add_field(name="Statut", value="> Le statut : en relancement. Signifie qu'il y a une nouvelle session donc quitter l'ancienne et rejoignez nous!", inline=False)
    else:
        return {"status": "error", "message": "Statut de session inconnu."}

    embed.set_footer(text="Secure.Contain.Protect.")
    if icon_url:
        embed.set_thumbnail(url=icon_url)

    try:
        messages_to_delete = []
        async for message in session_channel.history(limit=2):
            if (discord.utils.utcnow() - message.created_at).days < 14:
                messages_to_delete.append(message)
        if messages_to_delete:
            await session_channel.delete_messages(messages_to_delete)

        await session_channel.send("@everyone")
        await session_channel.send(embed=embed)
        return {"status": "success", "message": f"Session mise à jour vers '{status}'."}
    except discord.Forbidden:
        return {"status": "error", "message": "Je n'ai pas la permission d'envoyer/supprimer des messages dans ce canal."}
    except Exception as e:
        return {"status": "error", "message": f"Erreur lors de la mise à jour de la session: {str(e)}"}
