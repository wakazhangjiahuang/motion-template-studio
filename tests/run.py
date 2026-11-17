from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parents[1]/'skills/motion-template-studio/scripts/test_motion_studio.py'
raise SystemExit(subprocess.run([sys.executable,str(p)]).returncode)
