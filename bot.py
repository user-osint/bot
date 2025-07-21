# bot.py
import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import time, datetime, timedelta
import config
from views.ticket_views import TeamSelectView, TicketCloseView # Pour ajouter les vues persistantes

load_dotenv()

CHANNEL_IDS = [
    1361646608009265202,  # Premier salon
    1152669498738999397   # Deuxième salon
]
MESSAGES = [
    "# La commande obligatoire est /spawn",
    "# La commande obligatoire est /action"
]

print("Lancement du bot...")
bot = commands.Bot(command_prefix="&", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Bot allumé en tant que {bot.user}")
    
    # Charger les cogs
    if "cogs.general" not in bot.extensions:
        await bot.load_extension("cogs.general")
    else:
        print("L'extension 'cogs.general' est déjà chargée.")
    if "cogs.moderation" not in bot.extensions:
        await bot.load_extension("cogs.moderation")
    else:
        print("L'extension 'cogs.moderation' est déjà chargée.")
        
   
    
    # Charger les événements
    await bot.load_extension("events.anti_raid")

    # Ajouter les vues persistantes (si le bot redémarre)
    bot.add_view(TeamSelectView())
    bot.add_view(TicketCloseView())

    # Mettre à jour la présence du bot
    await bot.change_presence(activity=discord.Game(name="Notre RP préférer : Le site quantum"))
    
    # Synchroniser les commandes slash
    try: 
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes slash : {e}")

    # Envoyer un message de démarrage dans le canal de logs
    start_channel = bot.get_channel(config.MOD_LOG_CHANNEL_ID)
    if start_channel:
        await start_channel.send("Le bot démarre")
    else:
        print(f"Canal de démarrage {config.MOD_LOG_CHANNEL_ID} introuvable.")
        
    if not message_loop.is_running():
            message_loop.start()
            print("La boucle de messages a démarré.")
        
async def send_initial_messages():
    """Envoie les messages immédiatement après le démarrage du bot."""
    if is_working_hours():
        try:
            for channel_id, message in zip(CHANNEL_IDS, MESSAGES):
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(message)
                    print(f"Message envoyé dans {channel.name} à {datetime.now().strftime('%H:%M')}")
                else:
                    print(f"Salon {channel_id} introuvable")
        except Exception as e:
            print(f"Erreur d'envoi : {e}")

def is_working_hours():
    """Vérifie si l'heure actuelle est entre 7h et minuit"""
    now = datetime.now().time()
    return time(8, 20) <= now <= time(23, 59)

@tasks.loop(minutes=120)
async def message_loop():
    if not is_working_hours():
        return
        
    try:
        for channel_id, message in zip(CHANNEL_IDS, MESSAGES):
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(message)
                print(f"Message envoyé dans {channel.name} à {datetime.now().strftime('%H:%M')}")
            else:
                print(f"Salon {channel_id} introuvable")
    except Exception as e:
        print(f"Erreur d'envoi : {e}")

@message_loop.before_loop
async def before_loop():
    await bot.wait_until_ready()
    # Calcule le délai jusqu'à la prochaine demi-heure
    now = datetime.now()
    next_run = now + timedelta(minutes=120)
    next_run = next_run.replace(second=0, microsecond=0)
    wait_seconds = (next_run - now).total_seconds()
    await asyncio.sleep(wait_seconds)

bot.run(os.getenv('DISCORD_TOKEN'))
