# Teraveri reference value registry

This public repository distributes reference values and independently verifiable
publisher statements. The repository is a transport and review record; a verifier
owner decides which publishers and reference versions its policy accepts.

## Entry model

Each `entries/<profile>/<environment>/` directory contains:

- `reference.json`: exact bytes consumed by an evidence verifier.
- `manifest.json`: scope, provenance and SHA-256 of those exact bytes.
- `endorsements/*.sigstore.json`: optional signed publisher statements whose
  subject is the SHA-256 of `manifest.json`. Multiple issuers may sign the same
  manifest without changing it.

The first entry is a **stage candidate**, derived from live Azure Genoa evidence
after a kernel update. Its measurements cover the boot aggregate and 44 kernel
module records. It is not an independently approved production baseline and says
nothing about the application, model, GPU, or later state changes. The candidate
must be reviewed against the intended image/build before promotion.

`python3 tools/validate.py` checks every entry, including paths, digests, scope,
and expected measurement count. Publisher signatures are checked separately by
the consuming verifier owner against locally configured issuer identities. A
GitHub PR or a commit author string alone is not a publisher signature.

## Publishing

1. Add a new entry; do not rewrite an old reference to reflect an OS update.
2. Review and merge the entry through a protected branch. Record the resulting
   full commit ID and the SHA-256 of `manifest.json`.
3. A publisher reviews that exact manifest and issues an attestation from its own
   protected GitHub workflow. Copy the resulting Sigstore bundle into the entry
   through another PR. This second commit leaves the signed manifest unchanged.
4. A verifier owner checks the bundle, pins the registry commit and reference
   digest in its local policy, and performs positive and negative live acceptance.

Revocation or supersession requires a new decision and policy rollout. A verifier
already pinned to an older commit cannot discover a later revocation by itself.

The JSON manifest is deliberately simple for Confido 0.2. A future CoRIM export
can represent Reference Values and Endorsements for Veraison without changing the
original bytes or treating this repository as an automatic trust authority.

Other publishers can add their own signed statements beside the same manifest.
Each consuming verifier owner must explicitly authorize that publisher's
repository, workflow and source branch; publication in this registry alone
grants no trust. The current GENXT statement records manifest authorship and
scope. It is not by itself a CoRIM Endorsement or an approval of all measured
software.
