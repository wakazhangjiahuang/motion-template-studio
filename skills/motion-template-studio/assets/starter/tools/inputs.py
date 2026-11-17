import sys,json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry
def load(p):
 def pairs(rows):
  d={}
  for k,v in rows:
   if k in d:raise ValueError('duplicate JSON key')
   d[k]=v
  return d
 return json.loads(Path(p).read_text(),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite')))
root=Path(sys.argv[1]);m=load(root/'motion.json');schema=load(root/m['parameters']['schema']);preset=load(root/m['parameters']['defaultPreset']);inputs=load(sys.argv[2])
if not isinstance(inputs,dict):raise ValueError('inputs must be an object')
resolved={k:v['default'] for k,v in schema.get('properties',{}).items() if 'default' in v};resolved.update(preset);resolved.update(inputs)
def deny(uri):raise ValueError('remote schema reference forbidden')
Draft202012Validator(schema,registry=Registry(retrieve=deny)).validate(resolved)
print(json.dumps(resolved,ensure_ascii=False,allow_nan=False))
