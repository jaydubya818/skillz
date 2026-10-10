# PR 7 retarget and disclosure review

Owner authorization retargeted PR #7 to `main` at merged foundation
`dee52b0344c700237f18f6bff1a4eb016a8317a4`. The head was unchanged at
`125fcc7e2a506df97d1bc5176520d4313f7b89bf`. The 212-file diff was byte-identical
before and after retargeting. The PR remains draft and on HOLD. The historical
read-only assessment remains unchanged; `retarget-receipt.json` records the action.

The final hosted run on that head stopped inside checkpoint 6 at
`follow-up frozen evaluation differs`. Its failing result was not retained.
The cause of that old failure cannot be reconstructed from its artifact.
`replay_checkpoint6_diagnostics` now captures the exact case, normalized expected
and actual evaluation, and differing JSON paths before the frozen comparison.
It rethrows the original failure and preserves both final checkpoint-6 gates.
Historical evaluators and verdicts are unchanged. Independent source review
passed, three focused diagnostic tests passed, and all 359 portable tests passed.

The original native bundle `af12d52061c706aee5be94aa2d23e74b53d4d05ac262a44becd1f1e2a301974c`
has eight parts totaling 466,548 bytes. Review confirmed sensitive model reasoning
and internal session metadata in its native/transport records. The original
bundle must remain private. A separate sanitized disclosure view and per-file
manifest require independent review and the owner's final approval. No public
upload is authorized by preparing or reviewing that view.

Paid model operations remain zero. Production integration, consumer execution,
marketplace activation and external-alpha changes remain disabled.

## Completed disclosure preparation

Independent review decoded all eight original parts and both sanitized parts,
checked all 144 file mappings, and verified 63 retained function-call witnesses.
The sanitized view contains 135 unchanged public/synthetic records, nine distinct
projections, and its disclosure manifest. The two prepared parts total 69,294 bytes.
Its digest is `48add3667ad937c6ee724a3087f9febf06ea30c081c7a57db74f4b756dbc0724`.
The original remains private. No evidence parts or disclosure manifest have been
uploaded. Final owner approval of this exact view remains required.

The view omits raw model reasoning, opaque payloads, native provider instructions,
provider history, client/session identifiers and host operational metadata.
Automated scans and file review identified no credentials, private paths, or
private project source in the view. This is a scoped review, not a universal
secret-detection guarantee. Public replay can verify preserved tool journals,
source and outputs; it cannot reconstruct omitted raw native/provider content.
The original native provenance remains in private custody with independent review.

After the diagnostic fix, hosted run `38073082300` passed both observed checkpoint-6
comparisons. The run later failed replaying checkpoint-7 follow-up API call
`call_rdzlldpm`. Its retained result expected exit 0; the actual result exited 1
at per-request WAL configuration with `database is locked`. Cleanup was confirmed
and unauthorized changes were empty. `hosted-retarget-divergence.json` binds that
specific divergence. This does not establish the cause of the older uncaptured
checkpoint-6 failure.

The API correction uses separate harness `8.2.1-assisted-edit` and preserves
runtime 8.2.0. Additional task feedback requires the two literal edits without
rewriting the SQL string. Skill instructions and evaluator 8.0.0 are unchanged.
Pretrial source review and 373 portable tests pass; behavioral results require a
new native batch and separately bound review/replay. The historical FAIL stands.
