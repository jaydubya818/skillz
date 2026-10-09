from copy import deepcopy
import pytest
from myskills.cohort_assessment import seal
from myskills.manifest import ValidationError
from qualification.accept_checkpoint_five import validate,EXPORTS,hosted_files


def inputs():
    c=seal({'profile':{'behavioral_candidate':'PASS','qualification':'PENDING_VALIDATION'},'behavioral_candidate_profiles':1,'behaviorally_qualified_profiles':0})
    files={name:'sha256:fixture' for name in EXPORTS}
    p=seal({'checkpoint_evidence_digest':c['evidence_digest'],'local_files':dict(files),'fresh_clone_files':dict(files),'hosted_files':dict(files),
            'portable_tests':{'status':'PASS'},'browser_checks':{'status':'PASS'},'report_file_digest':files['checkpoint.json'],'source_commit':'a'*40,'run_id':1})
    r={'id':1,'head_sha':'a'*40,'conclusion':'success','status':'completed','repository':{'full_name':'jaydubya818/skillz'}}
    return c,p,r


def test_acceptance_requires_matching_candidate_replays_and_hosted_success():
    c,p,r=inputs();assert validate(c,p,r)['qualification']=='PASS'
    for key,value in [('conclusion','failure'),('head_sha','b'*40),('status','in_progress')]:
        wrong={**r,key:value}
        with pytest.raises(ValidationError):validate(c,p,wrong)
    wrong=deepcopy(p);wrong['hosted_files']['profile.json']='different';wrong=seal({k:v for k,v in wrong.items() if k!='evidence_digest'})
    with pytest.raises(ValidationError):validate(c,wrong,r)
    wrong=seal({**{k:v for k,v in c.items() if k!='evidence_digest'},'behaviorally_qualified_profiles':1})
    with pytest.raises(ValidationError):validate(wrong,p,r)


def test_hosted_archive_requires_exact_export_set(tmp_path):
    import zipfile
    good=tmp_path/'good.zip'
    with zipfile.ZipFile(good,'w') as archive:
        for name in EXPORTS:archive.writestr('checkpoint5/'+name,'{}')
    assert set(hosted_files(good))==EXPORTS
    wrong=tmp_path/'wrong.zip'
    with zipfile.ZipFile(wrong,'w') as archive:
        for name in EXPORTS:archive.writestr('other-checkpoint/'+name,'{}')
    with pytest.raises(ValidationError):hosted_files(wrong)
