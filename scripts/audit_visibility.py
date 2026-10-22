import ast,copy,hashlib,json,pathlib,re,time,types
import argparse
if not __debug__:
    raise RuntimeError("Run without -O: audit assertions must remain enabled")
parser=argparse.ArgumentParser(description='Audit HP visibility and build diagnostic input/target files')
parser.add_argument('--data-dir',type=pathlib.Path,required=True)
parser.add_argument('--output-dir',type=pathlib.Path,required=True)

args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=False)

ROOT=args.output_dir
SRC=args.data_dir/'FIREBALL'
raw=[json.loads(l) for l in (SRC/'raw.jsonl').read_text(encoding='utf-8').splitlines()]
triples=[json.loads(l) for l in (SRC/'filtered_triples.jsonl').read_text(encoding='utf-8').splitlines()]
# Execute only the inspected, dependency-free upstream hp_str method, not the project.
p=args.data_dir/'sources/avrae_cogs5e_initiative_combatant.py'
lock=json.loads((pathlib.Path(__file__).resolve().parents[1]/'config/sources.lock.json').read_text(encoding='utf-8'))
record=next(x for x in lock if x['file']=='sources/avrae_cogs5e_initiative_combatant.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'], 'Pinned upstream method hash mismatch'
tree=ast.parse(p.read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Combatant')
method=copy.deepcopy(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='hp_str'))
ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(p),'exec'),ns);hp_str=ns['hp_str']
def build_inputs(events,ts):
 output=[]
 for ti,t in enumerate(ts):
  group=[(i,events[i]) for i in t['command_idxs']]
  cmds=[(i,e) for i,e in group if e['event_type']=='command'];assert len(cmds)==1
  targetid=cmds[0][1]['message_id'];target=[(i,e) for i,e in group if e['event_type']=='message' and e['message_id']==targetid];assert len(target)==1
  boundary,action=target[0];hist=[];seen=set()
  for i,e in enumerate(events[:boundary]):
   if e['event_type']!='message' or e.get('author_bot'):continue
   if int(e['message_id'])>=int(targetid) or e['created_at']>=action['created_at']:continue
   if e['message_id'] in seen:continue
   seen.add(e['message_id']);hist.append({'raw_idx':i,'author_id':str(e['author_id']),'created_at':e['created_at'],'message_id':str(e['message_id']),'content':e['content']})
  hist=sorted(hist,key=lambda e:int(e['message_id']))[-20:]
  output.append({'sample_id':f'{events[0]["combat_id"]}:{ti}','speaker_id':str(t['speaker_id']),'history':hist,'view_scope':'recorded human channel messages only; role visibility unverified','state_included':False})
 return output
inputs=build_inputs(raw,triples);labels=[];privacy=[]
for ti,t in enumerate(triples):
 labels.append({'sample_id':inputs[ti]['sample_id'],'commands_norm':t['commands_norm'],'automation_results':t['automation_results'],'combat_state_after':t['combat_state_after'],'usage':'observed target/result, not oracle reward or counterfactual'})
 before=raw[t['before_state_idx']]['data']['combatants']
 for a in before:
  if a.get('private') is not True:continue
  matches=[x for x in t['combat_state_before'] if x['name']==a['name'] and str(x['controller_id'])==str(a['controller_id'])];assert len(matches)==1
  norm=matches[0];fake=types.SimpleNamespace(is_private=True,hp=a['hp'],max_hp=a['max_hp'],temp_hp=a.get('temp_hp',0))
  pub=hp_str(fake);priv=hp_str(fake,True)
  token=f"{a['hp']}/{a['max_hp']} HP"
  privacy.append({'triple_index':ti,'before_state_idx':t['before_state_idx'],'actor_name':a['name'],'controller_id':str(a['controller_id']),'speaker_is_controller':str(t['speaker_id'])==str(a['controller_id']),'upstream_public_hp':pub,'upstream_revealed_hp':priv,'normalized_hp':norm['hp'],'normalized_has_raw_numeric_hp':token in norm['hp'],'public_has_raw_numeric_hp':token in pub,'public_status_found_in_recorded_human_readable':(a['name']+' '+pub) in raw[t['before_state_idx']]['human_readable']})
# A future event/target/state must not influence the serialized input for that decision.
tests=[]
for ti,t in enumerate(triples):
 targetid=next(raw[i]['message_id'] for i in t['command_idxs'] if raw[i]['event_type']=='command')
 bi=next(i for i in t['command_idxs'] if raw[i]['event_type']=='message' and raw[i]['message_id']==targetid)
 for mutation in ['future_text','target_text','structured_state']:
  rr=copy.deepcopy(raw);tt=copy.deepcopy(triples)
  if mutation=='future_text':
   for e in rr[bi+1:]:
    if 'content' in e:e['content']='AUDIT_FUTURE_SENTINEL'
   tt[ti]['automation_results']=['AUDIT_FUTURE_SENTINEL'];tt[ti]['after_utterances']=['AUDIT_FUTURE_SENTINEL']
  elif mutation=='target_text':
   rr[bi]['content']='AUDIT_TARGET_SENTINEL';tt[ti]['commands_norm']=['AUDIT_TARGET_SENTINEL']
  else:
   for e in rr:
    if e['event_type']=='combat_state_update':e['data']={'AUDIT_STATE_SENTINEL':True};e['human_readable']='AUDIT_STATE_SENTINEL'
   tt[ti]['combat_state_before']=[{'AUDIT_STATE_SENTINEL':True}]
  same=build_inputs(rr,tt)[ti]==inputs[ti];tests.append({'triple_index':ti,'mutation':mutation,'pass':same});assert same
for name,rows in [('inputs.jsonl',inputs),('targets_results.jsonl',labels)]:
 (ROOT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
(ROOT/'privacy_rows.json').write_text(json.dumps(privacy,indent=2),encoding='utf-8')
(ROOT/'boundary_tests.json').write_text(json.dumps(tests,indent=2),encoding='utf-8')
results={'scope':'single combat diagnostic; no corpus inference, no training','raw_source_sha256':hashlib.sha256((SRC/'raw.jsonl').read_bytes()).hexdigest(),'triples_source_sha256':hashlib.sha256((SRC/'filtered_triples.jsonl').read_bytes()).hexdigest(),'samples':len(inputs),'private_actor_occurrences_before':len(privacy),'private_numeric_hp_retained':sum(x['normalized_has_raw_numeric_hp'] for x in privacy),'upstream_public_numeric_hp':sum(x['public_has_raw_numeric_hp'] for x in privacy),'noncontroller_sample_occurrences':sum(not x['speaker_is_controller'] for x in privacy),'upstream_public_status_matches_recorded_summary':sum(x['public_status_found_in_recorded_human_readable'] for x in privacy),'boundary_tests':len(tests),'boundary_tests_passed':sum(x['pass'] for x in tests),'input_history_lengths':[len(x['history']) for x in inputs],'private_hp_example':privacy[0] if privacy else None,'gpu_calls':0,'paid_api_calls':0,'model_calls':0,'cross_session_scope':'single pinned combat only'}
(ROOT/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))
