from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]/'skills/motion-template-studio/scripts'
sys.path.insert(0,str(p))
runpy.run_path(str(p/'mcp_server.py'),run_name='__main__')
