from flask import Flask, jsonify, request, render_template, abort
import json
from character import *
from engine import *
from arena import *
from http import *
import http.client


app = Flask(__name__)

# Fonctions utilitaires
@app.route('/')
def index():
    return "Home page"

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
        
        # Ajouter le personnage à l'arène via l'Engine
        engine.addPlayer(character, request.remote_addr)
        
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
        character.setTarget(target)

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

        # Retourner une réponse de succès
        return jsonify({"message": f"Le personnage '{cid}' a choisi l'action '{action}'."}), 200

    except Exception as e:
        # Gérer les erreurs
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Récupérer les résultats d'un match pour un tour spécifique."""
    try:
        # Récupérer le numéro de tour à partir des paramètres de la requête
        turn_number = request.args.get('turn_number', type=int)

        # Vérifier si un tour est spécifié
        if turn_number is None:
            return jsonify({"error": "Le numéro du tour est requis."}), 400

        # Vérifier si le tour spécifié existe dans l'historique de l'arène
        if turn_number not in engine._history:
            return jsonify({"error": f"Le tour {turn_number} n'existe pas."}), 404

        # Récupérer l'état de l'arène pour ce tour spécifique
        arena_state = engine._history[turn_number]
        
        # Retourner l'état de l'arène sous forme JSON
        return jsonify(arena_state), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start', methods=['POST'])
def start_game():
    """Démarrer le moteur de jeu."""
    try:
        # Vérifier si le moteur de jeu est déjà en cours
        if engine.isRunning():
            return jsonify({"error": "Le jeu est déjà en cours."}), 400
        
        # Lancer le moteur de jeu
        engine.run()  # Appel à la méthode run() pour démarrer le jeu

        return jsonify({"message": "Le jeu a démarré avec succès."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Démarrer le serveur
if __name__ == '__main__':
    engine = Engine()
    app.run(host="0.0.0.0",debug=True)
    engine.run()
