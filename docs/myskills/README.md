# MySkills reference platform

MySkills adds governance to the existing portable collection. It does not execute
skills, connect services, mint Work authority, or publish owner work. The public
catalog is metadata; instructions load only after exact selection and validation.

## Development

Python 3.10 or later is required. The runtime uses only the standard library.

```sh
python3 -m venv .artifacts/venv
.artifacts/venv/bin/pip install pytest
.artifacts/venv/bin/python -m pytest tests -q --ignore=tests/test_evidence.py
python3 -m myskills validate
python3 -m myskills inspect api-and-interface-design
python3 -m myskills digest api-and-interface-design
python3 -m myskills provenance api-and-interface-design
python3 -m myskills overlaps
python3 -m myskills catalog > catalog/myskills.json
python3 -m myskills schema > catalog/skill-manifest.schema.json
```

The recorder suite has separate FFmpeg/display prerequisites. Passing portable
checks does not establish recorder support, live review or skill qualification.

## Manifest and identity

The authoritative contract is `myskills.manifest.SCHEMA`, exported as
[JSON schema](../../catalog/skill-manifest.schema.json). Objects reject unknown
fields. Effects use the enumerated taxonomy. Capabilities require a dotted namespace;
a namespace makes a declaration syntactically valid, never authorized. Secrets use
requirement names and credential-handle classes, never values or credential handles.

The legacy importer supports the repository's scalar and metadata YAML subset.
Unsupported syntax produces an explicit inventory failure. It preserves SKILL.md
and runtime metadata in place. Runtime labels describe packaging compatibility,
not behavioral qualification. See the upstream [Agent Skills specification](https://agentskills.io/specification).

Legacy versions use `0.0.0+legacy.<package-content-hash-prefix>`. These are generated
inventory identities, not an upstream version claim. The full SHA-256 digest remains
mandatory for Work binding. Actual upstream revisions live in provenance.

`myskills.package.v1` hashes canonical ASCII JSON with sorted keys and compact
separators. Its envelope contains the manifest minus only its `digest` field and
sorted file records: relative POSIX path, executable flag and SHA-256 of raw bytes.
Array order is significant. Line endings are significant. It includes supporting
scripts, templates, runtime metadata and bundled licenses. It rejects symlinks and
special files. It excludes `.git`, `__pycache__`, `.artifacts`, `.pytest_cache`,
`node_modules`, `.DS_Store` and `.pyc` runtime artifacts. Those excluded locations
must never be used as packaged executable resources. Dependency declarations bind
external content separately; a source reference is not a dependency grant.

Changing a security declaration changes identity. Mutable lifecycle, trust,
qualification and revocation decisions belong to external append-only registry
records; changing those records must never rewrite the package or historical Work.

## Safe legacy inventory

All 92 canonical skills, including the seven PR #5 adaptations, start UNTRUSTED,
NOT_EVALUATED, draft and UNREVIEWED. Their requested effect envelope is empty and
all consequential selection is denied until reviewed metadata and scoped evidence
exist. Empty dependency/capability declarations mean unknown for UNREVIEWED entries,
not that the skill has no dependencies. Resource limits are zero.

The catalog records lexical effect, helper, external-host and cross-skill reference
signals separately. These are review candidates, including mentions in examples,
and are not complete behavior analysis. Overlap candidates use description tokens;
they do not prove semantic equivalence and never delete or consolidate skills.

Vendor manifests and per-skill license files remain authoritative for attribution.
UNSPECIFIED licensing blocks future redistribution review, rather than asserting a
blanket platform license. The PR #5 rejection decisions remain unchanged.

## Authority and storage boundaries

Conversation, catalog presence, installation, selection, Work authority, Factory
admission and publication are distinct. The strictest policy controls actual effects.
Skill-authored trust labels and qualification claims cannot establish platform trust.

The reference registry partitions public records and each owner's private records
before search, counts and exact lookup. Missing and foreign records share a generic
error. Team and organization scopes are reserved and rejected until their policy is
implemented. Library callers must supply authenticated owner context; this library
is not an authentication service. In-process references are not a hostile-code sandbox.
Production encrypted private custody and transactional MyEve persistence are deferred.

No private owner material belongs in this public repository. Tests use synthetic
owners and content. Telemetry must never contain private bodies, queries, evidence,
secret data or private identifiers.

## Release boundaries

Production MyEve, MyFactory and Relay integration is disabled. The frozen external
alpha is unchanged. Paid model calls, deployments, tester grants, marketplace
payments and public marketplace activation remain zero. Automatic execution,
automatic updates and automatic self-publication are unavailable.

`myskills.package.export_package` emits a deterministic ZIP containing only the
hashed file set and the exact manifest. Ignored local artifacts never enter it.
Future runtimes must consume validated packages, not execute the source checkout
or install dependencies implicitly. This offline export is not Factory custody
fencing and does not make scripts safe to run.
