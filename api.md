ROUTES
------

- **POST** - Ajouter un personnage à une arène  
  **Route**: `/join`  
  **Paramètres**:  
    - `cid` (string) : ID unique du personnage  
    - `teamid` (string) : ID de l'équipe  
    - `life` (int) : Points de vie du personnage  
    - `strength` (int) : Force du personnage  
    - `armor` (int) : Armure du personnage  
    - `speed` (int) : Vitesse du personnage  

- **POST** - Ajouter une action à un personnage  
  **Route**: `/set_action`  
  **Paramètres**:  
    - `cid` (string) : ID du personnage  
    - `action` (string) : Action à effectuer (peut être "HIT", "BLOCK", "DODGE", "FLY")  
    - `target` (string, optionnel) : ID de la cible si l'action est une attaque ou une interaction avec un autre personnage (nécessaire pour "HIT" et "FLY")  

- **GET** - Récupérer un personnage  
  **Route**: `/character/<cid>`  
  **Paramètres**:  
    - `cid` (string) : ID du personnage dont on veut récupérer les statistiques  

- **GET** - Récupérer tous les personnages d'une arène  
  **Route**: `/characters`  
  **Paramètres**: Aucun  

- **POST** - Ajouter un joueur existant à une arène  
  **Route**: `/add_to_arena`  
  **Paramètres**:  
    - `cid` (string) : ID du personnage à ajouter à l'arène  

- **GET** - Récupérer les résultats des matchs  
  **Route**: `/status`  
  **Paramètres**:  
    - `turn_number` (int) : Numéro du tour pour lequel récupérer le statut des matchs
