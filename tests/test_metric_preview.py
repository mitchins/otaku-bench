"""Synthetic regression tests: no access to sealed gold required."""
import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'mission/metric_preview.py'
spec = importlib.util.spec_from_file_location('metric_preview', P)
metric = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metric)


def case(a, p, f, english='The door is open.', error=None, note=False, original='扉が開いている。'):
    g = {'id': 'JMB-900', 'japanese':original,'primary_challenge':'idiom_proverb', 'split':'eval'}
    b = {'id':'JMB-900','japanese':original}
    r = {'id':'JMB-900','translation': english + ('\nNote: some context is missing.' if note else ''), 'error':error}
    j = {'id':'JMB-900', 'gold_sha256':metric.sha(g), 'score':{'adequacy':a,'pragmatics':p,'fluency':f}}
    return metric.assess_case(g,b,r,j)


def test_gated_full_fidelity():
    assert case(4,4,2)['pass']
    assert case(4,4,1)['pass']  # awkward English still faithful and readable
    assert not case(3,4,2)['pass']  # lost meaning cannot compensate with nuance
    assert not case(4,3,2)['pass']  # lost nuance cannot compensate with literal meaning
    assert not case(4,4,0)['pass']  # broken English not reader ready
    assert case(4,4,2,note=True)['fidelity']
    assert not case(4,4,2,note=True)['pass']  # commentary fails screen readiness
    assert case(4,4,2,note=True)['raw'] == 10  # original judge untouched


def test_exact_echo_overrides_judge():
    c = case(4,4,2,english='扉が開いている。')
    assert c['status']=='mechanical_zero' and c['raw']==0
    assert c['zero_reason']=='exact_echo'
    assert not c['pass']


def test_failures_and_pending_are_distinct():
    c=case(4,4,2,english='',error='token_cap')
    assert c['status']=='mechanical_zero' and c['raw']==0
    assert c['zero_reason']=='inference_failure'
    g={'id':'JMB-900','primary_challenge':'idiom_proverb'}
    b={'japanese':'扉が開いている。'}
    assert metric.assess_case(g,b,None,None)['status']=='not_run'
    assert metric.assess_case(g,b,{'translation':'Door open','error':None},None)['status']=='pending_judge'


def test_unchanged_raw_and_partial_nonranking():
    g={'id':'JMB-900','primary_challenge':'idiom_proverb','split':'eval','japanese':'扉が開いている。'}
    b={'id':'JMB-900','japanese':'扉が開いている。'}
    jr={'id':'JMB-900','model':'gpt-6.1-sol','score':{'adequacy':4,'pragmatics':3,'fluency':2},'gold_sha256':metric.sha(g)}
    rs={'id':'JMB-900','translation':'The door is open.', 'error':None}
    result=metric.summarize('test',[jr],[rs],{'JMB-900':g}, {'JMB-900':b},None)
    assert result['status']=='COMPLETE'
    assert result['raw_mean_10']==9
    assert result['screen_ready_pct']==0
    assert result['loss_points_per_100']==100
    result2=metric.summarize('test',[],[rs],{'JMB-900':g},{'JMB-900':b},None)
    assert result2['status']=='INCOMPLETE'
    assert result2['screen_ready_pct'] is None


def test_stratified_bootstrap_repeatable():
    items=[{'category':'A','pass':i%2==0} for i in range(20)]+[{'category':'B','pass':True} for _ in range(20)]
    c1=metric.stratified_ci(items,reps=200)
    assert c1==metric.stratified_ci(items,reps=200)
    assert c1[0] <= 75 <= c1[1]


def test_stale_judgment_is_pending_not_zero():
    g={'id':'JMB-900','primary_challenge':'idiom_proverb','split':'eval','japanese':'扉が開いている。'}
    b={'id':'JMB-900','japanese':'扉が開いている。'}
    r={'translation':'The door is open.','error':None}
    j={'score':{'adequacy':4,'pragmatics':4,'fluency':2},'gold_sha256':'old'}
    result=metric.assess_case(g,b,r,j)
    assert result['status']=='pending_judge'


def test_paired_bootstrap_preserves_matched_items_and_direction():
    a={'model':'A','_private_cases':{str(i):{'id':str(i),'category':'idiom', 'raw':10,'pass':True} for i in range(20)}}
    b={'model':'B','_private_cases':{str(i):{'id':str(i),'category':'idiom', 'raw':9,'pass':i%2==0} for i in range(20)}}
    r=metric.paired_pass_delta(a,b,reps=100)
    assert r['delta_pp']==50.0 and r['n']==20
    assert r['a_only_passes']==10 and r['b_only_passes']==0 and r['ties']==10
    assert r['ci_95_pp'][0]>0


def test_polished_requires_natural_english():
    assert case(4,4,2)['polished']
    assert case(4,4,1)['pass'] and not case(4,4,1)['polished']
    assert not case(4,4,2,note=True)['polished']
