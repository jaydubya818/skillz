"""Separate acceptance gate after matching fresh-clone and actual hosted replay."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import zipfile
from myskills.cohort_assessment import file_digest,seal
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal

EXPORTS={'checkpoint.json','profile.json','matrix.json','MyApps.json','MyFactory.json','MissionControl.json','MyEve-Sofie-subagents.json'}


def files(directory):
    return {name:file_digest(directory/name) for name in sorted(EXPORTS)}


def hosted_files(archive):
    with zipfile.ZipFile(archive) as data:
        entries=[entry for entry in data.infolist() if entry.filename.startswith('checkpoint5/') and not entry.is_dir()]
        require(len(entries)==7 and {e.filename for e in entries}=={'checkpoint5/'+n for n in EXPORTS},'hosted report export set differs')
        require(all(e.file_size<=2_000_000 for e in entries),'hosted report exceeds bound')
        return {e.filename.split('/')[1]:'sha256:'+sha256(data.read(e)).hexdigest() for e in entries}

def validate(candidate,pin,remote):
    unseal(candidate);unseal(pin)
    require(candidate['profile']['behavioral_candidate']=='PASS' and candidate['behavioral_candidate_profiles']==1,'behavioral corpus did not pass')
    require(candidate['profile']['qualification']=='PENDING_VALIDATION' and candidate['behaviorally_qualified_profiles']==0,'candidate self-promoted')
    require(pin['checkpoint_evidence_digest']==candidate['evidence_digest'],'validation bound to another candidate')
    require(pin['local_files']==pin['fresh_clone_files']==pin['hosted_files'] and set(pin['local_files'])==EXPORTS,'replay outputs disagree')
    require(pin['portable_tests']['status']=='PASS' and pin['browser_checks']['status']=='PASS','fresh-clone suites incomplete')
    require(remote['head_sha']==pin['source_commit'] and remote['id']==pin['run_id'] and remote['conclusion']=='success' and remote['status']=='completed','hosted run did not complete successfully at pinned source')
    require(remote['repository']['full_name']=='jaydubya818/skillz','unexpected hosted repository')
    require(pin['report_file_digest']==pin['local_files']['checkpoint.json'],'report file not in compared outputs')
    return seal({'schema':'myskills.accepted-profile.v5','qualification':'PASS','behaviorally_qualified_profiles':1,
                 'exact_profile':candidate['profile'],'candidate_evidence_digest':candidate['evidence_digest'],
                 'validation_pin_digest':pin['evidence_digest'],'hosted_run_id':remote['id'],'hosted_head_sha':remote['head_sha'],
                 'globally_trusted_skills':0,'catalog_qualification':'NOT_EVALUATED','global_trust':'UNTRUSTED',
                 'consumer_activation':'DISABLED','execution_eligible':False,'production_integration':'NOT_RUN','external_alpha_impact':'NONE'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True)
    p.add_argument('--pin',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fresh-report',type=Path,required=True);p.add_argument('--hosted-archive',type=Path,required=True)
    args=p.parse_args();candidate=json.loads(args.report.read_text());pin=json.loads(args.pin.read_text())
    require(file_digest(args.report)==pin['report_file_digest'],'candidate file differs from validated bytes')
    require(type(pin['run_id']) is int and pin['run_id']>0,'invalid hosted run identity')
    remote=json.loads(subprocess.check_output(['gh','api',f'repos/jaydubya818/skillz/actions/runs/{pin["run_id"]}'],text=True))
    require(type(pin['artifact_id']) is int and pin['artifact_id']>0,'invalid artifact identity')
    artifact=json.loads(subprocess.check_output(['gh','api',f'repos/jaydubya818/skillz/actions/artifacts/{pin["artifact_id"]}'],text=True))
    require(artifact['workflow_run']['id']==pin['run_id'] and artifact['workflow_run']['head_sha']==pin['source_commit'],'artifact belongs to another run')
    require(file_digest(args.hosted_archive)==artifact['digest']==pin['archive_digest'],'hosted archive custody differs')
    require(files(args.report.parent)==pin['local_files'] and files(args.fresh_report)==pin['fresh_clone_files'] and hosted_files(args.hosted_archive)==pin['hosted_files'],'actual replay bytes differ')
    value=validate(candidate,pin,remote)
    with args.output.open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(value['evidence_digest'])
