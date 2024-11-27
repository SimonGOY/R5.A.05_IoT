from flask import Flask, jsonify, request, render_template, abort
import json
from character import *
from engine import *
from arena import *
from http import *
import http.client
import threading
import requests
import random
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import prometheus_client
from prometheus_flask_exporter import PrometheusMetrics
from threading import Lock


app = Flask(__name__)

# Fonctions utilitaires
@app.route('/')
def index():
    return "Home page"

# ---------------------------------- Metrics ----------------------------------
# Créer des métriques
total_characters = Counter('total_characters', 'Nombre total de personnages ajoutés')
active_games = Gauge('active_games', 'Nombre de jeux actifs')
turn_duration = Histogram('turn_duration', 'Durée des tours', buckets=[0.1, 0.5, 1, 2, 5, 10])

# Metrics pour les personnages
character_life = Gauge('character_life', 'Vie des personnages', ['cid', 'teamid'])
character_strength = Gauge('character_strength', 'Force des personnages', ['cid', 'teamid'])
character_armor = Gauge('character_armor', 'Armure des personnages', ['cid', 'teamid'])
character_speed = Gauge('character_speed', 'Vitesse des personnages', ['cid', 'teamid'])

# Initialiser PrometheusMetrics
metrics = PrometheusMetrics(app)

# Configurez les métriques de requêtes HTTP
metrics.register_default(
    metrics.counter('http_requests_total', 'Total HTTP requests', labels={'method': lambda: request.method, 'endpoint': lambda: request.path})
)

@app.route('/metrics')
def metrics_endpoint():
    update_character_metrics()
    """Exposer les métriques Prometheus."""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

# --------------------------------- Utility Functions -------------------------
def update_character_metrics():
    """Met à jour les métriques des personnages, et ignore celles des personnages morts."""
    active_characters = engine._arena._playersList  # Liste des personnages actifs

    # Parcourir tous les personnages dans l'arène
    for character in active_characters:
        cid = character.getId()
        teamid = character._teamid

        # Mettre à jour les métriques pour les personnages vivants
        character_life.labels(cid=cid, teamid=teamid).set(character.getLife())
        character_strength.labels(cid=cid, teamid=teamid).set(character.getStrength())
        character_armor.labels(cid=cid, teamid=teamid).set(character.getArmor())
        character_speed.labels(cid=cid, teamid=teamid).set(character.getSpeed())
        print("Je passe bien là")

# ---------------------------------- Routes ----------------------------------

@app.route('/join', methods=['POST'])
def join_arena():
    """Crée un personnage et l'ajoute directement à l'arène."""
    data = request.json  # Récupérer les données JSON envoyées dans la requête

    # Vérifier que toutes les statistiques nécessaires sont présentes
    required_fields = ["cid", "teamid", "life", "strength", "armor", "speed"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Les statistiques du personnage sont incomplètes."}), 400

    # Extraire les données du personnage
    cid = data["cid"]
    teamid = data["teamid"]
    life = data["life"]
    strength = data["strength"]
    armor = data["armor"]
    speed = data["speed"]

    # Vérifier que la somme des statistiques est inférieure ou égale à 20
    if strength + speed + life + armor > 20:
        return jsonify({"error": "La somme des statistiques ne peut pas dépasser 20."}), 400
    if speed > 10:
        return jsonify({"error": "La vitesse ne peut pas dépasser 10."}), 400

    # Créer le personnage
    try:
        # Créer le personnage avec les caractéristiques données
        character = CharacterProxy(cid, teamid, life, strength, armor, speed)
        print(character)
        # Ajouter le personnage à l'arène via l'Engine
        engine.addPlayer(character, request.remote_addr)

        total_characters.inc()
        update_character_metrics()
        
        # Retourner une réponse de succès
        return jsonify({"message": f"Le personnage '{cid}' a été créé et ajouté à l'arène avec succès."}), 201
    except Exception as e:
        # Gérer les erreurs
        return jsonify({"error": str(e)}), 500

@app.route('/characters', methods=['GET'])
def get_characters():
    """Renvoie tous les IDs des personnages présents dans l'arène."""
    try:
        # Extraire les IDs des personnages depuis l'arène via `engine`
        character_ids = [character.getId() for character in engine._arena._playersList]
        return jsonify({"characters": character_ids}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/character/<cid>', methods=['GET'])
def get_character(cid):
    """Renvoie les statistiques d'un joueur donné à partir de son ID."""
    try:
        # Chercher le personnage dans l'arène via son ID
        character = next((char for char in engine._arena._playersList if char.isId(cid)), None)
        
        if character is None:
            return jsonify({"error": f"Personnage avec l'ID '{cid}' introuvable."}), 404

        # Retourner les statistiques du personnage
        return jsonify(character.toDict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/active_players', methods=['GET'])
def get_active_players():
    """Récupère la liste des joueurs actifs dans l'arène."""
    try:
        active_players = engine._arena.getActiveNbPlayer()
        return jsonify({"active_players": active_players}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500   

@app.route('/is_ready_for_next_turn', methods=['GET'])
def is_ready_for_next_turn():
    """Vérifie si tous les joueurs sont prêts pour un nouveau tour."""
    try:
        if engine.isReady():
            return jsonify({"message": "Tous les joueurs sont prêts pour le prochain tour."}), 200
        else:
            return jsonify({"error": "Tous les joueurs ne sont pas prêts."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_target', methods=['POST'])
def set_target():
    """Permet à un personnage de choisir une cible."""
    try:
        # Récupérer les données du joueur et de la cible depuis la requête
        data = request.json

        # Vérifier que l'ID du personnage et de la cible sont présents
        required_fields = ["cid", "target_id"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Les IDs du personnage et de la cible sont manquants."}), 400

        cid = data["cid"]
        target_id = data["target_id"]

        # Trouver le personnage avec l'ID donné
        character = next((char for char in engine._arena._playersList if char.isId(cid)), None)
        if character is None:
            return jsonify({"error": f"Personnage avec l'ID '{cid}' introuvable."}), 404

        # Trouver la cible avec l'ID donné
        target = next((char for char in engine._arena._playersList if char.isId(target_id)), None)
        if target is None:
            return jsonify({"error": f"Personnage avec l'ID '{target_id}' introuvable."}), 404

        # Définir la cible pour le personnage
        character.setTarget(target_id)

        # Appliquer la mise à jour dans l'arène
        engine.setTargetTo(cid, target_id)

        # Retourner une réponse de succès
        return jsonify({"message": f"Le personnage '{cid}' a maintenant '{target_id}' comme cible."}), 200

    except Exception as e:
        # Gérer les erreurs
        return jsonify({"error": str(e)}), 500



@app.route('/set_action', methods=['POST'])
def set_action():
    """Permet à un personnage de définir une action."""
    try:

        # Récupérer les données du joueur et de l'action depuis la requête
        data = request.json

        # Vérifier que l'ID du personnage et l'action sont présents
        required_fields = ["cid", "action"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "L'ID du personnage et l'action sont manquants."}), 400

        cid = data["cid"]
        action = data["action"]

        # Vérifier que l'action est valide (ex: HIT, BLOCK, DODGE, FLY)
        valid_actions = ["HIT", "BLOCK", "DODGE", "FLY"]
        if action not in valid_actions:
            return jsonify({"error": f"L'action '{action}' n'est pas valide."}), 400

        # Trouver le personnage avec l'ID donné
        character = next((char for char in engine._arena._playersList if char.isId(cid)), None)
        if character is None:
            return jsonify({"error": f"Personnage avec l'ID '{cid}' introuvable."}), 404

        # Définir l'action pour le personnage
        if action == "HIT":
            character.setAction(ACTION.HIT)
        elif action == "BLOCK":
            character.setAction(ACTION.BLOCK)
        elif action == "DODGE":
            character.setAction(ACTION.DODGE)
        elif action == "FLY":
            character.setAction(ACTION.FLY)

        # Appliquer l'action et mettre à jour l'état du personnage
        engine.setActionTo(cid, character.getAction())

        # Retourner une réponse de succès
        return jsonify({"message": f"Le personnage '{cid}' a choisi l'action '{action}'."}), 200

    except Exception as e:
        # Gérer les erreurs
        return jsonify({"error": str(e)}), 500


    
@app.route('/start')
def start_game():
    """Démarrer le moteur de jeu."""
    try:
        # Vérifier si le moteur de jeu est déjà en cours
        if engine.isRunning():
            return jsonify({"error": "Le jeu est déjà en cours."}), 400

        # Ajouter un log avant de démarrer le thread
        print("Démarrage du jeu dans un thread séparé")
        x = threading.Thread(target=run_game)
        x.start()

        return jsonify({"message": "Le jeu a démarré avec succès."}), 200

    except Exception as e:
        print(f"Erreur lors du démarrage du jeu : {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/stop')
def stop_game():
    try:
        if not engine.isRunning():
            return jsonify({"error": " le jeu n'est pas en cours."}),400
        
        engine.stop()

        return jsonify({"message": "Le jeu à stopper avec succès."}),200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_random_characters')
def add_random_characters():
    """Ajoute 5 personnages avec des statistiques aléatoires à l'arène."""
    try:
        characters_added = []
        for i in range(5):
            # Générer un ID unique pour chaque personnage
            cid = f"Random-{random.randint(1, 500)}"

            # Générer les statistiques aléatoires
            stats = {"life": 0, "strength": 0, "armor": 0, "speed": 0}
            remaining_points = 20

            stats["life"] = random.randint(1, 19)
            remaining_points -= stats["life"]

            for stat in stats:
                if stat == "life":
                    continue  # Ne pas modifier la vie puisque nous l'avons déjà définie

                if stat == "speed":
                    # Limiter la vitesse à un maximum de 10
                    max_value = min(10, remaining_points)
                else:
                    max_value = remaining_points

                # Répartir aléatoirement les points restants
                value = random.randint(0, max_value)
                stats[stat] = value
                remaining_points -= value

            # Générer un `teamid` aléatoire (par exemple, "Team A" ou "Team B")
            teamid = f"Team {random.choice(['A', 'B'])}"

            # Créer les données du personnage
            character_data = {
                "cid": cid,
                "teamid": teamid,
                "life": stats["life"],
                "strength": stats["strength"],
                "armor": stats["armor"],
                "speed": stats["speed"]
            }

            # Ajouter le personnage via l'API /join
            response = requests.post("http://localhost:5000/join", json=character_data)

            if response.status_code == 201:
                characters_added.append(character_data)
            else:
                return jsonify({
                    "error": f"Échec lors de l'ajout du personnage '{cid}'.",
                    "details": response.json()
                }), 500

        return jsonify({
            "message": "5 personnages aléatoires ont été ajoutés avec succès.",
            "characters": characters_added
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/leave', methods=['DELETE'])
def leave_arena():
    """Supprime un personnage de l'arène."""
    data = request.json  # Récupérer les données JSON envoyées dans la requête

    # Vérifier que le cid est bien présent dans la requête
    if "cid" not in data:
        return jsonify({"error": "Le 'cid' du personnage est manquant."}), 400

    # Extraire le cid du personnage
    cid = data["cid"]

    
    # Vérifier si le personnage existe (par exemple, via l'Engine ou la base de données)
    character = engine.getPlayerByName(cid)  
    print(character, "delete")
    if not character:
        return jsonify({"error": f"Le personnage '{cid}' n'existe pas."}), 404
    
    # Supprimer le personnage de l'arène
    engine._arena.removePlayer(character)  
    
    #total_characters.dec()  

    # Retourner une réponse de succès
    return jsonify({"message": f"Le personnage '{cid}' a été supprimé de l'arène avec succès."}), 200

def run_game():
    while not engine.isReadyToStart():
        time.sleep(1)
    try:
        if engine.isReady():
            if not engine.isRunning():
                engine.run()

    except Exception as e:
        print(f"Erreur dans run_game : {str(e)}")

# ----------------------------------- Démarrage ----------------------------------

if __name__ == '__main__':
    # Initialise le moteur
    engine = Engine()

    # Lancer le serveur Flask dans un thread pour permettre les requêtes HTTP
    app.run(host="0.0.0.0",debug=True)