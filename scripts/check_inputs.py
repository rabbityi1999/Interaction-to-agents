import pathlib,json,hashlib,copy
import argparse
if not __debug__:
    raise RuntimeError('Run without -O: audit assertions must remain enabled')
parser=argparse.ArgumentParser(description='Independently check action input boundaries')
parser.add_argument('--data-dir',type=pathlib.Path,required=True)
parser.add_argument('--schema-dir',type=pathlib.Path,required=True)
parser.add_argument('--visibility-dir',type=pathlib.Path,required=True)
args=parser.parse_args()
r=args.visibility_dir
src=args.data_dir
if (r/'independent_checks.json').exists():
    raise FileExistsError('Refuse to overwrite independent_checks.json')
raw=[json.loads(l) for l in (src/'FIREBALL/raw.jsonl').read_text(encoding='utf-8').splitlines()]
lineage=json.loads((args.schema_dir/'lineage.json').read_text());inputs=[json.loads(l) for l in (r/'inputs.jsonl').read_text(encoding='utf-8').splitlines()]
labels=[json.loads(l) for l in (r/'targets_results.jsonl').read_text(encoding='utf-8').splitlines()]
def check(rows):
 assert len(rows)==len(lineage)==25
 for x,link,y in zip(rows,lineage,labels):
  assert x['sample_id']==y['sample_id']
  assert set(x)=={'sample_id','speaker_id','history','view_scope','state_included'}
  assert x['state_included'] is False
  boundary=link['action_message_idx'];target=raw[boundary]
  for m in x['history']:
   e=raw[m['raw_idx']]
   assert m['raw_idx']<boundary and int(m['message_id'])<target['message_id']
   assert m['created_at']<target['created_at']
   assert e['event_type']=='message' and not e['author_bot']
   assert m['content']==e['content'] and m['author_id']==str(e['author_id'])
   assert m['message_id']==str(e['message_id'])
  assert len({m['message_id'] for m in x['history']})==len(x['history'])
check(inputs)
bad=copy.deepcopy(inputs);boundary=lineage[0]['action_message_idx'];e=raw[boundary]
bad[0]['history'].append({'raw_idx':boundary,'message_id':str(e['message_id']),'created_at':e['created_at'],'content':e['content'],'author_id':str(e['author_id'])})
rejected=False
try:check(bad)
except AssertionError:rejected=True
assert rejected
bot=[]
for i,e in enumerate(raw):
 if e['event_type']=='message' and e.get('author_bot') and 'SH1 <' in e.get('content',''):
  bot.append({'raw_idx':i,'message_id':str(e['message_id']),'content':e['content']})
source_checks=[]
for m in json.loads((pathlib.Path(__file__).resolve().parents[1]/'config/sources.lock.json').read_text(encoding='utf-8')):
 if m['file'].startswith('sources/'):
  source_checks.append({'path':m['file'],'hash_match':hashlib.sha256((src/m['file']).read_bytes()).hexdigest()==m['sha256']})
assert all(m['hash_match'] for m in source_checks)
out={'status':'independent input boundary checker passed','rows_checked':len(inputs),'current_action_injection_rejected':rejected,'bot_public_hp_examples':bot,'state_summary_example':{'raw_idx':29,'human_readable':raw[29]['human_readable']},'source_checks':source_checks}
(r/'independent_checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checked':len(inputs),'negative_control_rejected':rejected,'bot_hp_examples':len(bot),'source_hashes_pass':len(source_checks)}))
