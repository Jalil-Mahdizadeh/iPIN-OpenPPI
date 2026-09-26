"""Render every quantitative panel exclusively from its same-basename CSV."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize
M=Path(__file__).resolve().parents[1]
INK='#20313E'; MUTED='#697782'; GRID='#E5EAED'; TEAL='#087F8C'; GOLD='#D49A32'; PURPLE='#79579D'; BLUE='#367DB0'
EXPOSURE={'C1':GOLD,'C2':PURPLE,'C3':TEAL}; MODEL={'iPIN affine':INK,'iPIN optimized':TEAL,'3-mer cosine':BLUE,'3-mer interolog':PURPLE,'Length ratio':GOLD}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':11,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':9,'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':INK,'axes.edgecolor':GRID,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'savefig.facecolor':'white','figure.facecolor':'white'})
def read(name):return pd.read_csv(M/(name+'.csv'))
def panel(ax,letter,title):
 ax.set_title(title,loc='left',pad=15,fontweight='semibold');ax.text(-.09,1.05,letter,transform=ax.transAxes,fontweight='bold',fontsize=13,va='bottom')
def clean(ax,axis='x'):
 ax.spines['left'].set_visible(False);ax.spines['bottom'].set_color(GRID);ax.tick_params(axis='both',length=0,pad=5);ax.grid(axis=axis,color=GRID,lw=.6);ax.set_axisbelow(True)
def save(fig,name):
 fig.savefig(M/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.15)
 plt.close(fig)
def error(ax,x,y,lo,hi,color=TEAL,marker='o',size=5):
 if pd.notna(lo) and pd.notna(hi): ax.plot([lo,hi],[y,y],color=color,lw=1.35,solid_capstyle='round')
 ax.plot(x,y,marker=marker,ms=size,color=color,markeredgecolor='white',markeredgewidth=.55,zorder=4)
def box(ax,x,y,w,h,title,detail='',color=TEAL,fs=10):
 p=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015,rounding_size=0.025',facecolor='white',edgecolor=color,lw=1);ax.add_patch(p)
 ax.text(x+w/2,y+h*(.66 if detail else .5),title,ha='center',va='center',fontsize=fs,fontweight='semibold',color=color)
 if detail:ax.text(x+w/2,y+h*.27,detail,ha='center',va='center',fontsize=8,color=MUTED)
def arrow(ax,a,b,color=MUTED):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=11,lw=1,color=color))
def figure1():
 d=read('figure-1');fig=plt.figure(figsize=(8.5,7.1));gs=fig.add_gridspec(3,1,height_ratios=[1,1,1.25],hspace=.54)
 a=fig.add_subplot(gs[0]);a.set(xlim=(-.025,1.025),ylim=(0,1));a.axis('off');panel(a,'a','An evidence-defined interaction universe')
 a.text(0,.89,'P  Released interactions',fontsize=10,fontweight='semibold',color=TEAL)
 a.text(.45,.89,'U  Eligible pairs without released positive evidence',fontsize=9,color=MUTED)
 for x,condition,color in [(0,'train',INK),(.355,'development',BLUE),(.71,'test',TEAL)]:
  r=d[(d.panel=='a')&(d.condition==condition)].iloc[0];box(a,x,.14,.27,.48,r['label'],f"{int(r.estimate):,} endpoints\n{int(r.components):,} sequence components",color)
  if x<.7:arrow(a,(x+.285,.38),(x+.33,.38))
 a.text(.5,-.05,'Whole sequence components stay together; P and U retain distinct evidence states.',ha='center',fontsize=8.5,color=MUTED)
 b=fig.add_subplot(gs[1]);b.set(xlim=(0,1),ylim=(0,1));b.axis('off');panel(b,'b','Endpoint exposure defines the prediction task')
 for x,condition in zip([.02,.365,.71],['C1','C2','C3']):
  r=d[(d.panel=='b')&(d.condition==condition)].iloc[0];col=EXPOSURE[condition]
  b.text(x+.125,.89,condition,ha='center',fontweight='bold',fontsize=12,color=col)
  for j,cx in enumerate([x+.06,x+.20]):
   exposed=j<int(r.estimate);b.scatter([cx],[.52],s=180,facecolors=col if exposed else 'white',edgecolors=col,linewidths=1.7,zorder=3);b.text(cx,.36,'Exposed' if exposed else 'Held out',ha='center',fontsize=8,color=MUTED)
  b.plot([x+.101,x+.159],[.52,.52],ls='--',color=col,lw=1.5)
  b.text(x+.13,.10,{ 'C1':'Two exposed endpoints','C2':'One exposed endpoint','C3':'No exposed endpoints'}[condition],ha='center',fontsize=9)
 c=fig.add_subplot(gs[2]);c.set(xlim=(-.025,1.025),ylim=(0,1));c.axis('off');panel(c,'c','Frozen sequence representations, a compact trainable scorer')
 blocks=[(.00,.20,'Sequences A, B','Frozen ESM-2 150M'),(.27,.22,'Protein vectors','Pool + standardize'),(.57,.39,'Symmetric pair representation',r'$[\,z_A+z_B,\ |z_A-z_B|,\ z_A\odot z_B,\ \cos(z_A,z_B)\,]$')]
 for x,w,t,det in blocks:box(c,x,.57,w,.29,t,det,INK,9)
 arrow(c,(.215,.715),(.25,.715));arrow(c,(.505,.715),(.55,.715))
 box(c,.10,.02,.36,.32,'Affine branch + nonlinear branch','LayerNorm → 256 → GELU → scalar',TEAL,9)
 box(c,.62,.02,.34,.32,'Pair-ranking score','Mean raw score of three seeds',TEAL,9)
 arrow(c,(.76,.55),(.30,.36));arrow(c,(.48,.18),(.60,.18))
 save(fig,'figure-1')
def figure2():
 d=read('figure-2');models=['iPIN affine','Degree sum','Preferential attachment','Common neighbors','Component degree mass','Length ratio','Length sum','3-mer cosine','3-mer interolog']
 fig,axes=plt.subplots(1,2,figsize=(8.5,5.0),gridspec_kw={'wspace':.15})
 cmap=LinearSegmentedColormap.from_list('ranking',['#D9D8EA','#F7F8F9','#A4CFCD','#087F8C']);norm=Normalize(.3,.95)
 for ax,letter in zip(axes,['a','b']):
  sub=d[d.panel==letter];data=np.array([[sub[(sub.model==model)&(sub.condition==c)].estimate.iloc[0] for c in ['C1','C2','C3']] for model in models])
  ax.imshow(data,cmap=cmap,norm=norm,aspect='auto')
  for i in range(len(models)):
   for j in range(3):ax.text(j,i,f'{data[i,j]:.3f}',ha='center',va='center',fontsize=10,color='white' if data[i,j]>.80 else INK,fontweight='bold' if i==0 else 'normal')
  ax.set_xticks(range(3),['C1','C2','C3']);ax.xaxis.tick_top();ax.set_yticks(range(len(models)),models if letter=='a' else ['']*len(models));ax.tick_params(length=0,pad=7)
  for tick,c in zip(ax.get_xticklabels(),['C1','C2','C3']):tick.set_color(EXPOSURE[c]);tick.set_fontweight('bold');tick.set_fontsize(10)
  for pos in [.5,4.5,6.5]:ax.axhline(pos,color='white',lw=3)
  for spine in ax.spines.values():spine.set_visible(False)
  ax.set_title('Development' if letter=='a' else 'Original protected test',loc='left',fontweight='semibold',pad=34);ax.text(-.08,1.125,letter,transform=ax.transAxes,fontsize=13,fontweight='bold')
 fig.subplots_adjust(bottom=.16,left=.25,top=.83,right=.98)
 fig.text(.25,.05,'HT-weighted P-versus-U concordance  •  0.500 denotes tied/chance ranking',fontsize=8.5,color=MUTED)
 save(fig,'figure-2')
def figure3():
 d=read('figure-3');fig,ax=plt.subplots(figsize=(8.5,5.4));models=['iPIN optimized','iPIN affine','3-mer cosine','3-mer interolog','Length ratio','Length sum','ESM cosine','Composition cosine']
 for y,m in enumerate(models):
  sub=d[d.model==m];dv=sub[sub.dataset=='Development'];te=sub[sub.dataset!='Development'].iloc[0];col=MODEL.get(m,MUTED)
  if len(dv):
   dv=dv.iloc[0];ax.plot([dv.estimate,te.estimate],[y-.12,y+.12],color=col,alpha=.5,lw=1.1)
   if pd.notna(dv.CI_low):ax.plot([dv.CI_low,dv.CI_high],[y-.12,y-.12],color=col,alpha=.42,lw=1)
   ax.plot(dv.estimate,y-.12,'o',mfc='white',mec=col,ms=6,zorder=5)
  error(ax,te.estimate,y+.12,te.CI_low,te.CI_high,col)
  ax.text(.985,y,f'{te.estimate:.3f}',ha='right',va='center',fontsize=9,color=col,transform=ax.get_yaxis_transform())
 ax.axvline(.5,color=MUTED,ls='--',lw=.8);ax.axhline(5.5,color=GRID,lw=1)
 ax.set(yticks=range(len(models)),yticklabels=models,xlim=(.22,.90),ylim=(7.7,-.75),xlabel='C3 P-versus-U concordance')
 ax.text(.235,6.55,'Test-only controls',fontsize=8,color=MUTED)
 clean(ax);ax.set_title('C3 ranking across development and protected cohorts',loc='left',fontweight='semibold',pad=24)
 ax.plot([],[],'o',mfc='white',mec=MUTED,label='Development');ax.plot([],[],'o',color=MUTED,label='Protected test');ax.legend(loc='upper center',bbox_to_anchor=(.55,1.075),ncol=2,frameon=False,fontsize=8,handletextpad=.5)
 fig.subplots_adjust(left=.25,right=.96,bottom=.16,top=.87)
 fig.text(.25,.035,'Whiskers: marginal 95% component intervals where reported.\nOptimized test result is a disclosed follow-up on the same test set.',fontsize=8,color=MUTED)
 save(fig,'figure-3')
def figure4():
 d=read('figure-4');fig=plt.figure(figsize=(8.5,7.2));gs=fig.add_gridspec(2,4,height_ratios=[1.5,1],hspace=.8,wspace=.18)
 conditions=['Full C3','Exclude largest','Exclude rank 3','Exclude both','Between components'];labels=['Full C3',f'Remove {int(d.largest_component_endpoints.iloc[0])}-endpoint group',f'Remove {int(d.rank3_component_endpoints.iloc[0])}-endpoint group','Remove both groups','Between-component pairs']
 for i,m in enumerate(['iPIN affine','3-mer cosine','3-mer interolog','Length ratio']):
  ax=fig.add_subplot(gs[0,i]);sub=d[(d.panel=='a')&(d.model==m)]
  for y,c in enumerate(conditions):
   v=sub[sub.condition==c].iloc[0];error(ax,v.estimate,y,v.CI_low,v.CI_high,MODEL[m]);
  ax.set(xlim=(.44,.87),ylim=(4.5,-.55),yticks=range(5),yticklabels=labels if i==0 else ['']*5,xticks=[.5,.65,.8]);ax.axvline(.5,ls='--',color=MUTED,lw=.7);clean(ax);ax.set_title(m,color=MODEL[m],fontsize=10,pad=10)
  if i==0:fig.text(.23,.975,'a',fontweight='bold',fontsize=13)
  if i==1:ax.set_xlabel('P-versus-U concordance',x=1.05,labelpad=12)
 b=fig.add_subplot(gs[1,:]);panel(b,'b','Where the development excess above chance comes from')
 for y,m in enumerate(['3-mer cosine','3-mer interolog']):
  sub=d[(d.panel=='b')&(d.model==m)];left=0
  for j,(_,v) in enumerate(sub.iterrows()):
   col=MODEL[m] if j==0 else '#C9D2D8';b.barh(y,v.estimate,left=left,height=.30,color=col)
   pct=v.estimate/v.total_excess*100
   if j==0:b.text(left+v.estimate/2,y,f'{pct:.1f}%',color='white',ha='center',va='center',fontsize=11,fontweight='bold')
   left+=v.estimate
  b.text(left+.006,y,f'Total +{left:.3f}',va='center',fontsize=8.5,color=MUTED)
 b.set(yticks=[0,1],yticklabels=['3-mer: within-component P','Interolog: P touching rank 3'],xlim=(0,.18),ylim=(1.65,-.65),xlabel='Contribution to concordance − 0.5');clean(b)
 b.text(.002,1.52,'Colored segment: highlighted positive group; gray: remaining positives. Full U reference in both groups.',fontsize=7.5,color=MUTED)
 fig.subplots_adjust(left=.27,right=.97,top=.92,bottom=.10)
 fig.text(.27,.975,'Sensitivity to sequence-component composition',fontsize=12,fontweight='semibold')
 save(fig,'figure-4')
def figure5():
 d=read('figure-5');fig=plt.figure(figsize=(8.5,7.0));gs=fig.add_gridspec(2,2,height_ratios=[1,1.15],hspace=.75,wspace=.85)
 ax=fig.add_subplot(gs[0,0]);models=['pair_linear','endpoint_linear','endpoint_mlp64','kmer3_cosine','pooled_cosine','length_ratio'];labels=['Pair head','Linear unary','MLP unary','3-mer cosine','ESM cosine','Length ratio']
 for y,m in enumerate(models):
  v=d[(d.panel=='a')&(d.model==m)].iloc[0];error(ax,v.estimate,y,v.CI_low,v.CI_high,TEAL if y==0 else MUTED)
 ax.set(yticks=range(6),yticklabels=labels,xlim=(.49,.72),ylim=(5.5,-.5),xlabel='Within-anchor concordance');clean(ax);panel(ax,'a','Conditioning on the partner')
 v=d[d.panel=='a_difference'].iloc[0]; ax.text(0,-.36,f'Pair − MLP unary: {v.estimate:+.3f}\n95% CI [{v.CI_low:.3f}, {v.CI_high:.3f}]',transform=ax.transAxes,fontsize=8,color=TEAL)
 ax=fig.add_subplot(gs[0,1]);arms=['union','purged20','hi_to_huri','huri_to_hi'];labels=['Union','Homology purge','HI-II-14 → HuRI','HuRI → HI-II-14']
 for y,arm in enumerate(arms):
  v=d[(d.panel=='b')&(d.condition==arm)].iloc[0];error(ax,v.estimate,y,v.CI_low,v.CI_high,TEAL)
 ax.axvline(0,ls='--',color=MUTED,lw=.7);ax.set(xlim=(-.006,.12),yticks=range(4),yticklabels=labels,ylim=(3.5,-.5),xlabel='Pair − linear unary');clean(ax);panel(ax,'b','Internal robustness')
 c=fig.add_subplot(gs[1,:]);panel(c,'c','Matched endpoints, alternative pairings')
 for y,arm in enumerate(arms):
  v=d[(d.panel=='c')&(d.condition==arm)].iloc[0];error(c,v.estimate,y,v.CI_low,v.CI_high,TEAL if arm!='huri_to_hi' else GOLD)
  c.text(1.02,y,f'n = {int(v.quartets):,}',transform=c.get_yaxis_transform(),va='center',fontsize=8,color=MUTED)
 c.axvline(.5,color=MUTED,ls='--',lw=.8);c.set(xlim=(0,1),yticks=range(4),yticklabels=labels,ylim=(3.6,-.65),xlabel='Preference for observed pairings over endpoint-balanced U alternatives');clean(c)
 c.text(.515,3.40,'Unary scores cancel to 0.5',fontsize=8,color=MUTED)
 fig.subplots_adjust(left=.20,right=.88,top=.91,bottom=.10)
 save(fig,'figure-5')
def figure6():
 d=read('figure-6');fig=plt.figure(figsize=(8.5,7.2));gs=fig.add_gridspec(2,2,height_ratios=[1.1,1],wspace=.55,hspace=.7)
 a=fig.add_subplot(gs[0,0]);enc={'esm2_150m':TEAL,'esm2_650m':PURPLE};shapes={'linear':'o','mlp':'s','residual_mlp':'D','bilinear':'^'}
 for _,v in d[d.panel=='a'].iterrows():a.scatter(v.parameters,v.estimate,color=enc[v.encoder],marker=shapes[v.condition],s=35,alpha=.83,edgecolors='white',linewidth=.5)
 a.set_xscale('log');a.set(xlim=(1000,1.8e6),ylim=(.67,.82),xlabel='Trainable head parameters',ylabel='Development C3 concordance');clean(a,'y');panel(a,'a',f'All {len(d[d.panel=="a"])} screened recipes')
 for e,col in enc.items():a.scatter([],[],c=col,label=e.replace('esm2_','ESM-2 '),s=25)
 a.legend(frameon=False,fontsize=8,loc='lower left');a.text(0,-.30,'○ Affine   □ MLP   ◇ Residual   △ Bilinear',transform=a.transAxes,fontsize=8,color=MUTED)
 b=fig.add_subplot(gs[0,1]);sub=d[d.panel=='b'];recipes=['esm2_150m__residual_wide','esm2_150m__mlp_wide','esm2_650m__mlp_small','esm2_150m__linear_base_lr'];labels=['150M residual','150M MLP','650M MLP','150M affine']
 for y,(recipe,label) in enumerate(zip(recipes,labels)):
  s=sub[sub.model==recipe].sort_values('epoch');x=s.estimate.to_numpy();b.plot(x,[y,y],c=enc[s.encoder.iloc[0]],lw=1)
  for _,v in s.iterrows():b.plot(v.estimate,y,'o' if v.epoch==4 else 's',mfc=enc[v.encoder] if v.epoch==4 else 'white',mec=enc[v.encoder],ms=6)
 b.set(yticks=range(4),yticklabels=labels,xlim=(.78,.805),ylim=(3.5,-.55),xlabel='Development C3 concordance');clean(b);panel(b,'b','Promoted three-seed ensembles')
 b.text(0,-.30,'● Epoch 4    □ Epoch 8',transform=b.transAxes,fontsize=8,color=MUTED)
 c=fig.add_subplot(gs[1,:]);panel(c,'c','Ensemble benefit and member variability')
 sub=d[d.panel=='c'];labels=[]
 for y,(_,v) in enumerate(sub.iterrows()):
  color=MUTED if v.condition=='Individual seed' else (TEAL if v.dataset=='Development C3' else PURPLE)
  error(c,v.estimate,y,v.CI_low,v.CI_high,color)
  labels.append(f'Seed {int(v.seed)}' if v.condition=='Individual seed' else ('Development ensemble' if v.dataset=='Development C3' else 'Protected follow-up ensemble'))
 c.axvline(0,color=MUTED,ls='--',lw=.8);c.axhline(2.5,color=GRID,lw=.8);c.set(yticks=range(len(labels)),yticklabels=labels,xlim=(-.013,.058),ylim=(4.6,-.55),xlabel='Optimized − original affine C3 concordance');clean(c)
 fig.subplots_adjust(left=.15,right=.97,top=.92,bottom=.10)
 save(fig,'figure-6')
def figures1():
 d=read('figure-s1');models=['Degree sum','Preferential attachment','Common neighbors','Component degree mass','Length ratio','Length sum','3-mer cosine','3-mer interolog','ESM cosine','Composition cosine','Hash sentinel'];fig,axes=plt.subplots(1,3,figsize=(8.5,5.7),sharey=True,gridspec_kw={'wspace':.18})
 for ax,c in zip(axes,['C1','C2','C3']):
  for y,m in enumerate(models):
   v=d[(d.panel==c)&(d.model==m)].iloc[0];error(ax,v.estimate,y,v.CI_low,v.CI_high,EXPOSURE[c],size=4)
  ax.axvline(0,color=MUTED,ls='--',lw=.8);ax.set(xlim=(-.12,.6),ylim=(10.6,-.6),yticks=range(11),yticklabels=models,xticks=[0,.2,.4,.6]);clean(ax);ax.set_title(c,color=EXPOSURE[c],fontweight='bold')
 axes[1].set_xlabel('Original affine iPIN − fixed control: paired concordance difference',labelpad=15)
 fig.subplots_adjust(left=.27,right=.98,top=.88,bottom=.15);fig.text(.27,.96,'Protected comparisons retain endpoint-exposure differences',fontsize=11,fontweight='semibold')
 save(fig,'figure-s1')
if __name__=='__main__':
 for f in [figure1,figure2,figure3,figure4,figure5,figure6,figures1]:f();print(f.__name__+' rendered',flush=True)
