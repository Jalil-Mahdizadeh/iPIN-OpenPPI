"""Candidate-only workload/coverage census; no test labels or scores."""
import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from common import CELLS,read,write,now


def main():
    ids=pa.array(read('/bundle/endpoints.json'));lengths=np.asarray(read('/bundle/lengths.json'),np.int64)
    result={}
    for cell,index in zip(CELLS,(6,3,0)):
        table=pq.read_table(f'/session/cell-{index:02d}.parquet',columns=['endpoint_a_sha256','endpoint_b_sha256'])
        a=pc.index_in(table.column(0),value_set=ids).to_numpy();b=pc.index_in(table.column(1),value_set=ids).to_numpy()
        n,m=lengths[a],lengths[b];area=n*m
        result[cell]={'rows':len(table),'unique_endpoints':len(np.unique(np.concatenate([a,b]))),
                      'pairs_with_endpoint_over_2000':int(((n>2000)|(m>2000)).sum()),
                      'pairs_requiring_tiled_contact_maps':int((area>1_000_000).sum()),
                      'mean_endpoint_length':float(np.mean(np.concatenate([n,m]))),
                      'mean_pair_area':float(area.mean()),'maximum_pair_area':int(area.max()),
                      'pair_area_quantiles':np.quantile(area,[.5,.9,.95,.99,1]).tolist(),
                      'all_residues_retained':True,'pairs_excluded':0}
    write('/output/INPUT_CENSUS.json',{'at_utc':now(),'cells':result,'test_truth_read':False,'scores_read':False},exclusive=True)
    print(result,flush=True)


if __name__=='__main__':main()
