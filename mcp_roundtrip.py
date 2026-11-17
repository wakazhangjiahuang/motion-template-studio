"""Reproduce local MCP behavior using bundled synthetic author fixtures."""
import asyncio,json,os,sys,tempfile,shutil
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
R=Path(__file__).resolve().parents[1]
async def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='motion-mcp-test-') as td:
  w=Path(td);shutil.copyfile(R/'fixtures/tampered.motion',w/'source.motion')
  before=(w/'source.motion').read_bytes()
  params=StdioServerParameters(command=sys.executable,args=[str(R/'mcp/server.py')],env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MOTION_STUDIO_KB':str(R),'MOTION_STUDIO_WORKSPACE':str(w)})
  async with stdio_client(params) as (read,write):
   async with ClientSession(read,write) as c:
    await c.initialize();tools=await c.list_tools();assert len(tools.tools)==8;checks.append('8 tools discovered')
    async def call(name,args):
     r=await c.call_tool(name,args);d=r.structuredContent
     if d is None:
      try:d=json.loads(''.join(x.text for x in r.content if x.type=='text'))
      except:d={}
     return r,d
    r,d=await call('search_recipes',{'query':'接力'});assert not r.isError and d['results'];checks.append('recipe search')
    r,d=await call('get_recipe',{'recipe_id':'package-repair'});assert d['id']=='package-repair';checks.append('exact recipe')
    r,d=await call('get_source_excerpt',{'source_id':'adu:scripts/pipeline.py','start_line':1,'end_line':12});assert d['status']=='READ';checks.append('pinned source excerpt')
    r,d=await call('check_compatibility',{'recipe_id':'semantic-handoff','target_engine':'html-canvas/1'});assert d['status']=='ADAPTER_REQUIRED' and d['runtime']=='NOT_RUN';checks.append('engine boundary')
    r,d=await call('get_validation_case',{'case_id':'new-content'});assert d['id']=='new-content';checks.append('validation retrieval')
    r,d=await call('audit_motion_package',{'path':'source.motion'});assert d['status']=='FAIL';checks.append('tamper detected')
    r,plan=await call('plan_motion_repairs',{'path':'source.motion'});assert plan['fixes'];checks.append('bound repair plan')
    r,d=await call('apply_motion_repair',{'path':'source.motion','plan_json':json.dumps(plan),'output':'new.motion'});assert not r.isError and d['audit']['status']=='STATIC_PASS';assert (w/'source.motion').read_bytes()==before;checks.append('new artifact, source preserved')
    r,d=await call('audit_motion_package',{'path':'../outside.motion'});assert r.isError;checks.append('workspace escape rejected')
    r,d=await call('apply_motion_repair',{'path':'source.motion','plan_json':json.dumps(plan),'output':'new.motion'});assert r.isError;checks.append('overwrite rejected')
 print(json.dumps({'status':'PASS','checks':checks,'runtime_visual':'NOT_RUN'},ensure_ascii=False))
asyncio.run(main())
