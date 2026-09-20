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
The connector is still being built. There is no installable release in this
repository yet.

The first jobs I want to get right:

- **Find the right source.** Tell an approved document from a newer draft.
- **Keep up with changes.** Notice what matters in a project folder and update its brief.
- **Make documents searchable by their facts.** Extract useful fields, review them, and save them as metadata.
- **Track commitments.** Find obligations and deadlines, with the source attached.
- **Finish the work.** Save the result to the right Box folder and verify it arrived.

Every job needs clear permissions, useful errors, and evidence you can check.
Box AI and enterprise administration need their own access and capability checks.

## Bring a real problem

[Open an issue](https://github.com/danieloleary/box-for-muse/issues/new/choose).
Tell us what you need done, what files it involves, and how you'd know it worked.
A small fictional example helps more than a long feature list.

Found a bad assumption or a better approach? Send a correction or pull request.
Please keep customer files, credentials, and private logs out of public contributions.

- [Research and sources](research/SOURCES.md): what Aaron Levie said, what we inferred, and what still needs checking.
- [Build roadmap](ROADMAP.md): what has to work before release.
- [Contributing](CONTRIBUTING.md): how to help.
- [Keeping it current](MAINTENANCE.md): how changes get reviewed.
- [Writing and demo copy](COPY.md): how this project should sound.
- [Use-case data](data/use-cases.json): the catalog in JSON.

The project uses the MIT license. Box and Muse accounts, API charges, and product
entitlements may still be required. The goal is an open connector anyone can
build on, with those requirements explained plainly.

## Check a contribution

```sh
python3 scripts/validate.py
```

This checks the catalog and its references. A working connector needs tests in
Muse too. We'll publish that evidence alongside the implementation.
