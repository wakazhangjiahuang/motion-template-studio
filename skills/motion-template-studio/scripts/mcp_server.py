#!/usr/bin/env python3
"""Local stdio MCP. No cloud endpoint and no media/model service is implied."""
from pathlib import Path
import json,os
from mcp.server.fastmcp import FastMCP
import motion_studio as studio

KB=Path(os.environ['MOTION_STUDIO_KB']).resolve() if os.environ.get('MOTION_STUDIO_KB') else None
WORK=Path(os.environ['MOTION_STUDIO_WORKSPACE']).resolve() if os.environ.get('MOTION_STUDIO_WORKSPACE') else None
mcp=FastMCP('motion-template-studio')

def catalog():return studio.strict_json(studio.catalog_path(KB).read_bytes())
def work_path(value,new=False):
 if not WORK or not WORK.is_dir():raise ValueError('Set MOTION_STUDIO_WORKSPACE to the explicit allowed workspace first')
 p=Path(value);p=(WORK/p).resolve() if not p.is_absolute() else p.resolve()
 if not p.is_relative_to(WORK):raise ValueError('Path outside allowed workspace')
 if new and p.exists():raise ValueError('Refusing existing output')
 if not new and not p.is_file():raise ValueError('Expected existing file')
 return p

@mcp.tool()
def search_recipes(query:str,engine:str='',kind:str='')->dict:
 """Find declared recipes; rank is lexical matching, never recognition accuracy or runtime proof."""
 return studio.search(query,engine or None,kind or None,KB)

@mcp.tool()
def get_recipe(recipe_id:str)->dict:
 """Read an exact catalog record, implementation and acceptance requirements."""
 for a in catalog()['assets']:
  if a['id']==recipe_id:return a
 raise ValueError('Unknown recipe ID')

@mcp.tool()
def get_source_excerpt(source_id:str,start_line:int=1,end_line:int=60)->dict:
 """Read registered, KB-contained source by ID; never arbitrary local paths. Max 200 lines/40KB."""
 if start_line<1 or end_line<start_line or end_line-start_line>=200:raise ValueError('Invalid line range')
 a=catalog().get('sources',{}).get(source_id)
 if not a:raise ValueError('Unknown source ID')
 if KB:
  p=(KB/a['path']).resolve()
  if not p.is_relative_to(KB):raise ValueError('Registered source outside KB')
 else:
  # Portable Skill remains useful without claiming the full repository is mounted.
  prefix='skills/motion-template-studio/'
  if not a['path'].startswith(prefix):return {'status':'SOURCE_NOT_MOUNTED','source':a,'next':'Mount repository as MOTION_STUDIO_KB or read the stated upstream URL'}
  p=(studio.ROOT/a['path'][len(prefix):]).resolve()
  if not p.is_relative_to(studio.ROOT):raise ValueError('Source outside Skill')
 if not p.is_file():return {'status':'SOURCE_NOT_MOUNTED','source':a}
 if p.stat().st_size>4*1024**2:raise ValueError('Source too large')
 b=p.read_bytes();lines=b.decode('utf-8').splitlines();excerpt='\n'.join(lines[start_line-1:end_line])
 if len(excerpt.encode())>40000:raise ValueError('Excerpt too large; request fewer lines')
 return {'status':'READ','source':a,'sha256':studio.digest(b),'start_line':start_line,'end_line':min(end_line,len(lines)),'text':excerpt}

@mcp.tool()
def check_compatibility(recipe_id:str,target_engine:str)->dict:
 """Compare engine declarations; this does not render or certify the recipe."""
 a=get_recipe(recipe_id)
 return {'recipe_id':recipe_id,'status':'DECLARATION_MATCH' if a['engine'] in ('agnostic',target_engine) else 'ADAPTER_REQUIRED','declared_engine':a['engine'],'target_engine':target_engine,'runtime':'NOT_RUN','verification':a['verification']}

@mcp.tool()
def get_validation_case(case_id:str)->dict:
 """Get concrete test operation and required evidence from the registered validation catalog."""
 p=studio.ROOT/'assets/validation-cases.json'
 for a in studio.strict_json(p.read_bytes())['cases']:
  if a['id']==case_id:return a
 raise ValueError('Unknown validation case ID')

@mcp.tool()
def audit_motion_package(path:str)->dict:
 """Read-only author package audit under explicit workspace. Never runs embedded code or online checks."""
 return studio.audit(work_path(path))

@mcp.tool()
def plan_motion_repairs(path:str)->dict:
 """Plan author root/integrity corrections bound to source SHA. Personal delivery is blocked."""
 return studio.repair_plan(work_path(path))

@mcp.tool()
def apply_motion_repair(path:str,plan_json:str,output:str)->dict:
 """Apply only an exact recomputed SHA-bound repair plan to a NEW workspace file. Never overwrites."""
 import tempfile
 p=work_path(path);out=work_path(output,new=True);plan=studio.strict_json(plan_json)
 with tempfile.TemporaryDirectory(prefix='motion-repair-plan-') as tmp:
  pp=Path(tmp)/'plan.json';studio.write_json(pp,plan)
  return studio.repair(p,pp,out)

if __name__=='__main__':mcp.run(transport='stdio')
