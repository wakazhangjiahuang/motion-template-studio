/** Local author adapter. API: --project DIR --inputs FILE --out NEW.mp4 (--silent | --audio-plan FILE).
 * Audio plan: {tracks:[{file: relative-to-plan, role: voiceover|music|sfx, start:0, offset:0, duration?:seconds, gain:1}]}.
 * Native HTML audio/video/WebAudio are not supported. No remote assets. No template is executed by static audit.
 */
import fs from 'node:fs/promises';import path from 'node:path';import http from 'node:http';import crypto from 'node:crypto';import {spawnSync} from 'node:child_process';import {createRequire} from 'node:module';import {pathToFileURL} from 'node:url';
const argv=process.argv.slice(2),opts={};for(let i=0;i<argv.length;i++){if(argv[i]==='--silent')opts.silent=true;else if(argv[i].startsWith('--'))opts[argv[i].slice(2)]=argv[++i];else throw Error('Unknown argument')}
for(const k of ['project','inputs','out'])if(!opts[k])throw Error('Missing --'+k);
const project=await fs.realpath(opts.project),output=path.resolve(opts.out);
try{await fs.stat(output);throw Error('Refusing existing output')}catch(e){if(e.code!=='ENOENT')throw e}
const m=JSON.parse(await fs.readFile(path.join(project,'motion.json'),'utf8'));if(m.runtime.profile!=='html-canvas/1')throw Error('RUNTIME_UNSUPPORTED');
const o=m.output,fps=o.fps.num/o.fps.den,count=Math.ceil(o.durationSeconds*fps-1e-9);
if(o.durationPolicy!=='fixed'||m.permissions.network!==false||!Number.isInteger(o.width)||!Number.isInteger(o.height)||o.width%2||o.height%2||o.width>4096||o.height>4096||fps<1||fps>120||o.durationSeconds>600||count>36000)throw Error('Profile capability mismatch');
const py=spawnSync(process.env.PYTHON||'python3',[path.join(project,'tools/inputs.py'),project,path.resolve(opts.inputs)],{encoding:'utf8'});if(py.status!==0)throw Error('Input validation failed: '+py.stderr.slice(0,500));const inputs=JSON.parse(py.stdout);
const req=createRequire(import.meta.url);let modulePath=process.env.MOTION_PLAYWRIGHT_MODULE;
if(!modulePath&&process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES)modulePath=path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright/index.mjs');
if(!modulePath){try{modulePath=req.resolve('playwright')}catch{modulePath=req.resolve('playwright-core')}}
const {chromium}=await import(pathToFileURL(modulePath));
await fs.mkdir(path.dirname(output),{recursive:true});const run=await fs.mkdtemp(path.join(path.dirname(output),'motion-render-'));await fs.mkdir(path.join(run,'frames'));
const report={sourceManifestSha256:crypto.createHash('sha256').update(await fs.readFile(path.join(project,'motion.json'))).digest('hex'),inputsSha256:crypto.createHash('sha256').update(JSON.stringify(inputs)).digest('hex'),status:'NOT_RUN',visualReview:'NOT_RUN',listening:'NOT_RUN',frames:count,mediaProfile:'html-canvas/1; external explicit audio plan only'};
const blocked=[];const server=http.createServer(async(req,res)=>{try{const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1);const p=await fs.realpath(path.join(project,name));if(!(p===project||p.startsWith(project+path.sep)))throw Error('outside root');if(!(await fs.stat(p)).isFile())throw Error('not file');const ext=path.extname(p);res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.json':'application/json','.css':'text/css','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2'})[ext]||'application/octet-stream');res.end(await fs.readFile(p))}catch{res.writeHead(404);res.end()}});
let browser;
try{
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});const origin='http://127.0.0.1:'+server.address().port;
 browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),args:['--no-sandbox']});
 async function page(){const c=await browser.newContext({viewport:{width:o.width,height:o.height},deviceScaleFactor:1,serviceWorkers:'block'});await c.route('**/*',r=>{if(r.request().url().startsWith(origin+'/'))return r.continue();blocked.push('external resource');return r.abort()});if(typeof c.routeWebSocket!=='function')throw Error('Browser adapter cannot enforce network=false for WebSockets');await c.routeWebSocket('**/*',ws=>{blocked.push('WebSocket blocked');ws.close()});const p=await c.newPage();p.on('pageerror',e=>blocked.push(e.message));await p.addInitScript(()=>{window.AudioContext=window.webkitAudioContext=class{constructor(){throw Error('WebAudio requires another adapter')}}});await p.goto(origin+'/'+m.runtime.entry);await p.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));if(document.querySelector('video,audio'))throw Error('Embedded audio/video requires another adapter')});return p}
 const p=await page();const seek=async(page,n)=>{await page.evaluate(async({n,inputs})=>{if(typeof window.renderFrame==='function')await window.renderFrame(n,inputs);else if(typeof window.seek==='function')await window.seek(n*window.__motionDen/window.__motionNum,inputs);else throw Error('Missing frame API')},{n,inputs});return page.screenshot({type:'png'})};
 await p.evaluate(({num,den})=>{window.__motionNum=num;window.__motionDen=den},o.fps);
 const n=Math.floor(count/2),a=await seek(p,n);await seek(p,count-1);const b=await seek(p,n),fresh=await page();await fresh.evaluate(({num,den})=>{window.__motionNum=num;window.__motionDen=den},o.fps);const c=await seek(fresh,n);
 const sha=b=>crypto.createHash('sha256').update(b).digest('hex');if(sha(a)!==sha(b)||sha(a)!==sha(c))throw Error('Independent seeking differs');report.seekCheck='PASS';
 for(let f=0;f<count;f++){await fs.writeFile(path.join(run,'frames',String(f).padStart(6,'0')+'.png'),await seek(p,f));if(blocked.length)throw Error(blocked.join('; '))}
 const tracks=opts['audio-plan']?JSON.parse(await fs.readFile(opts['audio-plan'],'utf8')).tracks:[];
 if(!Array.isArray(tracks)||tracks.length>16)throw Error('Invalid audio plan');if(!tracks.length&&!opts.silent)throw Error('Explicit --silent or actual audio-plan required');
 const cmd=['-v','error','-framerate',o.fps.num+'/'+o.fps.den,'-i',path.join(run,'frames','%06d.png')],filters=[],labels=[];
 for(let i=0;i<tracks.length;i++){
  const t=tracks[i],base=await fs.realpath(path.dirname(path.resolve(opts['audio-plan']))),f=await fs.realpath(path.resolve(base,t.file));if(!f.startsWith(base+path.sep))throw Error('Audio outside plan vault');if(!['voiceover','music','sfx'].includes(t.role))throw Error('Audio role');
  const pr=spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','json',f],{encoding:'utf8'});if(pr.status!==0)throw Error('Audio probe failed');const available=Number(JSON.parse(pr.stdout).format.duration),offset=t.offset??0,start=t.start??0,duration=t.duration??(available-offset),gain=t.gain??1;
  if(![offset,start,duration,gain].every(Number.isFinite)||offset<0||start<0||duration<=0||gain<0||gain>4||offset+duration>available+0.01||start+duration>count/fps+0.01)throw Error('Audio range/gain');if(t.role==='voiceover'&&(offset>0||duration<available-0.01)&&!t.explicitVoiceSelection)throw Error('Voice trim requires an explicit selection contract');
  cmd.push('-i',f);const label='a'+i;filters.push(`[${i+1}:a]atrim=start=${offset}:duration=${duration},asetpts=PTS-STARTPTS,volume=${gain},adelay=${Math.round(start*1000)}:all=1[${label}]`);labels.push('['+label+']');
 }
 cmd.push('-map','0:v:0');if(labels.length){filters.push(labels.join('')+`amix=inputs=${labels.length}:normalize=0,apad,atrim=duration=${count/fps}[mix]`);cmd.push('-filter_complex',filters.join(';'),'-map','[mix]','-c:a','aac')}else cmd.push('-an');
 cmd.push('-frames:v',String(count),'-c:v','libx264','-pix_fmt','yuv420p',path.join(run,'encoded.mp4'));const enc=spawnSync('ffmpeg',cmd,{encoding:'utf8'});if(enc.status!==0)throw Error('FFmpeg: '+enc.stderr.slice(0,1000));
 const dec=spawnSync('ffmpeg',['-v','error','-i',path.join(run,'encoded.mp4'),'-f','null','-'],{encoding:'utf8'});if(dec.status!==0||dec.stderr.trim())throw Error('Full decode failed');
 await fs.rename(path.join(run,'encoded.mp4'),output);report.status='TECHNICAL_RENDERED';report.outputSha256=sha(await fs.readFile(output));report.browser=browser.version();report.audioTracks=tracks.map(t=>({role:t.role,start:t.start??0}));
}catch(e){report.status='FAIL';report.error=String(e).slice(0,1800);process.exitCode=1}
finally{await browser?.close();await new Promise(r=>server.close(r));await fs.writeFile(path.join(run,'render-report.json'),JSON.stringify(report,null,2));if(report.status==='TECHNICAL_RENDERED')await fs.writeFile(output+'.json',JSON.stringify(report,null,2));console.log(JSON.stringify({...report,recordDirectory:run},null,2))}
