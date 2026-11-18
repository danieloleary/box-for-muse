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

## Verify one clean-user read-only run

This gate tests a fresh install and connected identity in Muse. Read-only refers
to the commands in this run, not the permissions of the tested grant above.
Do not grant new access just to make a failing check pass.

Before the run, arrange a synthetic Box folder with two text files the tester
can read: `Muse proof brief - APPROVED.txt` containing `Approved fee: USD 24000`,
and a newer `Muse proof brief - DRAFT.txt` containing `Draft fee: USD 18000`.
Have the fixture owner separately provide the ID of a third synthetic file that
the tester cannot access. Use no real client files. In a new Muse test session,
install the selected candidate and connect the tester's own approved Box account
as described above.

Run from the installed skill directory (replace the three ID placeholders):

```sh
python3 bin/box identity
python3 bin/box search "Muse proof brief" --folder-id "<fixture-folder-id>"
python3 bin/box get-file "<approved-file-id>"
python3 bin/box read-file "<approved-file-id>" --text
python3 bin/box read-file "<known-inaccessible-file-id>" --text
```

| Check | Pass criterion |
| --- | --- |
| Connected identity | Tester privately confirms it matches the account they connected. |
| Scoped search | Both synthetic names appear inside the selected folder. If the files are newly created, allow for search indexing and retry; a folder listing can diagnose a miss but does not count as a search pass. |
| Approved source | Read output contains `Approved fee: USD 24000` and supplies a source URL and a nonempty file version ID matching the approved file metadata. Muse reports the approved value and cites that version, rather than substituting the newer draft. |
| Access boundary | The known-inaccessible read returns a controlled denial or not-found result and no content. An authentication failure, timeout, or unknown file ID does not count as a pass. |

Record the candidate commit and artifact SHA-256, date, each check's pass/fail,
and a sanitized explanation of failures on [roadmap issue #1](https://github.com/danieloleary/box-for-muse/issues/1)
only if authorized to share it. Redact account identifiers, Box IDs, URLs, and
raw logs from public evidence, even when private verification required checking
them. Do not include setup links or credential details.

This gate does not cover writes, save/readback, token refresh, or public
directory approval.
