# Negative verifier fixtures

These files are test inputs, not enrolled reference values or publisher-endorsed
manifests. The Genoa fixture copies the stage candidate and changes only the
`filedata_hash` of `nf_tables.ko` and `bridge.ko`. It leaves the original
template hashes and PCR 10 value unchanged on purpose: it represents a bounded
measurement mismatch, not a coherent alternative VM image.

Consumers must pin the fixture's exact Git commit and SHA-256 before using it
in a negative test. Do not use it as a positive trust policy.
