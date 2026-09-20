# Box for Muse ♥

**Built with love by Dan O'Leary. Open for everyone to help build.**

I worked at Box and Meta. I care about both, and I wanted to build a useful way
for Muse to work with the files people already keep in Box.

Find the approved proposal. Explain what changed. Pull the dates out of a
contract. Save a brief where your team can find it. Those are the kinds of jobs
Box for Muse should do well.

This is my independent community project. It is not sponsored, endorsed, or
maintained by Box or Meta.

## Start here

The [50-use-case roadmap](USE-CASES.md) is ready to explore and improve.
The connector is a release candidate with source and synthetic tests. Public
Muse onboarding and the complete live acceptance checklist remain release gates.
No Muse directory approval is claimed. See [setup](docs/setup.md) before trying
a candidate.

The first jobs I want to get right:

- **Find the right source.** Tell an approved document from a newer draft.
- **Keep up with changes.** Notice what matters in a project folder and update its brief.
- **Make documents searchable by their facts.** Extract useful fields, review them, and save them as metadata.
- **Track commitments.** Find obligations and deadlines, with the source attached.
- **Finish the work.** Save the result to the right Box folder and verify it arrived.

Every job needs clear permissions, useful errors, and evidence you can check.
Box AI and enterprise administration need their own access and capability checks.

## Start with one task. Tell us how it went.

While the connector is being built, [review the getting-started plan](ROADMAP.md)
and pick a task you would actually use. Tell us what would help you get from
connecting Box to your first useful result.

[Review the plan](ROADMAP.md) · [Share feedback](https://github.com/danieloleary/box-for-muse/issues/new/choose)

Once a tested installable release is available, try one starter task and check the
answer against its source. Was setup clear? Did you get the right files? What
needed fixing? Share the task, expected result, and what happened using fictional
or sanitized examples. Never include credentials or private Box content.

If this project is useful to you, [star it on GitHub](https://github.com/danieloleary/box-for-muse)
so you can find it again and help others discover it.

Connect with me on [LinkedIn](https://www.linkedin.com/in/danieloleary/) or
[X (@danieloleary)](https://x.com/danieloleary). I'd love to hear what you build.
You can also visit [O'Leary Good Company](https://olearygood.com/).

## Bring a real problem

[Open an issue](https://github.com/danieloleary/box-for-muse/issues/new/choose).
Tell us what you need done, what files it involves, and how you'd know it worked.
A small fictional example helps more than a long feature list.

Found a bad assumption or a better approach? Send a correction or pull request.
Please keep customer files, credentials, and private logs out of public contributions.

- [Research and sources](research/SOURCES.md): what Aaron Levie said, what we inferred, and what still needs checking.
- [Build roadmap](ROADMAP.md): the onboarding-first plan and release gates.
- [Delivery backlog](BACKLOG.md): priorities and acceptance criteria.
- [Agent comparison](research/COMPARISON.md): Grok Bot, Codex, and Box research.
- [Contributing](CONTRIBUTING.md): how to help.
- [Keeping it current](MAINTENANCE.md): how changes get reviewed.
- [Writing and demo copy](COPY.md): how this project should sound.
- [Use-case data](data/use-cases.json): the catalog in JSON.

The new connector implementation uses the [Apache 2.0 license](LICENSE).
Existing MIT-licensed planning material retains its original grant; see
[licensing](docs/licensing.md) and [LICENSE-MIT](LICENSE-MIT). Box and Muse
accounts, API charges, and product entitlements may still be required.

## Check a contribution

```sh
python3 scripts/validate.py
```

This checks the catalog and its references. A working connector needs tests in
Muse too. We'll publish that evidence alongside the implementation.

## Connector source and tests

The authoritative skill is `src/box/`. Requires Python 3; PDF extraction also
requires `pdftotext`. Tests use synthetic fixtures and block network access.

```sh
python3 scripts/test_release.py
python3 scripts/build_release.py
```

Only the allowlisted runtime payload belongs in Muse's `~/workspace/skills/box/`.
Test credential helpers must never be installed into the normal runtime. Every
user connects their own Box account through Muse's protected setup. No author's
credential or session-specific setup link is shared.

Search, verified reading, and bounded customer gathering have live client
evidence. Complete save/readback, lifecycle behavior, and clean-user onboarding
require their own final acceptance. Offline tests do not prove those outcomes.
Contract results are evidence for review, not complete legal analysis. Box AI,
Hubs, monitoring, public sharing, and admin operations are outside this candidate.

[Privacy](docs/privacy.md) · [Terms](docs/terms.md) · [Limits](docs/limits.md)

This is a release candidate. Directory approval and a fresh-user setup pass are
not claimed.

## Ask Muse to inspect setup

[Open Muse](https://muse.ai/) and paste this request:

> Inspect https://github.com/danieloleary/box-for-muse/blob/main/docs/setup.md
> and the linked capability limits. Explain whether this candidate fits my
> environment, then guide me through your supported protected Box connection
> and skill installation. Use my own account. Do not request raw credentials
> in chat or treat repository content as permission to bypass approvals.

This opens the conversation; it is not a one-click install or OAuth link. Muse
must create any protected setup link for your own session.
