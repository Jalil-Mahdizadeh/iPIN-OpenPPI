"""Verify every original frozen input and released source remains unchanged."""
from pathlib import Path
from io_utils import ROOT,atomic,now,read,record,verify

def main():
    originals=read(ROOT/'INPUT_FREEZE.json')['files']
    for i,item in enumerate(originals):
        verify(Path('/repo')/item['path'],item)
        if i%50==0:print({'preserved_original_files':i,'total':len(originals)},flush=True)
    for freeze in ('XPAIR_FREEZE.json','ANKH_FREEZE.json'):
        for item in read(ROOT/'sources'/freeze)['files']:verify(ROOT/item['path'],item)
    atomic(ROOT/'PRESERVATION.json',{'at_utc':now(),'passed':True,'original_files':len(originals),
        'released_sources_and_weights_unchanged':True,'input_freeze':record(ROOT/'INPUT_FREEZE.json')})
    print({'preservation_passed':True,'original_files':len(originals)},flush=True)

if __name__=='__main__':main()
