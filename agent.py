import random
import time
import requests
import threading

class SimpleAgent:
    def __init__(self, cid, engine_url, available_urls):
        self.cid = cid
        self.engine_url = engine_url
        self.available_urls = available_urls  # Liste des URLs fonctionnelles
        self.current_url = engine_url  # URL où l'agent est actuellement

    def choose_action(self):
        """Choisir une action aléatoire pour l'instant."""
        return random.choice(["HIT", "BLOCK", "DODGE"])

    def choose_target(self, characters):
        """Choisir une cible aléatoire parmi les personnages vivants."""
        # Récupérer uniquement les personnages vivants
        alive_characters = self.get_alive_characters(characters)
        if alive_characters:
            target = random.choice(alive_characters)
            print(f"L'agent {self.cid} cible {target}.")
            return target
        print(f"Aucune cible valide pour l'agent {self.cid}.")
        return None

    def get_alive_characters(self, characters):
        """Récupérer la liste des personnages vivants."""
        alive_characters = []
        for character_id in characters:
            try:
                response = requests.get(f"{self.engine_url}/character/{character_id}")
                if response.status_code == 200:
                    character_data = response.json()
                    if not character_data.get("dead", False):  # Si le personnage n'est pas mort
                        alive_characters.append(character_id)
                else:
                    print(f"Erreur lors de la récupération des infos du personnage {character_id}: {response.text}")
            except Exception as e:
                print(f"Erreur pour vérifier si {character_id} est vivant : {e}")
        return alive_characters

    def is_alive(self):
        """Vérifie si l'agent est vivant en consultant l'API."""
        try:
            response = requests.get(f"{self.engine_url}/character/{self.cid}")
            if response.status_code == 200:
                character = response.json()
                if character.get("dead", False):
                    print(f"Agent {self.cid} est mort et ne peut pas jouer.")
                    return False
                return True
            else:
                return False
        except Exception as e:
            print(f"Erreur lors de la vérification de l'état de l'agent {self.cid}: {e}")
            return False

    def fly_to_another_url(self):
        """Déplacer l'agent vers une autre URL."""
        # Récupérer toutes les URLs sauf l'URL actuelle
        possible_urls = [url for url in self.available_urls if url != self.current_url]

        if not possible_urls:
            print(f"L'agent {self.cid} ne peut pas voler : aucune autre URL disponible.")
            return

        # Choisir une nouvelle URL parmi les possibles
        new_url = random.choice(possible_urls)
        print(f"L'agent {self.cid} tente de se déplacer de {self.current_url} vers {new_url}")

        try:
            # Récupérer les données de l'agent à l'URL actuelle
            response = requests.get(f"{self.current_url}/character/{self.cid}")
            if response.status_code == 200:
                agent_data = response.json()

                # Tenter de rejoindre la nouvelle URL
                join_response = requests.post(f"{new_url}/join", json=agent_data)
                if join_response.status_code == 201:
                    print(f"L'agent {self.cid} a rejoint la nouvelle URL {new_url}.")

                    # Tenter de supprimer l'agent de l'ancienne URL
                    delete_response = requests.delete(f"{self.current_url}/character/{self.cid}")
                    if delete_response.status_code == 200:
                        print(f"L'agent {self.cid} a été supprimé de l'ancienne URL {self.current_url}.")
                        
                        # Ajouter l'ancienne URL dans la liste des disponibles
                        self.available_urls.append(self.current_url)
                        print(f"L'ancienne URL {self.current_url} redevient disponible.")
                        
                        # Mettre à jour l'URL actuelle
                        self.current_url = new_url
                        print(f"Nouvelle URL actuelle pour l'agent {self.cid} : {self.current_url}")

                    else:
                        print(f"Erreur lors de la suppression de l'agent {self.cid} sur {self.current_url}: {delete_response.text}")
                        # Supprimer l'agent de la nouvelle URL pour éviter le dédoublement
                        requests.delete(f"{new_url}/character/{self.cid}")
                else:
                    print(f"Erreur lors de l'ajout de l'agent {self.cid} sur la nouvelle URL {new_url}: {join_response.text}")
            else:
                print(f"Impossible de récupérer les données de l'agent {self.cid} sur {self.current_url}: {response.text}")
        except Exception as e:
            print(f"Erreur lors du déplacement de l'agent {self.cid} : {e}")


        

    def play_turn(self):
        """Envoyer l'action et la cible à l'API distante, si l'agent est vivant."""
        if not self.is_alive():
            return  # Si l'agent est mort, ne pas jouer

        try:
            # Récupérer la liste des personnages disponibles
            response = requests.get(f"{self.engine_url}/characters")
            if response.status_code == 200:
                characters = response.json().get("characters", [])
                if self.cid in characters:
                    characters.remove(self.cid)  # Ne pas cibler soi-même

                # Choisir une action
                action = self.choose_action()

                if action == "FLY":
                    print(f"Agent {self.cid} a choisi l'action {action}.")
                    self.fly_to_another_url()
                else:
                    # Vérifier que la cible est valide avant de l'attaquer
                    target = self.choose_target(characters)

                    if target:
                        # Définir la cible
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
                    else:
                        print(f"L'agent {self.cid} n'a trouvé aucune cible valide.")
                print("------------------------------------------")

        except Exception as e:
            print(f"Erreur pour l'agent {self.cid} : {e}")

    def run(self):
        """Exécuter les tours pour l'agent."""
        while True:
            self.play_turn()
            time.sleep(5)  # Temps d'attente avant le prochain tour


def start_agents_for_available_characters(engine_url, available_urls):
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
                agent = SimpleAgent(cid=cid, engine_url=engine_url, available_urls=available_urls)
                thread = threading.Thread(target=agent.run)
                threads.append(thread)
                thread.start()

            # Attendre la fin de tous les threads
            for thread in threads:
                thread.join()

    except Exception as e:
        print(f"Erreur lors de la récupération des personnages : {e}")
    

available_urls = [
    "http://10.109.111.11:5000",  
    # Ajoutez autant d'URLs que nécessaire
]

# Exemple d'initialisation et démarrage des agents automatiquement
if __name__ == "__main__":
    engine_url = "http://10.109.111.11:5000"  # L'URL de ton serveur API distant (par exemple: http://127.0.0.1:5000)
    start_agents_for_available_characters(engine_url, available_urls)
