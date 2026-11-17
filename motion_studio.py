#!/usr/bin/env python3
"""Local authoring support. Static inspection NEVER executes template code or contacts services."""
from __future__ import annotations
import argparse,copy,hashlib,json,math,os,re,shutil,stat,subprocess,sys,tempfile,unicodedata,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[1]
VERSION='1.0.0'
CONTENT_VERSION='0.1.0-draft.1'
MAX_ARCHIVE=384*1024**2; MAX_FILE=150*1024**2; MAX_TOTAL=600*1024**2; MAX_ENTRIES=5000
FORBIDDEN={'.env','motiongit.key.json','AGENTS.md','CLAUDE.md','.cursorrules'}
BLOCKED_DIRS={'.git','node_modules','.venv','__pycache__','.claude','.cursor'}

class StudioError(Exception):pass
def digest(b):return hashlib.sha256(b).hexdigest()
def strict_json(b):
 def pairs(rows):
  out={}
  for k,v in rows:
   if k in out:raise StudioError('json.duplicate-key: '+k)
   out[k]=v
  return out
 def bad(v):raise StudioError('json.nonfinite: '+v)
 try:
  if isinstance(b,bytes):b=b.decode('utf-8')
  if b.startswith('\ufeff'):raise StudioError('json.bom')
  return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
 except (ValueError,UnicodeError) as e:raise StudioError('json.invalid: '+str(e)) from e
def write_json(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():raise StudioError('Refusing existing output: '+str(p))
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def safe_name(name):
 if not isinstance(name,str) or not name or '\\' in name or '\x00' in name or name.startswith('/') or re.match(r'^[A-Za-z]:',name):raise StudioError('path.unsafe')
 q=name.rstrip('/');parts=q.split('/')
 if not q or any(x in ('','.','..') for x in parts):raise StudioError('path.unsafe')
 if any(any(ord(c)<32 for c in x) for x in parts):raise StudioError('path.control')
 return q

class Package:
 """Read lazily, so a personal envelope is identified without reading credentials/core."""
 def __init__(self,path):
  self.path=Path(path).resolve();self.zip=None;self.names=[];seen={};total=0;directories=set()
  if self.path.is_dir():
   for parent,dirs,files in os.walk(self.path,followlinks=False):
    for n in dirs+files:
     p=Path(parent)/n
     if p.is_symlink():raise StudioError('path.symlink')
    for n in files:
     p=Path(parent)/n;rel=p.relative_to(self.path).as_posix();size=p.stat().st_size
     if not p.is_file():raise StudioError('path.special')
     total+=size;self.names.append(rel)
     if size>MAX_FILE:raise StudioError('zip.file-size')
  else:
   if self.path.stat().st_size>MAX_ARCHIVE:raise StudioError('zip.archive-size')
   try:self.zip=zipfile.ZipFile(self.path)
   except zipfile.BadZipFile as e:raise StudioError('zip.read') from e
   for z in self.zip.infolist():
    n=safe_name(z.filename)
    kind=(z.external_attr>>16)&0o170000
    if kind not in (0,stat.S_IFREG,stat.S_IFDIR):raise StudioError('path.symlink-or-special')
    if z.flag_bits&1:raise StudioError('zip.encrypted')
    if z.is_dir():
     directories.add(unicodedata.normalize('NFC',n).casefold())
     continue
    # The special encrypted/enveloped release is never read by this author tool.
    if z.file_size>MAX_FILE and n!='content/release.bin':raise StudioError('zip.file-size')
    if z.file_size>MAX_ARCHIVE:raise StudioError('zip.file-size')
    if z.file_size>10*1024**2 and z.file_size/max(1,z.compress_size)>200:raise StudioError('zip.bomb')
    total+=z.file_size;self.names.append(n)
  if len(self.names)>MAX_ENTRIES or total>MAX_TOTAL:raise StudioError('zip.bounds')
  for n in self.names:
   safe_name(n);key=unicodedata.normalize('NFC',n).casefold()
   if key in seen:raise StudioError('path.case-unicode-collision: '+n)
   seen[key]=n
  keys=set(seen)
  if keys&directories:raise StudioError('path.file-directory-collision')
  for key in keys:
   if any('/'.join(key.split('/')[:i]) in keys for i in range(1,len(key.split('/')))):raise StudioError('path.file-directory-collision')
 def read(self,name,limit=MAX_FILE):
  n=safe_name(name)
  if n not in self.names:raise StudioError('reference.missing: '+n)
  if self.zip:
   if self.zip.getinfo(n).file_size>limit:raise StudioError('file.bounds')
   try:return self.zip.read(n)
   except (zipfile.BadZipFile,RuntimeError) as e:raise StudioError('zip.crc-or-read') from e
  p=self.path/n
  if p.is_symlink() or not p.resolve().is_relative_to(self.path):raise StudioError('path.escape')
  if p.stat().st_size>limit:raise StudioError('file.bounds')
  return p.read_bytes()
 def obj(self,name):return strict_json(self.read(name,4*1024**2))
 def close(self):
  if self.zip:self.zip.close()
 def __enter__(self):return self
 def __exit__(self,*a):self.close()

def schema_errors(schema,value):
 try:
  from jsonschema import Draft202012Validator
  from referencing import Registry
 except ImportError as e:raise StudioError('dependency.jsonschema: install jsonschema>=4.26,<5') from e
 def deny(uri):raise StudioError('schema.remote-ref-blocked: '+uri)
 try:
  Draft202012Validator.check_schema(schema)
  return [('/'.join(str(x) for x in e.absolute_path) or '$')+': '+e.message for e in Draft202012Validator(schema,registry=Registry(retrieve=deny)).iter_errors(value)]
 except StudioError:raise
 except Exception as e:raise StudioError('schema.invalid-or-unresolved: '+str(e)) from e

def audit(path,verify_integrity=True):
 report={'tool':'motion-template-studio','version':VERSION,'mode':'read-only-static','findings':[],'execution':'NOT_RUN','visual_review':'NOT_RUN','new_content':'NOT_RUN'}
 def note(level,code,message,file=None):
  v={'level':level,'code':code,'message':message}
  if file:v['file']=file
  report['findings'].append(v)
 try:
  with Package(path) as p:
   if 'motion.json' not in p.names:
    note('error','manifest.missing','根目录缺少motion.json；若仅多一层作者目录，可生成非破坏性校正计划。')
    report['status']='FAIL';return report
   m=p.obj('motion.json')
   if not isinstance(m,dict):raise StudioError('manifest.object-required')
   if m.get('packageProfile')=='personal-download-v1' or m.get('specVersion')=='1.0.0-rc.1' and 'personal' in m:
    report.update({'status':'PERSONAL_PACKAGE','identity':'declared-only','execution':'NOT_RUN'})
    note('warning','personal.entry-required','这是个人交付封套；本工具不读Key、不读或解包release.bin/core、不联网验签、不修复封套。按公开入口处理。')
    return report
   schema=strict_json((ROOT/'assets/schemas/motion.schema.json').read_bytes())
   for e in schema_errors(schema,m):note('error','manifest.schema',e,'motion.json')
   if m.get('specVersion')!=CONTENT_VERSION:note('error','manifest.version','仅支持精确内容版本 '+CONTENT_VERSION)
   if m.get('format')!='motiongit-template':note('error','manifest.format','format必须为motiongit-template')
   report['template']={k:m.get('template',{}).get(k) for k in ['id','name','version']}
   runtime=m.get('runtime',{});report['runtime']=runtime
   report['runner_supported']=runtime.get('profile')=='html-canvas/1'
   if not report['runner_supported']:note('warning','runtime.adapter-required','本工具的便携渲染器只验证html-canvas/1；其它profile保留原入口并单独运行，静态可读不等于可执行。')
   refs=[]
   for parent,key in [('runtime','entry'),('runtime','dependencyLock'),('parameters','schema'),('parameters','defaultPreset'),('parameters','mapping'),('assets','manifest'),('ai','entry'),('ai','guide'),('license','file')]:
    v=m.get(parent,{}).get(key)
    if v is not None:refs.append((parent+'.'+key,v))
   if verify_integrity and m.get('integrity'):refs.append(('integrity',m['integrity']))
   for label,v in refs:
    try:
     safe_name(v)
     if v not in p.names:note('error','reference.missing',label+'指向缺失文件',v)
    except StudioError:note('error','reference.unsafe',label+'不是包内相对安全路径')
   params=None
   if m.get('parameters',{}).get('schema') in p.names:
    params=p.obj(m['parameters']['schema'])
    if not isinstance(params,dict) or params.get('type')!='object':note('error','params.shape','参数Schema顶层必须为object')
    else:
     if params.get('additionalProperties') is not False:note('warning','params.open','建议显式限制未知参数')
     preset=m.get('parameters',{}).get('defaultPreset')
     if preset in p.names:
      for e in schema_errors(params,p.obj(preset)):note('error','params.preset',e,preset)
   else:note('error','params.missing','完整可复用作者模板需要真实参数Schema')
   variants=m.get('variants',[])
   if isinstance(variants,list):
    ids=set()
    for v in variants:
     if not isinstance(v,dict):continue
     if v.get('id') in ids:note('error','variants.duplicate','重复的样式ID')
     ids.add(v.get('id'))
     for key in ['preset','preview']:
      if key in v:
       try:
        safe_name(v[key])
        if v[key] not in p.names:note('error','variants.reference','样式引用缺失',v[key])
        elif key=='preset' and params:
         for e in schema_errors(params,p.obj(v[key])):note('error','variants.params',e,v[key])
       except StudioError as e:note('error','variants.unsafe',str(e))
   guidepath=m.get('ai',{}).get('guide','guide.json')
   if guidepath in p.names:
    g=p.obj(guidepath);props=set(params.get('properties',{})) if isinstance(params,dict) else set()
    if not isinstance(g,dict):raise StudioError('guide.object-required')
    if not g.get('fit',{}).get('summary'):note('error','guide.fit','指南缺少适用摘要')
    dur=g.get('duration',{})
    if dur.get('policy')!=m.get('output',{}).get('durationPolicy'):note('error','guide.duration','guide与output时长策略不一致')
    if dur.get('policy') not in ('fixed',None):
     v=dur.get('param')
     if v not in props:note('error','guide.duration-param','可变时长缺少对应参数')
    roles={'video.presenter','video.footage','video.screen','image.photo','image.product','image.logo','image.screenshot','audio.voiceover','audio.music','text.subtitles','text.script','text.facts'}
    for a in g.get('materials',[]):
     if not isinstance(a,dict):note('error','guide.materials','素材项必须为对象');continue
     if a.get('role') not in roles and not str(a.get('role','')).startswith('x-'):note('error','guide.role','未知素材角色')
     if not a.get('use') or not a.get('ask'):note('error','guide.materials','素材须说明use和ask')
     if a.get('required') is False and not a.get('ifMissing'):note('error','guide.if-missing','可选素材缺少ifMissing')
     if any(x not in props for x in a.get('maps',[])):note('error','guide.param-unknown','素材绑定到未声明参数')
    for a in g.get('copy',[]):
     if not isinstance(a,dict) or a.get('param') not in props:note('error','guide.param-unknown','copy指向未声明参数')
   else:note('error','guide.missing','完整模板需要可读的使用与容量说明')
   for n in p.names:
    parts=PurePosixPath(n).parts
    if any(x in FORBIDDEN for x in parts) or any(x in BLOCKED_DIRS for x in parts):note('error','content.forbidden','发行包含凭据/自动加载指令/依赖缓存等禁止项',n)
    if n.endswith(('.json','.md','.js','.mjs','.ts','.html','.css','.py','.txt')):
     b=p.read(n);s=b.decode('utf-8',errors='replace')
     if re.search(r'\bmgk_[A-Za-z0-9_-]{32}\b|\bsk-[A-Za-z0-9_-]{24,}',s):note('error','content.credential','检测到疑似凭据；报告不输出其值',n)
   if not m.get('license',{}).get('file'):note('error','license.missing','缺少模板许可引用')
   assetpath=m.get('assets',{}).get('manifest')
   if assetpath in p.names:
    am=p.obj(assetpath)
    if not isinstance(am,dict) or not isinstance(am.get('assets'),list):note('warning','assets.contract-unknown','资源清单不是本工具认识的assets列表；需要对应适配器审查')
    else:
     for item in am['assets']:
      if not isinstance(item,dict):note('error','assets.shape','资源项必须为对象');continue
      if item.get('bundled') is True:
       ap=item.get('path')
       try:
        safe_name(ap)
        if ap not in p.names:note('error','assets.missing','声明随包的素材缺失',ap)
        elif item.get('sha256') and item['sha256']!=digest(p.read(ap)):note('error','assets.hash','素材摘要不匹配',ap)
       except StudioError:note('error','assets.path','资源路径无效')
      if not item.get('license') or not item.get('source'):note('warning','assets.provenance','资源缺少来源或许可记录')
   if verify_integrity:
    ip=m.get('integrity','integrity.json')
    if ip not in p.names:note('error','integrity.missing','缺少完整性清单')
    else:
     integ=p.obj(ip);members=integ.get('files',{})
     if integ.get('algorithm')!='sha256' or not isinstance(members,dict):note('error','integrity.shape','需要algorithm=sha256与files映射')
     else:
      if set(members)!=set(p.names)-{ip}:note('error','integrity.membership','摘要成员集合与包内容不一致')
      for n,h in members.items():
       if n in p.names and digest(p.read(n))!=h:note('error','integrity.mismatch','文件摘要不匹配',n)
   report['source_sha256']=digest(Path(path).read_bytes()) if Path(path).is_file() else digest(json.dumps({n:digest(p.read(n)) for n in sorted(p.names)},sort_keys=True).encode())
 except (StudioError,OSError,KeyError,TypeError,AttributeError) as e:note('error','package.invalid',str(e))
 report['status']='FAIL' if any(x['level']=='error' for x in report['findings']) else 'STATIC_PASS'
 report['limits']='静态检查不证明执行、参数画面、连续运动/声音、许可所有权或独立用户验收。'
 return report

def repair_plan(path):
 before=audit(path);fixes=[]
 if before.get('status')=='PERSONAL_PACKAGE':return {'source_sha256':digest(Path(path).read_bytes()),'fixes':[],'blocked':'personal-package','audit':before}
 with Package(path) as p:
  names=p.names
  if 'motion.json' not in names:
   roots={n.split('/')[0] for n in names}
   if len(roots)==1:
    root=next(iter(roots))+'/'
    if root+'motion.json' in names:
     m=p.obj(root+'motion.json')
     if m.get('specVersion')==CONTENT_VERSION and m.get('format')=='motiongit-template':fixes.append({'operation':'flatten-root','prefix':root})
  codes={x['code'] for x in before.get('findings',[])}
  if codes&{'integrity.missing','integrity.membership','integrity.mismatch'}:fixes.append({'operation':'rebuild-integrity'})
 return {'profile':'motion-template-studio.repair-plan/1','source_sha256':digest(Path(path).read_bytes()),'fixes':fixes,'audit':before,'limits':'仅校正作者包根目录或重算完整性；不会修复视觉、改动动画源码、伪造验签或替换资源。'}

def repair(path,planpath,output):
 if Path(output).exists():raise StudioError('Refusing existing output')
 plan=strict_json(Path(planpath).read_bytes());sha=digest(Path(path).read_bytes())
 if plan.get('source_sha256')!=sha:raise StudioError('repair.stale-source')
 actual=repair_plan(path)
 if plan.get('fixes')!=actual.get('fixes') or not actual.get('fixes'):raise StudioError('repair.plan-mismatch-or-empty')
 with Package(path) as p:
  if actual.get('blocked'):raise StudioError('repair.personal-blocked')
  files={n:p.read(n) for n in p.names}
 for fix in plan['fixes']:
  if fix['operation']=='flatten-root':files={n[len(fix['prefix']):]:b for n,b in files.items()}
 m=strict_json(files['motion.json'])
 if m.get('specVersion')!=CONTENT_VERSION or m.get('packageProfile'):raise StudioError('repair.author-only')
 ip=m.get('integrity','integrity.json');safe_name(ip)
 m['integrity']=ip;files['motion.json']=(json.dumps(m,ensure_ascii=False,indent=2)+'\n').encode()
 files[ip]=(json.dumps({'algorithm':'sha256','files':{n:digest(b) for n,b in sorted(files.items()) if n!=ip}},ensure_ascii=False,indent=2)+'\n').encode()
 out=Path(output);out.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(files.items()):
   i=zipfile.ZipInfo(n,(2020,1,1,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b)
 checked=audit(out)
 return {'status':'FAIL' if checked['status']=='FAIL' else 'STATIC_CORRECTED','source_sha256':sha,'output_sha256':digest(out.read_bytes()),'fixes':plan['fixes'],'audit':checked,'trust':'重算哈希不是真实性认证；仍需实际源码/运行/画面检查。'}

def probe(path):
 p=Path(path).resolve()
 r=subprocess.run(['ffprobe','-v','error','-show_entries','format=start_time,duration:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,start_time,duration,sample_rate,channel_layout','-of','json',str(p)],capture_output=True,text=True)
 if r.returncode:raise StudioError('ffprobe failed: '+r.stderr[:500])
 return {'source_sha256':digest(p.read_bytes()),'source_name':p.name,'probe':strict_json(r.stdout),'scope':'媒体元数据，不是内容识别或画面验收。'}
def samples(path,out,times):
 p=Path(out)
 if p.exists():raise StudioError('Refusing existing sample directory')
 facts=probe(path);duration=float(facts['probe'].get('format',{}).get('duration',0));p.mkdir(parents=True)
 rows=[]
 for i,t in enumerate(times):
  if not math.isfinite(t) or t<0 or t>=duration:raise StudioError('sample.time-range')
  f=p/('reference-'+str(i).zfill(3)+'.png')
  r=subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(Path(path).resolve()),'-frames:v','1','-update','1',str(f)],capture_output=True,text=True)
  if r.returncode or not f.exists():raise StudioError('frame extraction failed: '+r.stderr[:300])
  rows.append({'time_seconds':t,'file':f.name,'sha256':digest(f.read_bytes())})
 result={'source_sha256':facts['source_sha256'],'frames':rows,'continuous_review':'NOT_RUN','note':'抽帧不代表已完整观看。关键变化前后应追加实际相邻时间点。'}
 write_json(p/'samples.json',result);return result

def validate_observations(path):
 j=strict_json(Path(path).read_bytes());schema=strict_json((ROOT/'assets/schemas/observations.schema.json').read_bytes());errors=schema_errors(schema,j)
 seen=set()
 if errors:return {'status':'FAIL','errors':errors,'scope':'字段结构不合法，未执行后续区间检查。'}
 for s in j.get('scenes',[]):
  if s['id'] in seen:errors.append('duplicate scene id')
  seen.add(s['id'])
  if s['end']<=s['start'] or s['end']>j.get('duration',0):errors.append(s['id']+': invalid source interval')
  for a in s.get('observations',[]):
   if a.get('end',s['end'])<a.get('start',s['start']) or a.get('start',s['start'])<s['start'] or a.get('end',s['end'])>s['end']:errors.append(s['id']+': observation time outside scene')
 if j.get('continuous_review')=='COMPLETE':
  cursor=0
  for s in sorted(j['scenes'],key=lambda x:x['start']):
   if abs(s['start']-cursor)>0.001:errors.append('COMPLETE timeline has a gap or overlap')
   cursor=s['end']
  if abs(cursor-j['duration'])>0.001:errors.append('COMPLETE timeline does not reach end')
 return {'status':'PASS' if not errors else 'FAIL','errors':errors,'scope':'字段、区间与来源结构；未自动认证视觉观察正确。'}

def catalog_path(kb=None):
 if kb:
  p=Path(kb)/'knowledge/catalog.json'
  if not p.is_file():raise StudioError('knowledge.catalog-missing')
  return p
 return ROOT/'assets/catalog.json'
def search(query,engine=None,kind=None,kb=None):
 data=strict_json(catalog_path(kb).read_bytes());terms=set(re.findall(r'[a-z0-9-]+|[\u4e00-\u9fff]',query.lower()));rows=[]
 for a in data['assets']:
  if kind and a.get('type')!=kind:continue
  text=json.dumps(a,ensure_ascii=False).lower();matched=sorted(t for t in terms if t in text)
  if not matched:continue
  compatible=not engine or a.get('engine') in (engine,'agnostic')
  rows.append({'asset':a,'match_terms':matched,'rank_score':len(matched),'compatibility':'matching-declaration' if compatible else 'needs-adapter','verification':a.get('verification','NOT_RUN')})
 rows.sort(key=lambda x:(x['compatibility']=='matching-declaration',x['rank_score']),reverse=True)
 return {'results':rows[:20],'query':query,'score_meaning':'词项匹配排序，不是识别准确率、可执行证明或质量评分。'}

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**k):raise StudioError('official.redirect-blocked')
def public_get(url):
 from urllib.parse import urlsplit
 u=urlsplit(url)
 if u.scheme!='https' or u.hostname!='motiongit.com' or u.username or u.password:raise StudioError('official.origin')
 with urllib.request.build_opener(NoRedirect()).open(url,timeout=30) as r:
  b=r.read(8*1024**2+1)
  if len(b)>8*1024**2:raise StudioError('official.size')
  return b
def official_tool(destination,offline=False):
 out=Path(destination)
 if out.exists():raise StudioError('Refusing existing tool directory')
 if offline:
  cache=os.environ.get('MOTION_STUDIO_OFFICIAL_BUNDLE')
  if not cache:raise StudioError('offline.helper-unavailable: set MOTION_STUDIO_OFFICIAL_BUNDLE to the previously downloaded public official ZIP; official code is not redistributed in this Skill')
  b=Path(cache).read_bytes();lock=strict_json((ROOT/'assets/official/lock.json').read_bytes())
  if digest(b)!=lock['bundle_sha256']:raise StudioError('official.bundle-hash')
 else:b=public_get('https://motiongit.com/skill/motiongit-skill.zip')
 with tempfile.NamedTemporaryFile(suffix='.zip') as f:
  f.write(b);f.flush()
  with Package(f.name) as p:
   build=p.obj('motiongit/BUILD.json');v=build.get('helperVersion','')
   if not re.fullmatch(r'1\.0\.0-rc\.[1-9][0-9]*',v):raise StudioError('official.version-unreviewed')
   meta=lock['metadata'] if offline else strict_json(public_get('https://motiongit.com/assets/motion-runtimes/'+v+'.json'))
   script=p.read('motiongit/scripts/motion.mjs')
   for obj in [build,meta]:
    if obj.get('helperVersion')!=v or obj.get('bytes')!=len(script) or obj.get('sha256')!=digest(script):raise StudioError('official.helper-hash')
   out.mkdir(parents=True)
   for n in p.names:
    if not n.startswith('motiongit/'):continue
    target=out/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read(n))
   write_json(out/'verified.json',{'version':v,'script_sha256':digest(script),'bytes':len(script),'mode':'frozen-offline' if offline else 'fresh-public-download','scope':'仅公共GET；没有发送素材、个人Key或模板内容。'})
 return out/'motiongit/scripts/motion.mjs'
def pack(project,output,offline=False):
 if Path(output).exists():raise StudioError('Refusing existing output')
 r=audit(project,False)
 if r['status']!='STATIC_PASS':raise StudioError('pack.preflight-failed: '+json.dumps(r,ensure_ascii=False))
 with tempfile.TemporaryDirectory(prefix='motion-author-tool-') as t:
  helper=official_tool(Path(t)/'tools',offline)
  r=subprocess.run(['node',str(helper),'pack',str(Path(project).resolve()),str(Path(output).resolve())],capture_output=True,text=True)
  if r.returncode:raise StudioError('official.pack-failed: '+(r.stdout+r.stderr)[-2000:])
 checked=audit(output)
 return {'status':'FAIL' if checked['status']=='FAIL' else 'STATIC_PACKED','package_sha256':digest(Path(output).read_bytes()),'tool':'official MotionGit author helper','mode':'frozen-offline' if offline else 'fresh-verified','audit':checked}

def init_project(path,name):
 p=Path(path)
 if p.exists():raise StudioError('Refusing existing project')
 shutil.copytree(ROOT/'assets/starter',p)
 m=strict_json((p/'motion.json').read_bytes());m['template']['id']=name;m['template']['name']=name
 (p/'motion.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 return {'project':str(p.resolve()),'status':'SCAFFOLD_ONLY','note':'这是可编辑诊断骨架，不是从用户视频重建出的模板；必须替换实现并实际验收。'}

def verify_render(path,manifest=None):
 p=Path(path);r=subprocess.run(['ffprobe','-v','error','-count_frames','-show_entries','format=duration:stream=codec_type,width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(p)],capture_output=True,text=True)
 if r.returncode:raise StudioError('ffprobe failed')
 facts=strict_json(r.stdout);errors=[]
 video=next((x for x in facts['streams'] if x.get('codec_type')=='video'),None)
 if not video:errors.append('no video stream')
 if manifest and video:
  m=strict_json(Path(manifest).read_bytes());o=m['output'];fps=Fraction(o['fps']['num'],o['fps']['den'])
  if (video.get('width'),video.get('height'))!=(o['width'],o['height']):errors.append('dimensions mismatch')
  if Fraction(video.get('avg_frame_rate','0/1'))!=fps:errors.append('fps mismatch')
  if o.get('durationPolicy')=='fixed':
   expected=math.ceil(float(o['durationSeconds'])*float(fps)-1e-9)
   if int(video.get('nb_read_frames',-1))!=expected:errors.append('frame count mismatch')
 dec=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
 if dec.returncode or dec.stderr.strip():errors.append('full decode failed or errors: '+dec.stderr[:300])
 return {'status':'PASS' if not errors else 'FAIL','errors':errors,'media':facts,'sha256':digest(p.read_bytes()),'scope':'编码与完整解码；画面、运动、所讲事实、声音内容和试听仍需另验。','visual_review':'NOT_RUN','listening':'NOT_RUN'}

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 a=sub.add_parser('audit');a.add_argument('path');a.add_argument('--out')
 a=sub.add_parser('repair-plan');a.add_argument('path');a.add_argument('--out',required=True)
 a=sub.add_parser('repair');a.add_argument('path');a.add_argument('--plan',required=True);a.add_argument('--out',required=True)
 a=sub.add_parser('probe');a.add_argument('path');a.add_argument('--out')
 a=sub.add_parser('samples');a.add_argument('path');a.add_argument('--out',required=True);a.add_argument('--times',required=True,help='comma-separated seconds')
 a=sub.add_parser('validate-observations');a.add_argument('path')
 a=sub.add_parser('search');a.add_argument('query');a.add_argument('--engine');a.add_argument('--type',dest='kind');a.add_argument('--kb')
 a=sub.add_parser('fetch-official');a.add_argument('--out',required=True);a.add_argument('--offline',action='store_true')
 a=sub.add_parser('pack');a.add_argument('project');a.add_argument('--out',required=True);a.add_argument('--offline',action='store_true')
 a=sub.add_parser('init');a.add_argument('path');a.add_argument('--name',default='reference-template')
 a=sub.add_parser('verify-render');a.add_argument('path');a.add_argument('--manifest');a.add_argument('--out')
 a=sub.add_parser('doctor')
 args=parser.parse_args(argv)
 try:
  c=args.command
  if c=='audit':result=audit(args.path)
  elif c=='repair-plan':result=repair_plan(args.path)
  elif c=='repair':result=repair(args.path,args.plan,args.out)
  elif c=='probe':result=probe(args.path)
  elif c=='samples':result=samples(args.path,args.out,[float(x) for x in args.times.split(',')])
  elif c=='validate-observations':result=validate_observations(args.path)
  elif c=='search':result=search(args.query,args.engine,args.kind,args.kb)
  elif c=='fetch-official':result={'helper':str(official_tool(args.out,args.offline))}
  elif c=='pack':result=pack(args.project,args.out,args.offline)
  elif c=='init':result=init_project(args.path,args.name)
  elif c=='verify-render':result=verify_render(args.path,args.manifest)
  elif c=='doctor':result={'python':sys.version.split()[0],'tools':{x:shutil.which(x) for x in ['node','ffmpeg','ffprobe','chromium','google-chrome']},'render':'NOT_RUN','note':'二进制存在不证明当前环境允许渲染。'}
  if getattr(args,'out',None) and c in ['audit','probe','repair-plan','verify-render']:write_json(args.out,result)
  print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
  return 1 if result.get('status')=='FAIL' else 0
 except (StudioError,OSError,ValueError,subprocess.SubprocessError) as e:
  print(json.dumps({'status':'ERROR','error':str(e)},ensure_ascii=False),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
