# Mode veille — tout couper, et rallumer

## Ce qui tourne tout seul dans ce dépôt : rien

Le workflow `rendu.yml` n'a **qu'un seul déclencheur** : `workflow_dispatch`
(le bouton « Run workflow »). Il n'y a :

- aucun `on: push` → pousser du code ne lance rien ;
- aucun `on: schedule` → aucun cron, rien qui se réveille la nuit ;
- aucun `on: pull_request`, aucun webhook, aucune app, aucune intégration ;
- `concurrency: cancel-in-progress` → deux lancements ne peuvent pas tourner en double ;
- `timeout-minutes: 20` par job → rien ne peut tourner indéfiniment.

**Un dépôt poussé et jamais touché consomme 0 minute.** Le dépôt seul ne « tourne » pas :
c'est du stockage de texte (716 Ko).

## Couper complètement (interrupteur général)

Désactive Actions au niveau du dépôt : même le bouton disparaît.

```bash
gh api -X PUT repos/<toi>/rendu-2d/actions/permissions -F enabled=false
```

Ou : **Settings → Actions → General → Disable actions**.

## Rallumer

```bash
gh api -X PUT repos/<toi>/rendu-2d/actions/permissions -F enabled=true -f allowed_actions=all
```

Ou : **Settings → Actions → General → Allow all actions**.

Rien n'est perdu entre les deux : le code et le workflow restent en place.

## Annuler un rendu en cours

```bash
gh run list --limit 5
gh run cancel <id>
```

## Vider le stockage (utile en dépôt privé : 500 Mo offerts)

```bash
gh api repos/<toi>/rendu-2d/actions/artifacts --jq '.artifacts[] | "\(.id) \(.name) \(.size_in_bytes)"'
gh api -X DELETE repos/<toi>/rendu-2d/actions/artifacts/<id>
```

Les artifacts expirent déjà seuls : 1 jour pour les segments, 7 jours pour la vidéo finale.

## Voir ce qui a été consommé

```bash
gh api /users/<toi>/settings/billing/actions      # minutes du mois
```

Ou : **Settings du compte → Billing and licensing → Plans and usage**.
