import random
import time
import requests
import threading

class SimpleAgent:
    def __init__(self, cid, engine_url):
        self.cid = cid
        self.engine_url = engine_url

    def choose_action(self):
        """Choisir une action aléatoire pour l'instant."""
        return random.choice(["HIT"])

    def choose_target(self, characters):
        """Choisir une cible aléatoire."""
        if characters:
            return random.choice(characters)
        return None

    def play_turn(self):
        """Envoyer l'action et la cible à l'API distante."""
        try:
            # Récupérer la liste des personnages disponibles
            response = requests.get(f"{self.engine_url}/characters")
            if response.status_code == 200:
                characters = response.json().get("characters", [])
                if self.cid in characters:
                    characters.remove(self.cid)  # Ne pas cibler soi-même

            # Choisir une action et une cible
            action = self.choose_action()
            target = self.choose_target(characters)

            # Définir la cible
            if target:
                target_response = requests.post(f"{self.engine_url}/set_target", json={
                    "cid": self.cid,
                    "target_id": target
                })
                if target_response.status_code == 200:
                    print(f"Agent {self.cid} a ciblé {target}.")
                else:
                    print(f"Erreur lors du ciblage pour {self.cid} vers {target}: {target_response.text}")

            # Définir l'action
            action_response = requests.post(f"{self.engine_url}/set_action", json={
                "cid": self.cid,
                "action": action
            })
            if action_response.status_code == 200:
                print(f"Agent {self.cid} a choisi l'action {action}.")
            else:
                print(f"Erreur lors de l'action pour {self.cid}: {action_response.text}")

        except Exception as e:
            print(f"Erreur pour l'agent {self.cid} : {e}")

    def run(self):
        """Exécuter les tours pour l'agent."""
        while True:
            self.play_turn()
            time.sleep(1)  # Temps d'attente avant le prochain tour


def start_agents_for_available_characters(engine_url):
    """Démarrer des agents pour chaque personnage disponible automatiquement."""
    try:
        # Récupérer la liste des personnages disponibles depuis l'API distante
        response = requests.get(f"{engine_url}/characters")
        if response.status_code == 200:
            characters = response.json().get("characters", [])
            if not characters:
                print("Aucun personnage disponible dans l'arène.")
                return

            print(f"Personnages disponibles : {characters}")

            # Lancer un agent pour chaque personnage disponible sur un serveur distant
            threads = []
            for cid in characters:
                agent = SimpleAgent(cid=cid, engine_url=engine_url)
                thread = threading.Thread(target=agent.run)
                threads.append(thread)
                thread.start()

            # Attendre la fin de tous les threads
            for thread in threads:
                thread.join()

    except Exception as e:
        print(f"Erreur lors de la récupération des personnages : {e}")


# Exemple d'initialisation et démarrage des agents automatiquement
if __name__ == "__main__":
    engine_url = "http://10.109.111.12:5000"  # L'URL de ton serveur API distant (par exemple: http://127.0.0.1:5000)
    start_agents_for_available_characters(engine_url)
