import json,datetime,os
from pathlib import Path
from typing import Any,Dict
from .config import settings

_log=Path(settings.audit_log_path)
_log.parent.mkdir(parents=True,exist_ok=True)

def mask(text:str)->str:
    import re
    text=re.sub(r'\b\d{5,}\b','[REDACTED_NUM]',text)
    text=re.sub(r'[\w.-]+@[\w.-]+','[REDACTED_EMAIL]',text)
    return text

def log(record:Dict[str,Any]):
    record['ts']=datetime.datetime.utcnow().isoformat()
    record['prompt']=mask(record.get('prompt',''))
    record['response']=mask(record.get('response',''))
    with _log.open('a',encoding='utf-8') as f:
        f.write(json.dumps(record)+'\n')
