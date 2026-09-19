"""Validate frozen length/cache/tile adaptation before opening any test pairs."""
import time
import numpy as np
import torch
from dscript.alphabets import Uniprot21
from dscript.pretrained import get_pretrained
from common import cuda, now, read, write
from native_adapter import create, learned_digest


def main():
    device = cuda(20260912)
    original = get_pretrained("human_v1").to(device).eval().requires_grad_(False)
    adapter = create(device=device)
    before = learned_digest(adapter)
    assert before == learned_digest(original)
    rng = np.random.default_rng(20260912)
    errors = []
    with torch.inference_mode():
        # Includes below/at the native length boundary and both orientations.
        for n, m in [(16,19),(32,47),(101,127),(128,256),(500,499),(999,511),(2000,32),(2000,501)]:
            a = torch.from_numpy(rng.normal(0,.25,(1,n,6165)).astype(np.float32)).to(device)
            b = torch.from_numpy(rng.normal(0,.25,(1,m,6165)).astype(np.float32)).to(device)
            adapter.tile_area = None
            native = original.predict(a,b)
            extended = adapter.predict(a,b)
            cached = adapter.predict(original.embed(a),original.embed(b))
            assert torch.equal(native, extended), (n,m,"position extension changed native output")
            assert torch.equal(native, cached), (n,m,"projection cache changed native output")
            adapter.tile_area = 25_000
            tiled = adapter.predict(original.embed(a), original.embed(b))
            error = abs(native.item()-tiled.item())
            assert error <= 1e-5, (n,m,error)
            errors.append({"n":n,"m":m,"extended_and_cached_bitwise_identical":True,"tiled_score_absolute_error":error})
            del a,b
        # Real frozen TRAIN sequences, with no TRAIN pair labels or test candidates.
        meta=read('/sequences.json')
        assert len(meta['sha256'])==17000
        train=[i for i,p in enumerate(meta['partition']) if p=='train' and meta['length'][i]<=2000]
        lm=get_pretrained('lm_v1').to(device).eval().requires_grad_(False)
        alphabet=Uniprot21(); real=[]
        for i in train[:32]:
            x=torch.from_numpy(alphabet.encode(meta['sequence'][i].encode())).long()[None].to(device)
            real.append(lm.transform(x))
        adapter.tile_area=None
        real_errors=[]
        for a,b in zip(real[:16],real[16:]):
            expected=original.predict(a,b)
            cached=adapter.predict(original.embed(a),original.embed(b))
            assert torch.equal(expected,cached)
            real_errors.append(abs(expected.item()-cached.item()))
        del lm,real
        # Worst-case full-length resource probe uses synthetic projected residues.
        # Native unchanged parameters plus the extended index; no learned adaptation.
        adapter.tile_area=1_000_000
        resource=[]
        for n,m in [(2001,32),(2501,1001),(7570,7570)]:
            a=torch.from_numpy(rng.normal(0,.25,(1,n,100)).astype(np.float32)).to(device)
            b=torch.from_numpy(rng.normal(0,.25,(1,m,100)).astype(np.float32)).to(device)
            torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize(); started=time.monotonic()
            value=adapter.predict(a,b); torch.cuda.synchronize()
            assert torch.isfinite(value) and 0<=value.item()<=1
            resource.append({"n":n,"m":m,"seconds":time.monotonic()-started,
                             "peak_gpu_allocated_bytes":torch.cuda.max_memory_allocated(),"finite":True})
            if n==2501:
                adapter.tile_area=None
                untiled=adapter.predict(a,b)
                assert abs(untiled.item()-value.item())<=1e-5
                resource[-1]['tiled_vs_extended_untiled_score_error']=abs(untiled.item()-value.item())
                adapter.tile_area=1_000_000
        # Size-based throughput pilot, fixed synthetic inputs and no test outcomes.
        timings=[]
        for n,m in [(128,128),(256,512),(512,512),(1024,1024),(2000,512)]:
            a=torch.randn(1,n,100,device=device)*.25; b=torch.randn(1,m,100,device=device)*.25
            for _ in range(3):adapter.predict(a,b)
            torch.cuda.synchronize(); started=time.monotonic()
            for _ in range(30):adapter.predict(a,b)
            torch.cuda.synchronize()
            timings.append({"n":n,"m":m,"pairs_per_second":30/(time.monotonic()-started)})
    assert learned_digest(adapter)==before==learned_digest(original)
    write('/output/ADAPTER_QUALIFICATION.json',{'at_utc':now(),'passed':True,'synthetic_fidelity':errors,
          'real_train_sequence_fixture_pairs':len(real_errors),'real_fixture_max_error':max(real_errors),
          'long_sequence_resources':resource,'throughput':timings,'learned_state_sha256':before,
          'only_state_change':'extended nonlearned xx integer index','test_pairs_read':False,'test_truth_read':False,
          'training_performed':False,'tile_score_tolerance':1e-5},exclusive=True)
    print({'passed':True,'fidelity_cases':len(errors)+len(real_errors),'resources':resource,'throughput':timings},flush=True)


if __name__=='__main__':main()
