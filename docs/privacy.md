# Privacy and data handling

Effective September 20, 2026. Applies to this community connector and its project support. Maintainer:
Dan O'Leary, independent developer of Box for Muse.

## Connector data flow

Depending on your request, the connector retrieves account identity, file and
folder metadata, and selected content from Box. It runs inside your Muse
workspace using Muse's protected credential service. Queries, document excerpts,
downloaded files, and generated artifacts can appear in your Muse conversation
or workspace. Writes send your selected content to the named Box destination.

The connector has no separate maintainer-hosted backend, search index, or
telemetry service. This does not mean zero retention: Box and Muse operate their
own services and may retain content according to their terms, policies, and
account controls. The connector does not define or guarantee their retention
periods, deletion outcomes, or compliance status.

## Credentials and permissions

Connect your own Box account through Muse's protected flow. Never post raw
credentials in chat or support issues. The connector uses Muse's credential
helper; the script does not manage real refresh tokens or client secrets.
The tested `root_readwrite` grant is broad within the account's Box permissions,
not limited to one selected folder. Folder choices limit the task, not the OAuth
grant. Muse runtime approval controls remain in effect.

Downloaded copies do not retain Box-hosted access, watermark, or retention
controls as enforcement in the local workspace. Consider your organization's
policies before requesting downloads or generated copies.

## Repository and support information

The project site and support route use GitHub. GitHub operates those
services under its own policies. If you open an issue, its title, body, attachments,
and account identity may be public and visible to the maintainer and other users.
Submit only non-sensitive, redacted information. No private support inbox or
separate support database is operated by this connector.

The maintainer has not established an automatic issue-retention or deletion
schedule. GitHub's own controls apply to account and issue data. Ask about
non-sensitive project-data handling through the repository's support route;
do not include the private content you want removed in a public report.

## Your controls

Use Box and Muse's supported controls to manage the connection and stored content.
Disconnecting a grant is different from deleting downloaded files or conversation
history. This package does not automatically revoke or reconnect access after a
failure. Use GitHub's controls for information you post there.

Support: https://github.com/danieloleary/box-for-muse/issues

This policy describes the community connector. It does not replace Box, Muse, or GitHub policies or claim Muse directory approval.
