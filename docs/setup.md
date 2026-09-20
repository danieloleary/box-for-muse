# Set up Box for Muse

This procedure targets Muse's workspace, not your Mac. Public directory setup
compatibility and a clean second-user installation remain release gates.

## Connect your own account

1. Use a Box User/OAuth app and register the exact redirect URI:
   `https://agent.meta.ai/api/hatch/oauth/callback`.
2. Ask Muse to connect Box through its supported protected OAuth setup for
   provider `box`, using the Box authorization and token endpoints and the
   intended scopes. The credential appears as `custom.box`.
3. Enter client credentials only on Muse's protected setup page and complete
   your own Box consent. Never put them in a prompt, repository, or support issue.

Authorization endpoint: `https://account.box.com/api/oauth2/authorize`.
Token endpoint: `https://api.box.com/oauth2/token`.
Authenticated API hosts: `api.box.com` and `upload.box.com`.
The tested grant is `root_readwrite`, which is broad within your account access.

No universal setup URL is included. A setup link must be created by Muse for the
connecting user through its supported credential service. Do not reuse or publish
an author's session-specific link. Directory-provided setup remains unverified.

## Install the skill

1. Verify the selected artifact's hash and manifest from the release you intend
   to install. Preserve the previous installation for rollback.
2. Install only the artifact's `box/` directory at `~/workspace/skills/box/` in
   Muse. Preserve executable permissions on `bin/box` and `bin/boxwork`.
3. Confirm the runtime supplies Python 3 and the credential helper at
   `/opt/hatch/skills/skill-creator/bin/dynamic_credentials.py`.
   PDF extraction additionally requires `pdftotext`.
4. From the skill directory, run `python3 bin/box identity` using your own grant,
   then test a folder you selected before requesting a broader workflow.

Do not install `tests/`, test-only `sitecustomize.py`, or credential stubs into the
runtime path. Follow Muse's approval controls. Do not automatically reconnect,
reset, or revoke a grant in response to a 401 or 403.
