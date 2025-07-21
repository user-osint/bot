# config.py
import os
from dotenv import load_dotenv
import collections

load_dotenv()

# --- IDs des Canaux et Rôles ---
CHANNEL_IDS = [
    1361646608009265202,  # Premier salon
    1152669498738999397   # Deuxième salon
]

SESSION_CHANNEL_ID = 1360545490944524429
VOICE_CHANNEL_ID = 1202972091750551613

CATEGORY_ID = 1360579920907997365  # ID de la catégorie tickets

MOD_LOG_CHANNEL_ID = int(os.getenv('MOD_LOG_CHANNEL_ID', 1389955672984129629)) # Canal pour les logs de modération
QUARANTINE_ROLE_ID = int(os.getenv('QUARANTINE_ROLE_ID', 0)) # REMPLACEZ PAR L'ID DE VOTRE RÔLE QUARANTAINE

# --- Configuration des Équipes de Tickets ---
TEAMS = {
        "support": {
            "role_id": 1264494975887085628,  # ID du rôle Support
            "emoji": "🛠️",
            "description": "Support"
        },
        "animation": {
            "role_id": 1176238735671697500,  # ID du rôle Modération
            "emoji": "🃏",
            "description": "Equipe animation"
        },
        "administration": {
            "role_id": 1372659962228248709,  # ID du rôle Admin
            "emoji": "👑",
            "description": "Demandes administratives"
        }
    }

# --- Configuration Anti-Spam ---
MESSAGE_HISTORY = collections.defaultdict(lambda: collections.deque(maxlen=5)) # Stocke les 5 derniers messages d'un utilisateur
MENTION_HISTORY = collections.defaultdict(lambda: collections.deque(maxlen=3)) # Stocke les 3 dernières mentions d'un utilisateur
SPAM_THRESHOLD = 3 # Nombre de messages/mentions en peu de temps
SPAM_TIME_WINDOW = 5 # Secondes

# --- Configuration Anti-Nuke ---
NUKE_THRESHOLD_CHANNELS = 5 # Nombre de créations/suppressions de canaux en peu de temps
NUKE_THRESHOLD_ROLES = 3 # Nombre de créations/suppressions de rôles en peu de temps
NUKE_TIME_WINDOW = 10 # Secondes
NUKE_ACTIONS = collections.defaultdict(lambda: collections.deque(maxlen=NUKE_THRESHOLD_CHANNELS)) # Pour les actions de canaux/rôles

# --- Système d'Avertissement ---
warnings = collections.defaultdict(int) # {user_id: warning_points}
WARNING_POINTS_MUTE = 3 # Points pour mute
WARNING_POINTS_KICK = 5 # Points pour kick
WARNING_POINTS_BAN = 7 # Points pour ban

# --- Messages du Bot ---
MESSAGES = [
    "*### > <:Annonce:1192611527400902796> • Rappel, Faites bien la commande «/spawn» pour valider votre présence*",
    "*### > <:Annonce:1192611527400902796> • Rappel, Faites bien la commande «/action» pour votre action RP*"
]

