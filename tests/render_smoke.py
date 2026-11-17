"""Real browser/FFmpeg smoke test. Synthetic fixture, never user-video fidelity certification."""
from pathlib import Path
import json,os,subprocess,sys,zipfile,hashlib
R=Path(__file__).resolve().parents[1];S=R/'skills/motion-template-studio';W=R/'workspaces/ci-render'
sys.path.insert(0,str(S/'scripts'));import motion_studio as studio
if W.exists():raise SystemExit('Use a fresh CI workspace')
W.mkdir(parents=True)
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','MOTION_PLAYWRIGHT_MODULE':str(R/'workspaces/browser/node_modules/playwright/index.mjs')}
checks=[]
report={'scope':'Synthetic diagnostic, real browser rendering and audio encoding; no reference fidelity or listening claim','visual_reference':'NOT_RUN','listening':'NOT_RUN','checks':checks}
def run(args,expected=0):
 p=subprocess.run([str(a) for a in args],cwd=R,env=env,capture_output=True,text=True)
 i=len(list(W.glob('command-*.log')));(W/f'command-{i:02}.log').write_text(p.stdout+'\n'+p.stderr)
 if (expected==0 and p.returncode!=0) or (expected!=0 and p.returncode==0):raise RuntimeError(f'Unexpected exit {p.returncode}: {args[0]}: '+p.stderr[-1600:])
 return p
def render(project,inputs,out,audio=None):
 args=['node',project/'tools/render.mjs','--project',project,'--inputs',inputs,'--out',out]
 args+=['--audio-plan',audio] if audio else ['--silent']
 run(args);checked=studio.verify_render(out,project/'motion.json')
 if checked['status']!='PASS':raise RuntimeError(str(checked))
 meta=json.loads(Path(str(out)+'.json').read_text())
 if meta.get('seekCheck')!='PASS' or meta.get('status')!='TECHNICAL_RENDERED':raise RuntimeError('Rendering did not pass deterministic seeking')
 return {'sha256':checked['sha256'],'seek':'PASS','full_decode':'PASS','streams':checked['media']['streams']}
try:
 P=W/'project';studio.init_project(P,'ci-diagnostic')
 defaults=P/'presets/demo.json';x=render(P,defaults,W/'default.mp4');checks.append({'id':'default-browser-render','status':'PASS',**x})
 # Exercise actual font metrics, Chinese boundary text and maximum list count.
 inputs=W/'new-content.json';studio.write_json(inputs,{'title':'长'*28,'accent':'#853B4A','items':['字'*14 for _ in range(5)]})
 run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=3',W/'voice-test.wav'])
 run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=220:duration=3',W/'music-test.wav'])
 plan=W/'audio-plan.json';studio.write_json(plan,{'tracks':[{'file':'voice-test.wav','role':'voiceover','gain':1},{'file':'music-test.wav','role':'music','gain':0.25}]})
 x=render(P,inputs,W/'new-content-audio.mp4',plan)
 audio=[a for a in x['streams'] if a['codec_type']=='audio']
 if not audio or abs(float(audio[0].get('duration',0))-3)>0.1:raise RuntimeError('Audio stream duration missing or mismatched')
 checks.append({'id':'boundary-Chinese-new-content-and-audio','status':'PASS',**x})
 too_long=W/'too-long.json';studio.write_json(too_long,{'title':'长'*29})
 run(['node',P/'tools/render.mjs','--project',P,'--inputs',too_long,'--out',W/'must-not-exist.mp4','--silent'],expected=1)
 if (W/'must-not-exist.mp4').exists():raise RuntimeError('Invalid input produced output')
 checks.append({'id':'over-capacity-rejected','status':'PASS'})
 packed=studio.pack(P,W/'diagnostic.motion')
 if packed.get('status')!='STATIC_PACKED':raise RuntimeError('Author pack failed')
 studio.write_json(W/'pack-report.json',packed);checks.append({'id':'fresh-official-author-pack','status':'PASS','sha256':packed['package_sha256']})
 clean=W/'clean-project';clean.mkdir()
 with zipfile.ZipFile(W/'diagnostic.motion') as z:z.extractall(clean)
 if studio.audit(clean)['status']!='STATIC_PASS':raise RuntimeError('Clean package failed audit')
 x=render(clean,clean/'presets/demo.json',W/'clean-replay.mp4');checks.append({'id':'clean-folder-real-browser-replay','status':'PASS',**x})
 # Compare decoded pixels rather than container metadata/encoder headers.
 for stem in ['default','clean-replay']:run(['ffmpeg','-v','error','-i',W/(stem+'.mp4'),'-map','0:v:0','-f','framemd5',W/(stem+'.framemd5')])
 if (W/'default.framemd5').read_bytes()!=(W/'clean-replay.framemd5').read_bytes():raise RuntimeError('Clean-folder output pixels differ')
 checks.append({'id':'clean-replay-decoded-frame-hashes','status':'PASS'})
 report.update({'status':'PASS','node':run(['node','--version']).stdout.strip(),'python':sys.version.split()[0],'browser':json.loads((W/'default.mp4.json').read_text())['browser']})
except Exception as e:
 report.update({'status':'FAIL','error':str(e)});raise
finally:
 (W/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
