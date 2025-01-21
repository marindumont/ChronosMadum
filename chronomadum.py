import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta, timezone
from discord import app_commands

# Charger le token depuis un fichier externe
def load_token():
    with open("token.txt", "r") as file:
        return file.read().strip()

TOKEN = load_token()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionnaires pour les timers
timers = {}  # Dictionnaire des timers actifs : {nom: {"time_left": seconds, "paused": bool}}
timer_history = []  # Historique des timers terminés
utc_offset = timezone.utc  # Fuseau horaire par défaut (UTC)

# Dictionnaire pour stocker les dernières demandes par utilisateur
dernieres_demandes = {}

# Dictionnaire des icônes pour chaque mois
MOIS_ICONES = {
    "janvier": "❄️", "février": "💝", "mars": "🌱", 
    "avril": "🌸", "mai": "🌼", "juin": "☀️", 
    "juillet": "🏖️", "août": "🍉", "septembre": "🍂", 
    "octobre": "🎃", "novembre": "🦃", "décembre": "🎄"
}

# Liste des mois pour les choix
MOIS = [
    app_commands.Choice(name="Janvier", value="janvier"),
    app_commands.Choice(name="Février", value="février"),
    app_commands.Choice(name="Mars", value="mars"),
    app_commands.Choice(name="Avril", value="avril"),
    app_commands.Choice(name="Mai", value="mai"),
    app_commands.Choice(name="Juin", value="juin"),
    app_commands.Choice(name="Juillet", value="juillet"),
    app_commands.Choice(name="Août", value="août"),
    app_commands.Choice(name="Septembre", value="septembre"),
    app_commands.Choice(name="Octobre", value="octobre"),
    app_commands.Choice(name="Novembre", value="novembre"),
    app_commands.Choice(name="Décembre", value="décembre")
]

@bot.event
async def on_ready():
    print(f'{bot.user} est prêt et connecté !')

# Commande slash : Gestion des mois en jeu
@bot.tree.command(name="chronosmadum_calendar", description="Indiquer le mois actuel en jeu et le mois souhaité.")
@app_commands.describe(
    mois_actuel="Le mois actuel dans le jeu.",
    mois_suivant="Le mois dans lequel vous souhaitez.",
    mention="Mentionnez une personne ou un rôle."
)
@app_commands.choices(
    mois_actuel=MOIS,
    mois_suivant=MOIS
)
async def chronosmadum_calendar(
    interaction: discord.Interaction,
    mois_actuel: app_commands.Choice[str],
    mois_suivant: app_commands.Choice[str],
    mention: str
):
    global dernieres_demandes

    # Réponse initiale différée pour éviter le délai dépassé
    await interaction.response.defer()

    # Stocker la dernière demande pour cet utilisateur
    dernieres_demandes[interaction.user.id] = {
        "user": interaction.user.display_name,
        "mois_actuel": mois_actuel.value,
        "mois_suivant": mois_suivant.value,
        "mention": mention
    }

    # Récupérer les icônes pour les mois
    icone_mois_actuel = MOIS_ICONES.get(mois_actuel.value, "📅")
    icone_mois_suivant = MOIS_ICONES.get(mois_suivant.value, "📅")

    # Définir une icône dynamique pour le titre
    titre_icone = f"{icone_mois_actuel} ➡️ {icone_mois_suivant}"

    # Création de l'embed pour l'affichage
    embed = discord.Embed(
        title=f"{titre_icone} Gestion des mois en jeu",
        description=(
            f"Nous sommes actuellement en {icone_mois_actuel} **{mois_actuel.value}**.\n"
            f"Je souhaite être en {icone_mois_suivant} **{mois_suivant.value}** pour avancer {mention}."
        ),
        color=0x00FF00  # Couleur verte
    )
    embed.set_footer(text=f"Demande faite par {interaction.user.display_name}")

    # Modifier la réponse initiale avec l'embed final
    await interaction.followup.send(embed=embed)

# Commande slash : Dernière demande d'un utilisateur
@bot.tree.command(name="chronosmadum_last_request", description="Afficher la dernière demande d'un utilisateur.")
@app_commands.describe(
    utilisateur="L'utilisateur pour lequel afficher la dernière demande."
)
async def chronosmadum_last_request(interaction: discord.Interaction, utilisateur: discord.Member):
    global dernieres_demandes

    if utilisateur.id not in dernieres_demandes:
        await interaction.response.send_message(f"Aucune demande trouvée pour {utilisateur.display_name}.", ephemeral=True)
        return

    demande = dernieres_demandes[utilisateur.id]
    embed = discord.Embed(
        title=f"📜 Dernière demande de {demande['user']}",
        description=(
            f"**Mois actuel** : {demande['mois_actuel']}\n"
            f"**Mois souhaité** : {demande['mois_suivant']}\n"
            f"**Mention** : {demande['mention']}"
        ),
        color=0xFF5733
    )
    await interaction.response.send_message(embed=embed)

# Commandes slash pour les timers
@bot.tree.command(name="chronosmadum_timer", description="Lancer un timer avec une durée spécifique.")
@app_commands.describe(
    heures="Durée en heures.",
    minutes="Durée en minutes.",
    secondes="Durée en secondes.",
    nom="Nom unique du timer."
)
async def chronosmadum_timer(interaction: discord.Interaction, heures: int, minutes: int, secondes: int, nom: str):
    total_seconds = heures * 3600 + minutes * 60 + secondes
    timers[nom] = {"time_left": total_seconds, "paused": False}
    await interaction.response.send_message(f"Timer '{nom}' lancé pour {heures}h {minutes}m {secondes}s.")

@bot.tree.command(name="chronosmadum_timer_pause", description="Mettre un timer actif en pause.")
async def chronosmadum_timer_pause(interaction: discord.Interaction, nom: str):
    if nom in timers:
        timers[nom]["paused"] = True
        await interaction.response.send_message(f"Timer '{nom}' mis en pause.")
    else:
        await interaction.response.send_message(f"Aucun timer nommé '{nom}' trouvé.", ephemeral=True)

@bot.tree.command(name="chronosmadum_timer_resume", description="Reprendre un timer en pause.")
async def chronosmadum_timer_resume(interaction: discord.Interaction, nom: str):
    if nom in timers and timers[nom]["paused"]:
        timers[nom]["paused"] = False
        await interaction.response.send_message(f"Timer '{nom}' repris.")
    else:
        await interaction.response.send_message(f"Aucun timer en pause nommé '{nom}' trouvé.", ephemeral=True)

@bot.tree.command(name="chronosmadum_timer_stop", description="Arrêter un timer actif.")
async def chronosmadum_timer_stop(interaction: discord.Interaction, nom: str):
    if nom in timers:
        del timers[nom]
        await interaction.response.send_message(f"Timer '{nom}' arrêté.")
    else:
        await interaction.response.send_message(f"Aucun timer nommé '{nom}' trouvé.", ephemeral=True)

@bot.tree.command(name="chronosmadum_timer_list", description="Afficher la liste des timers actifs.")
async def chronosmadum_timer_list(interaction: discord.Interaction):
    if not timers:
        await interaction.response.send_message("Aucun timer actif actuellement.")
    else:
        response = "**⏳ Timers actifs :**\n"
        for nom, data in timers.items():
            status = "En pause" if data["paused"] else "Actif"
            response += f"- `{nom}` : {status}\n"
        await interaction.response.send_message(response)

@bot.tree.command(name="chronosmadum_timer_history", description="Afficher l'historique des timers terminés.")
async def chronosmadum_timer_history(interaction: discord.Interaction):
    if not timer_history:
        await interaction.response.send_message("Aucun historique disponible.")
    else:
        response = "**📜 Historique des timers terminés :**\n"
        for entry in timer_history:
            response += f"- `{entry['name']}` terminé à {entry['timestamp']}\n"
        await interaction.response.send_message(response)

@bot.tree.command(name="chronosmadum_set_timezone", description="Configurer un décalage horaire.")
async def chronosmadum_set_timezone(interaction: discord.Interaction, offset: int):
    global utc_offset
    utc_offset = timezone(timedelta(hours=offset))
    await interaction.response.send_message(f"Fuseau horaire configuré sur UTC{offset:+}.")

# Commande slash : Aide pour le bot
@bot.tree.command(name="chronosmadum_help", description="Afficher l'aide pour les commandes.")
async def chronosmadum_help(interaction: discord.Interaction):
    help_message = """
    **chronosmadum : Liste des commandes disponibles**
    - `/chronosmadum_calendar` : Gestion des mois en jeu.
    - `/chronosmadum_last_request` : Dernière demande enregistrée.
    - `/chronosmadum_timer` : Lancer un timer.
    - `/chronosmadum_timer_pause` : Mettre un timer en pause.
    - `/chronosmadum_timer_resume` : Reprendre un timer en pause.
    - `/chronosmadum_timer_stop` : Arrêter un timer.
    - `/chronosmadum_timer_list` : Liste des timers actifs.
    - `/chronosmadum_timer_history` : Historique des timers terminés.
    - `/chronosmadum_set_timezone` : Configurer un fuseau horaire.
    - `/chronosmadum_help` : Liste des commandes.
    """
    await interaction.response.send_message(help_message)

@bot.event
async def setup_hook():
    await bot.tree.sync()
    print("Commandes synchronisées.")

bot.run(TOKEN)
