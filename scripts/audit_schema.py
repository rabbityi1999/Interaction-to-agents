import pathlib,json,collections,hashlib,datetime,time
import argparse
if not __debug__:
    raise RuntimeError("Run without -O: audit assertions must remain enabled")
parser=argparse.ArgumentParser(description='Audit the pinned FIREBALL combat and CRD3 episode')
parser.add_argument('--data-dir',type=pathlib.Path,required=True)
parser.add_argument('--output-dir',type=pathlib.Path,required=True)

args=parser.parse_args()
args.output_dir.mkdir(parents=True,exist_ok=False)

root=args.data_dir
start=time.perf_counter()
def readj(p):return json.loads(p.read_text(encoding='utf-8'))
def jsonl(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
raw=jsonl(root/'FIREBALL/raw.jsonl');tri=jsonl(root/'FIREBALL/filtered_triples.jsonl');c=readj(root/'CRD3/C1E001.json');turns=c['TURNS']
issues=[];links=collections.Counter();order=[];speaker=[];texteq=[]
for tid,t in enumerate(tri):
    for key,expected in [('before_idxs','message'),('after_idxs','message'),('command_idxs',None),('before_state_idx','combat_state_update'),('after_state_idx','combat_state_update'),('embed_idxs','message')]:
        val=t.get(key);ixs=val if isinstance(val,list) else [val]
        for idx in ixs:
            if idx is None:continue
            links[key]+=1
            if not isinstance(idx,int) or not 0<=idx<len(raw):issues.append([tid,key,idx,'out_of_range'])
            elif expected is not None and raw[idx]['event_type']!=expected:issues.append([tid,key,idx,raw[idx]['event_type']])
    ci=t['command_idxs']; b=t['before_state_idx'];a=t['after_state_idx']
    order.append(b<=min(ci)<=max(ci)<=a)
    actor_events=[raw[i] for i in ci if raw[i]['event_type'] in ('command','button_press')]; speaker.append(bool(actor_events) and all(str(e['author_id'])==str(t['speaker_id']) for e in actor_events))
    for field,idxfield in [('before_utterances','before_idxs'),('after_utterances','after_idxs')]:
        texteq.append(t[field]==[raw[i]['content'] for i in t[idxfield]])
msgs=[x for x in raw if x['event_type']=='message'];commands=[x for x in raw if x['event_type']=='command'];cmdids={x['message_id'] for x in commands}
human=[x for x in msgs if not x['author_bot']];noncmd=[x for x in human if x['message_id'] not in cmdids]
states=[x for x in raw if x['event_type']=='combat_state_update'];ts=[x['timestamp'] for x in raw]
rawactors=[a for s in states for a in s['data']['combatants']]
allnames=collections.Counter(n for t in turns for n in t.get('NAMES',[]))
result={'scope':'one FIREBALL combat and one CRD3 episode; purposive schema audit, NOT corpus estimate or training benchmark','FIREBALL':{'raw_events':len(raw),'event_types':dict(collections.Counter(x['event_type'] for x in raw)),'combat_ids':len({x['combat_id'] for x in raw}),'span_seconds':max(ts)-min(ts),'timestamp_adjacent_inversions':sum(a>b for a,b in zip(ts,ts[1:])),'human_message_events':len(human),'bot_message_events':len(msgs)-len(human),'human_message_ids_also_command':sum(x['message_id'] in cmdids for x in human),'human_noncommand_messages':len(noncmd),'human_authors':len({x['author_id'] for x in human}),'noncommand_authors':len({x['author_id'] for x in noncmd}),'triples':len(tri),'triple_command_author_count':len({t['speaker_id'] for t in tri}),'raw_link_count':sum(links.values()),'raw_links_by_key':dict(links),'raw_link_errors':issues,'naive_all_group_events_before_after_state_pass':sum(order),'triple_speaker_command_match_pass':sum(speaker),'utterance_exact_raw_list_match_pass':sum(texteq),'utterance_exact_raw_list_match_total':len(texteq),'null_current_actor':sum(t['current_actor'] is None for t in tri),'empty_before_utterances':sum(not t['before_utterances'] for t in tri),'empty_after_utterances':sum(not t['after_utterances'] for t in tri),'normalized_actor_keys':sorted({k for t in tri for a in t['combat_state_before'] for k in a}),'raw_actor_top_level_keys':sorted({k for a in rawactors for k in a}),'message_top_level_keys':sorted({k for x in msgs for k in x})},'CRD3':{'episode':'C1E001','turns':len(turns),'turn_keys':sorted({k for t in turns for k in t}),'number_contiguous_from_zero':all(t.get('NUMBER')==i for i,t in enumerate(turns)),'utterance_segments':sum(len(t['UTTERANCES']) for t in turns),'multi_name_turns':sum(len(t['NAMES'])>1 for t in turns),'no_name_turns':sum(not t['NAMES'] for t in turns),'name_labels':dict(allnames),'metadata_keys':list(c['METADATA'])},'resources':{'backend':'local Python stdlib CPU only','gpu_used':False,'model_calls':0,'paid_api_calls':0,'elapsed_seconds':time.perf_counter()-start}}
# source bytes are independently verified against manifest and Git blob hashes
checks=[]
for d in readj(pathlib.Path(__file__).resolve().parents[1]/'config/sources.lock.json'):
    b=(root/d['file']).read_bytes(); checks.append({'file':d['file'],'bytes_match':len(b)==d['bytes'],'sha256_match':hashlib.sha256(b).hexdigest()==d['sha256'],'git_blob_match':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==d['git_blob_sha']})
result['download_checks']=checks
lineage=[]
for tid,t in enumerate(tri):
    group=[(i,raw[i]) for i in t['command_idxs']]
    msg=[(i,x) for i,x in group if x['event_type']=='message']
    cmd=[(i,x) for i,x in group if x['event_type']=='command']
    aut=[(i,x) for i,x in group if x['event_type']=='automation_run']
    state=raw[t['after_state_idx']]
    same=len(msg)==len(cmd)==len(aut)==1 and msg[0][1]['message_id']==cmd[0][1]['message_id']==aut[0][1]['interaction_id']==state['probable_interaction_id']
    lineage.append({'triple_index':tid,'source_combat_id':raw[0]['combat_id'],'command_group_event_types':[x['event_type'] for _,x in group],'action_message_idx':msg[0][0] if len(msg)==1 else None,'command_log_idx':cmd[0][0] if len(cmd)==1 else None,'before_state_idx':t['before_state_idx'],'after_state_idx':t['after_state_idx'],'same_interaction_id':same,'before_state_precedes_action_message':len(msg)==1 and t['before_state_idx']<msg[0][0],'command_log_after_result':len(cmd)==1 and cmd[0][0]>t['after_state_idx']})
result['FIREBALL']['command_group_event_types']=dict(collections.Counter(raw[i]['event_type'] for t in tri for i in t['command_idxs']))
result['FIREBALL']['same_interaction_id_pass']=sum(x['same_interaction_id'] for x in lineage)
result['FIREBALL']['before_state_precedes_action_message_pass']=sum(x['before_state_precedes_action_message'] for x in lineage)
result['FIREBALL']['command_log_after_result_count']=sum(x['command_log_after_result'] for x in lineage)
result['FIREBALL']['raw_actor_private_value_counts_in_snapshots']=dict(collections.Counter(str(a.get('private')) for a in rawactors))
(args.output_dir/'lineage.json').write_text(json.dumps(lineage,indent=2),encoding='utf-8')
assert not issues
assert all(x['same_interaction_id'] and x['before_state_precedes_action_message'] for x in lineage)
assert all(x['bytes_match'] and x['sha256_match'] and x['git_blob_match'] for x in checks)

(args.output_dir/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
