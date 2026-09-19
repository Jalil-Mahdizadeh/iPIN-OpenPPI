"""Independent copies of frozen TRAIN/C3-DEV data; no protected-test inputs."""
from pathlib import Path
import shutil
import numpy as np
from common import read,write,sha,record,now,arrays


def main():
    source=Path('/source_data'); root=Path('/output/data')
    root.mkdir(exist_ok=True)
    if any(root.iterdir()):raise RuntimeError('Refusing to overwrite prepared data')
    manifest=read(source/'DATA_MANIFEST.json')
    expected={Path(x['path']).name:x for x in manifest['outputs']}
    files=[]
    for name in ('training.npz','development_00.npz','sequences.json','endpoints.json'):
        assert sha(source/name)==expected[name]['sha256']
        shutil.copyfile(source/name,root/name)
        item=record(root/name);item['path']=name;files.append(item)
    meta=read(root/'sequences.json'); train=arrays(root/'training.npz'); dev=arrays(root/'development_00.npz')
    assert read(root/'endpoints.json')==meta['sha256'] and len(set(meta['sha256']))==17000
    part=np.asarray(meta['partition'])
    for key in ('p_a','p_b','u_a','u_b'):
        assert (part[train[key]]=='train').all()
    assert (part[dev['a']]=='development').all() and (part[dev['b']]=='development').all()
    assert len(train['p_a'])==16799 and len(train['u_a'])==2000000
    assert len(dev['a'])==1002265 and dev['positive'].sum()==2265
    assert np.isfinite(train['u_weight']).all() and (train['u_weight']>0).all()
    write(root/'DATA_MANIFEST.json',{'at_utc':now(),'files':files,'source_manifest_sha256':sha(source/'DATA_MANIFEST.json'),
          'train_positive_rows':16799,'train_unlabeled_rows':2000000,'development_cell':'C3_development',
          'development_rows':1002265,'TRAIN_only_fitting_enforced':True,'test_pairs_read':False,'test_truth_read':False},exclusive=True)
    print('TRAIN and C3-DEV identities and partition isolation verified',flush=True)


if __name__=='__main__':main()
