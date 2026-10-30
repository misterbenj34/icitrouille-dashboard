# icitrouille-dashboard
Dashboard d'évolution d'Ici-Trouille (agrégats publics, mis à jour automatiquement).

Page statique (GitHub Pages) qui reprend le tableau « Évolution » d'icitrouille.fr :
maisons cumulées, nouvelles maisons par jour, navigation sur 14 jours.

- `scripts/collect.py` lit les endpoints publics `/api/houses` et `/api/recap` et écrit `data.json`.
- `scripts/update.sh` lance le collecteur et ne pousse que si les agrégats ont changé.
- `index.html` lit `data.json`.

## Limites

- Pas de date de création dans l'API publique : chaque maison est datée par `updatedAt`
  (jour Europe/Paris). Une maison modifiée plus tard se déplace donc dans le temps.
- Seuls des agrégats sont publiés. Aucune adresse, ID ni coordonnée n'est écrit dans le repo.
