"""Separately authorized recovery identity; historical pins remain unchanged."""
import json
from pathlib import Path
from typing import Any

from myskills.cohort_assessment import file_digest
from myskills.digest import digest_object
from qualification.checkpoint_four import require, unseal
from qualification.recovery_probe_v8 import stable_runtime
from qualification.runtime_identity import MODEL_DIGEST
from qualification.v4.adapter import VERSION as ADAPTER, schemas
from qualification.v8.cases import CASES
from qualification.v8.evaluate import VERSION as EVALUATOR
from qualification.v8.probe import context as historical_context, binding as historical_binding, prompt as historical_prompt

VERSION = 'myskills-local-runtime/8.2.0'
HARNESS = 'codex-app-server/0.157.0+myskills-native-8.2.0-recovery'
LOCATION = Path('qualification/checkpoint8/successor')
RUNTIME_DIGEST = 'sha256:ac26a2e9bf3afc13b7513772a816c522740767924fbee3c801faa08dce769276'
HISTORICAL_DIGEST = 'sha256:9edd4313e400254d9a6c765c089010562a8db2eafa6e5c1771b69d79d02a5a14'


def validate_identity(old: dict[str, Any], runtime: dict[str, Any], shown: dict[str, Any],
                      reconstructed: dict[str, Any]) -> None:
    require(digest_object(old) == HISTORICAL_DIGEST, 'historical runtime changed')
    require(digest_object(runtime) == RUNTIME_DIGEST, 'successor runtime changed')
    require(runtime['model_digest'] == 'sha256:'+MODEL_DIGEST, 'model substitution')
    require(digest_object(shown) == runtime['service']['show_digest'], 'successor metadata changed')
    require(digest_object(reconstructed) == old['service']['show_digest'], 'historical metadata reconstruction changed')
    before, after = stable_runtime(old), stable_runtime(runtime)
    after['service']['show_digest'] = before['service']['show_digest']
    require(before == after, 'unapproved runtime change')
    changed = {key for key in reconstructed.keys() | shown.keys() if reconstructed.get(key) != shown.get(key)}
    require(changed == {'modified_at', 'parameters', 'modelfile'}, 'unexpected metadata delta')
    require(sorted(shown['parameters'].splitlines()) == sorted(reconstructed['parameters'].splitlines()), 'parameter values changed')
    old_lines, new_lines = reconstructed['modelfile'].splitlines(), shown['modelfile'].splitlines()
    require([line for line in old_lines if not line.startswith('PARAMETER ')] ==
            [line for line in new_lines if not line.startswith('PARAMETER ')], 'model formatting changed')
    require(sorted(line for line in old_lines if line.startswith('PARAMETER ')) ==
            sorted(line for line in new_lines if line.startswith('PARAMETER ')), 'model parameters changed')


def context(root: Path) -> dict[str, Any]:
    value = historical_context(root)
    directory = root/LOCATION
    runtime = json.loads((directory/'runtime-pin.json').read_text())
    shown = json.loads((directory/'model-show.json').read_text())
    reconstructed = json.loads((directory/'historical-show-reconstructed.json').read_text())
    validate_identity(value['runtime'], runtime, shown, reconstructed)
    require(file_digest(directory/'model-manifest.json') == runtime['model_digest'], 'manifest changed')
    profile = json.loads((directory/'profile.json').read_text())
    unseal(profile)
    require(profile['runtime_version'] == VERSION and profile['harness_version'] == HARNESS
            and profile['adapter_version'] == ADAPTER and profile['evaluator_version'] == EVALUATOR, 'profile version differs')
    require(profile['runtime_digest'] == RUNTIME_DIGEST and profile['model_digest'] == runtime['model_digest'], 'profile runtime differs')
    require(profile['corpus_digest'] == digest_object(CASES) and profile['tool_contracts'] ==
            {name: digest_object(schemas(case)) for name, case in CASES.items()}, 'corpus or tool contract changed')
    for name, digest in profile['evidence_references'].items():
        require(Path(name).name == name and file_digest(directory/name) == digest, 'profile evidence changed')
    paths = [root/'qualification/runtime_successor_v8.py', root/'qualification/successor_probe_v8.py',
             root/'qualification/recovery_probe_v8.py',
             root/'qualification/custody_guard.py', *[directory/name for name in profile['evidence_references']], directory/'profile.json']
    return {**value, 'schema': 'myskills.native-batch.v8.2-recovery', 'runtime': runtime,
            'runtime_profile': profile, 'historical_runtime_digest': HISTORICAL_DIGEST,
            'runtime_change': 'Separately authorized full pin; timestamp and display-order delta proved by historical digest reconstruction. No behavioral equivalence inferred.',
            'harness': {**value['harness'], **{str(path.relative_to(root)): file_digest(path) for path in paths}}}


def binding(ctx: dict[str, Any], name: str) -> dict[str, Any]:
    value = historical_binding(ctx, name)
    value['harness']['version'] = HARNESS
    value['environment']['runtime_profile'] = VERSION
    value['environment']['runtime_profile_digest'] = ctx['runtime_profile']['evidence_digest']
    return value


def prompt(root: Path, ctx: dict[str, Any], name: str) -> str:
    value = json.loads(historical_prompt(root, ctx, name))
    value['native_runtime'] = HARNESS
    return json.dumps(value, sort_keys=True)
