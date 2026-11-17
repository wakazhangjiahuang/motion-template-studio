"""Local regression tests. Synthetic artifacts are never user reference reconstructions."""
import copy,hashlib,json,os,shutil,stat,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import motion_studio as s

def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def fixture_files():
 root=s.ROOT/'assets/starter'
 return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
def freeze(files):
 f=copy.deepcopy(files);m=s.strict_json(f['motion.json']);ip=m.get('integrity','integrity.json')
 f[ip]=encode({'algorithm':'sha256','files':{n:s.digest(b) for n,b in sorted(f.items()) if n!=ip}});return f
def archive(path,files):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for n,b in files.items():z.writestr(n,b)
 return path

class AuditTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.files=freeze(fixture_files())
 def tearDown(self):self.tmp.cleanup()
 def audit(self,files):return s.audit(archive(self.root/'case.motion',files))
 def codes(self,r):return {v['code'] for v in r['findings']}
 def test_complete_diagnostic_static_only(self):
  r=self.audit(self.files);self.assertEqual(r['status'],'STATIC_PASS');self.assertEqual(r['visual_review'],'NOT_RUN');self.assertEqual(r['execution'],'NOT_RUN')
 def test_missing_manifest(self):
  del self.files['motion.json'];self.assertIn('manifest.missing',self.codes(self.audit(self.files)))
 def test_wrong_content_version(self):
  m=s.strict_json(self.files['motion.json']);m['specVersion']='1.0.0';self.files['motion.json']=encode(m)
  self.assertIn('manifest.version',self.codes(self.audit(freeze(self.files))))
 def test_duplicate_json(self):
  self.files['motion.json']=b'{"format":"a","format":"b"}';self.assertEqual(self.audit(self.files)['status'],'FAIL')
 def test_reference_missing(self):
  del self.files['src/index.html'];self.assertIn('reference.missing',self.codes(self.audit(freeze(self.files))))
 def test_invalid_preset(self):
  self.files['presets/demo.json']=encode({'title':'x'*29,'items':['ok'],'accent':'#123456'});self.assertIn('params.preset',self.codes(self.audit(freeze(self.files))))
 def test_variant_unknown_param(self):
  m=s.strict_json(self.files['motion.json']);m['variants']=[{'id':'extra','name':'Extra','preset':'presets/extra.json'}];self.files['motion.json']=encode(m);self.files['presets/extra.json']=encode({'title':'ok','accent':'#123456','items':['ok'],'unknown':3})
  self.assertIn('variants.params',self.codes(self.audit(freeze(self.files))))
 def test_duplicate_variant(self):
  m=s.strict_json(self.files['motion.json']);m['variants']=[{'id':'a','name':'A','preset':'presets/demo.json'}]*2;self.files['motion.json']=encode(m)
  self.assertIn('variants.duplicate',self.codes(self.audit(freeze(self.files))))
 def test_guide_duration(self):
  g=s.strict_json(self.files['guide.json']);g['duration']['policy']='audio';self.files['guide.json']=encode(g);self.assertIn('guide.duration',self.codes(self.audit(freeze(self.files))))
 def test_guide_unknown_copy(self):
  g=s.strict_json(self.files['guide.json']);g['copy'][0]['param']='nothere';self.files['guide.json']=encode(g);self.assertIn('guide.param-unknown',self.codes(self.audit(freeze(self.files))))
 def test_missing_bundled_asset(self):
  self.files['asset-manifest.json']=encode({'assets':[{'path':'assets/not-here.png','bundled':True,'source':'own','license':'MIT'}]});self.assertIn('assets.missing',self.codes(self.audit(freeze(self.files))))
 def test_integrity_tamper(self):
  self.files['src/index.html']+=b'\n<!--modified-->';self.assertIn('integrity.mismatch',self.codes(self.audit(self.files)))
 def test_integrity_extra_member(self):
  self.files['unlisted.txt']=b'extra';self.assertIn('integrity.membership',self.codes(self.audit(self.files)))
 def test_unknown_metadata_preserved(self):
  m=s.strict_json(self.files['motion.json']);m['x-private-metadata']={'label':'allowed'};self.files['motion.json']=encode(m);self.assertEqual(self.audit(freeze(self.files))['status'],'STATIC_PASS')
 def test_other_engine_not_claimed_supported(self):
  m=s.strict_json(self.files['motion.json']);m['runtime']['profile']='x-other/1';self.files['motion.json']=encode(m);r=self.audit(freeze(self.files));self.assertFalse(r['runner_supported']);self.assertIn('runtime.adapter-required',self.codes(r))
 def test_forbidden_instructions(self):
  self.files['AGENTS.md']=b'test';self.assertIn('content.forbidden',self.codes(self.audit(freeze(self.files))))
 def test_secret_redacted(self):
  value='sk-'+'z'*30;self.files['credentials.txt']=value.encode();r=self.audit(freeze(self.files));self.assertIn('content.credential',self.codes(r));self.assertNotIn(value,json.dumps(r))
 def test_traversal(self):
  self.files['../escape']=b'x';self.assertEqual(self.audit(self.files)['status'],'FAIL');self.assertFalse((self.root.parent/'escape').exists())
 def test_case_collision(self):
  self.files['MOTION.json']=b'{}';self.assertEqual(self.audit(self.files)['status'],'FAIL')
 def test_nfc_collision(self):
  self.files['é.txt']=b'a';self.files['e\u0301.txt']=b'b';self.assertEqual(self.audit(self.files)['status'],'FAIL')
 def test_file_directory_collision(self):
  self.files['folder']=b'a';self.files['folder/a.txt']=b'b';self.assertEqual(self.audit(self.files)['status'],'FAIL')
 def test_explicit_directory_collision(self):
  p=self.root/'case.motion'
  with zipfile.ZipFile(p,'w') as z:z.writestr('folder',b'a');z.writestr('folder/',b'')
  self.assertEqual(s.audit(p)['status'],'FAIL')
 def test_symlink(self):
  p=self.root/'case.motion'
  with zipfile.ZipFile(p,'w') as z:
   i=zipfile.ZipInfo('link');i.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(i,b'/etc/passwd')
  self.assertEqual(s.audit(p)['status'],'FAIL')
 def test_personal_no_key_or_core_reads(self):
  f={'motion.json':encode({'packageProfile':'personal-download-v1','specVersion':'1.0.0-rc.1'}),'motiongit.key.json':b'PRIVATE_TEST','content/release.bin':b'PROTECTED_TEST'};p=archive(self.root/'personal.motion',f);seen=[];read=s.Package.read
  def record(self,name,*args):seen.append(name);return read(self,name,*args)
  with patch.object(s.Package,'read',record):r=s.audit(p);plan=s.repair_plan(p)
  self.assertEqual(r['status'],'PERSONAL_PACKAGE');self.assertEqual(seen,['motion.json','motion.json']);self.assertEqual(plan['blocked'],'personal-package')
 def test_repair_digest_new_file(self):
  self.files['src/index.html']+=b'\n<!-- edit -->';p=archive(self.root/'source.motion',self.files);before=p.read_bytes();plan=s.repair_plan(p);pp=self.root/'plan.json';s.write_json(pp,plan)
  r=s.repair(p,pp,self.root/'new.motion');self.assertEqual(r['audit']['status'],'STATIC_PASS');self.assertEqual(p.read_bytes(),before);self.assertEqual(r['audit']['visual_review'],'NOT_RUN')
 def test_stale_plan(self):
  self.files['src/index.html']+=b' ';p=archive(self.root/'source.motion',self.files);pp=self.root/'plan.json';s.write_json(pp,s.repair_plan(p));self.files['src/index.html']+=b' ';archive(p,self.files)
  with self.assertRaisesRegex(s.StudioError,'stale'):s.repair(p,pp,self.root/'out.motion')
 def test_flatten_root(self):
  p=archive(self.root/'wrapped.motion',{'project/'+n:b for n,b in self.files.items()});pp=self.root/'plan.json';s.write_json(pp,s.repair_plan(p));r=s.repair(p,pp,self.root/'fixed.motion');self.assertEqual(r['audit']['status'],'STATIC_PASS')
 def test_unfixed_error_stays_failed(self):
  self.files['presets/demo.json']=encode({'title':'x'*50});p=archive(self.root/'wrong.motion',self.files);pp=self.root/'plan.json';s.write_json(pp,s.repair_plan(p));r=s.repair(p,pp,self.root/'fixed.motion');self.assertEqual(r['status'],'FAIL')
 def test_overwrite_refused(self):
  p=archive(self.root/'source.motion',self.files)
  with self.assertRaisesRegex(s.StudioError,'existing'):s.repair(p,self.root/'none',p)
 def test_remote_schema_not_retrieved(self):
  with self.assertRaises(s.StudioError):s.schema_errors({'$ref':'https://invalid.example/schema'}, {})
 def test_strict_json_nan(self):
  with self.assertRaises(s.StudioError):s.strict_json('{"x":NaN}')

class InputAndObservationTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.r=Path(self.t.name)
 def tearDown(self):self.t.cleanup()
 def test_new_content_input(self):
  p=self.r/'inputs.json';p.write_text('{"title":"新的知识点","accent":"#aa3344","items":["一个","两个","三个","四个","五个"]}')
  cmd=[sys.executable,str(s.ROOT/'assets/starter/tools/inputs.py'),str(s.ROOT/'assets/starter'),str(p)]
  r=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['title'],'新的知识点')
  p.write_text('{"title":"'+('长'*29)+'"}');self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
 def obs(self,status='COMPLETE'):
  return {'source_sha256':'a'*64,'duration':3,'continuous_review':status,'unknowns':[],'scenes':[{'id':'s1','start':0,'end':3,'observations':[{'kind':'fact','statement':'synthetic title','evidence':['frame0.png']}],'implementation':'canvas','acceptance':['actual pixels reviewed separately']}]}
 def test_observation_complete_structure_only(self):
  p=self.r/'obs.json';s.write_json(p,self.obs());self.assertEqual(s.validate_observations(p)['status'],'PASS')
 def test_observation_gap_rejected(self):
  j=self.obs();j['scenes'][0]['start']=1;p=self.r/'obs.json';s.write_json(p,j);self.assertEqual(s.validate_observations(p)['status'],'FAIL')
 def test_observation_invalid_shape_reported(self):
  p=self.r/'obs.json';s.write_json(p,{'scenes':[{}]});self.assertEqual(s.validate_observations(p)['status'],'FAIL')
 def test_search_has_no_confidence_claim(self):
  r=s.search('接力','html-canvas');self.assertTrue(r['results']);self.assertEqual(r['results'][0]['compatibility'],'needs-adapter');self.assertNotIn('confidence',r['results'][0])

if __name__=='__main__':unittest.main(verbosity=2)
