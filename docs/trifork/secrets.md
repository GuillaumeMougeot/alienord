# Secrets

The necessary secrets are:

- Bot service account for Google Cloud Storage: `nordfou-biodiversity-2cd0fb3af162.json`. This secret can be fetched from LastPass. Ask jpes to get access.

- Github bot credential: `bot.env` (used for setup `scripts/setup-xnx.sh` in the flashing process). This secret can be from LastPass. Ask jpes to get access.

- Tailscale token: `tailscale.txt`. It needs to be manually generated in tailscale settings:
    - Enable reusable option.
    - Add tailscale device tag.
    - Tailscale does not allow to create an authentication token with no expiration date. Therefore, this secret needs to be updated periodically.

- .env file with:
    - Github user
    - Github token with the following permissions (It probably also works with less, we should look into that): 
        - repo 
        - read:packages 
        - read:org 
        - read:repo_hook 
        - read:project