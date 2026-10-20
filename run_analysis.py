"""Reproduce the project from the supplied CSV. No values are imputed or converted."""
from pathlib import Path
import pandas as pd
import numpy as np
import json, hashlib, html, io, contextlib, platform

HERE = Path(__file__).resolve().parent
ROOT = HERE
SOURCE_NAME = '1776250375-P2-Healthcare Analytics for Doctor Visits (1).csv'
SOURCE = ROOT / SOURCE_NAME
OUT = ROOT
OUT.mkdir(exist_ok=True)
TABLES = OUT / 'calculated_tables'
TABLES.mkdir(exist_ok=True)
df = pd.read_csv(SOURCE)
expected = ['Unnamed: 0','visits','gender','age','income','illness','reduced','health','private','freepoor','freerepat','nchronic','lchronic']
assert list(df.columns) == expected, 'Source columns changed. Review before analysis.'
numeric = ['visits','age','income','illness','reduced','health']
binary = ['private','freepoor','freerepat','nchronic','lchronic']
assert not df.isna().any().any(), 'Missing source values require review. No imputation permitted.'
assert not df.iloc[:,0].duplicated().any(), 'Repeated identifiers require review.'
assert all(pd.api.types.is_numeric_dtype(df[c]) for c in numeric)
assert all(set(df[c]) <= {'yes','no'} for c in binary)
assert set(df.gender) <= {'female','male'}
assert all((df[c]>=0).all() for c in numeric)
assert all((df[c]%1==0).all() for c in ['visits','illness','reduced','health'])

metrics = {
 'records':len(df), 'columns':len(df.columns), 'missing_cells':int(df.isna().sum().sum()),
 'duplicate_ids':int(df.iloc[:,0].duplicated().sum()), 'duplicate_full_rows':int(df.duplicated().sum()),
 'matching_measurement_rows':int(df.iloc[:,1:].duplicated().sum()),
 'total_visits':int(df.visits.sum()), 'mean_visits':float(df.visits.mean()),
 'median_visits':float(df.visits.median()), 'zero_visit_records':int((df.visits==0).sum()),
 'positive_visit_records':int((df.visits>0).sum()), 'maximum_visits':int(df.visits.max()),
 'zero_visit_pct':float((df.visits==0).mean()*100),
 'positive_visit_pct':float((df.visits>0).mean()*100),
 'mean_among_visitors':float(df.loc[df.visits>0,'visits'].mean()),
 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'source_file':SOURCE_NAME,
}

def summarize(column):
    t=df.groupby(column,dropna=False,sort=True).agg(records=('visits','size'), total_visits=('visits','sum'), mean_visits=('visits','mean'), visitors=('visits',lambda s:int((s>0).sum())))
    t['share_with_visit_pct']=100*t.visitors/t.records
    assert int(t.records.sum()) == len(df)
    assert int(t.total_visits.sum()) == int(df.visits.sum())
    return t.reset_index()

tables = {c:summarize(c) for c in ['gender','age','income','illness','reduced','health']+binary}
dist=df.visits.value_counts().sort_index().rename_axis('visits').reset_index(name='records')
dist['share_pct']=100*dist.records/len(df)
tables['visit_distribution']=dist
affected=df.assign(activity_affected=np.where(df.reduced==0,'No reduced days','One or more reduced days')).groupby('activity_affected').agg(records=('visits','size'),total_visits=('visits','sum'),mean_visits=('visits','mean')).reset_index()
tables['activity_affected']=affected
tables['numeric_summary']=df[numeric].describe().rename_axis('statistic').reset_index()
corr=df[numeric].corr(method='pearson')['visits'].drop('visits').rename_axis('field').reset_index(name='pearson_r_with_visits')
tables['correlations']=corr
tables['data_quality']=pd.DataFrame([
 {'check':'Source records','result':len(df),'action':'Retain all records'},
 {'check':'Missing cells','result':metrics['missing_cells'],'action':'No filling performed'},
 {'check':'Duplicate complete rows including ID','result':metrics['duplicate_full_rows'],'action':'No removal needed'},
 {'check':'Duplicate identifiers','result':metrics['duplicate_ids'],'action':'No removal needed'},
 {'check':'Repeated measurements excluding ID','result':metrics['matching_measurement_rows'],'action':'Retain: different IDs can have matching measurements'},
 {'check':'Age conversion','result':'None','action':'No conversion rule in either supplied reference'},
 {'check':'Income conversion','result':'None','action':'No units or conversion rule supplied'},
 {'check':'Health score direction','result':'Unspecified','action':'Do not label higher scores better or worse'},
])
for name,t in tables.items():
    t.to_csv(TABLES/(name+'.csv'),index=False,float_format='%.12g')
    back=pd.read_csv(TABLES/(name+'.csv'))
    assert back.shape==t.shape
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
(ROOT/'.analysis_cache').mkdir(exist_ok=True)
(ROOT/'.analysis_cache'/'analysis.json').write_text(json.dumps({'metrics':metrics,'tables':{k:json.loads(t.to_json(orient='records')) for k,t in tables.items()}},indent=2),encoding='utf-8')

# Notebook cells are executed here with their actual captured stdout saved as outputs.
# Only pandas and Python's standard library are required to rerun these cells.
cells=[]; env={}; cell_no=0
def markdown(text):
    cells.append({'cell_type':'markdown','metadata':{},'source':text.splitlines(keepends=True)})
def code(source):
    global cell_no
    cell_no+=1; buffer=io.StringIO()
    with contextlib.redirect_stdout(buffer): exec(compile(source,'<notebook>','exec'),env)
    cells.append({'cell_type':'code','execution_count':cell_no,'metadata':{},'source':source.splitlines(keepends=True),'outputs':[{'output_type':'stream','name':'stdout','text':buffer.getvalue().splitlines(keepends=True)}]})
markdown('# Healthcare Analytics for Doctor Visits\n\nThis project studies associations with doctor visits using only the supplied CSV. All 5,190 original records are retained. No values are filled, rescaled, or fabricated.\n\nAge and income remain in their original numerical scale. The visit observation period and the direction of the health score are not defined in the supplied files. Results are descriptive associations, not causal effects or medical advice.')
code("from pathlib import Path\nimport pandas as pd\nimport hashlib\nsource_name = '"+SOURCE_NAME+"'\nsource = next((p for p in [Path.cwd()/source_name, Path.cwd().parent/source_name] if p.exists()), None)\nif source is None:\n    raise FileNotFoundError('Keep the project folder beside the original CSV.')\ndf = pd.read_csv(source)\nprint('Records:', len(df), 'Columns:', len(df.columns))\nprint('CSV SHA256:', hashlib.sha256(source.read_bytes()).hexdigest())\nprint(df.head().to_string(index=False))")
markdown('## Data quality and preparation\nThe first column is an identifier, excluded from numerical comparisons. Matching measurements under different record IDs are retained. Zero income is kept as recorded because its meaning is not explained. No reference specifies an age or income conversion.')
code("print('Missing cells:', int(df.isna().sum().sum()))\nprint('Duplicate IDs:', int(df.iloc[:, 0].duplicated().sum()))\nprint('Duplicate complete rows:', int(df.duplicated().sum()))\nprint('Repeated measurements excluding ID:', int(df.iloc[:, 1:].duplicated().sum()))\nprint(df[['visits','age','income','illness','reduced','health']].describe().to_string())")
markdown('## Overall doctor visits\nAverage visits = total visits divided by all records. Share with a visit = records with visits greater than zero divided by all records. The CSV provides no time period for these visits.')
code("print('Total visits:', int(df.visits.sum()))\nprint('Average visits per record:', round(df.visits.mean(), 6))\nprint('Median visits:', df.visits.median())\nprint('Records with zero visits:', int((df.visits == 0).sum()))\nprint('Share with at least one visit (%):', round((df.visits > 0).mean()*100, 6))\nprint(df.visits.value_counts().sort_index().to_string())")
for col in ['gender','illness','reduced','nchronic','lchronic','private','freepoor','freerepat','age','income','health']:
    markdown('## Doctor visits by '+col+'\nGroup averages use each group\'s own record count. Group differences are unadjusted. Different healthcare support or chronic flags can overlap and must not be added together.')
    code("summary = df.groupby('"+col+"').agg(records=('visits','size'), total_visits=('visits','sum'), mean_visits=('visits','mean'), visitors=('visits',lambda s: int((s>0).sum())))\nsummary['share_with_visit_pct'] = 100*summary.visitors/summary.records\nassert summary.records.sum() == len(df)\nassert summary.total_visits.sum() == df.visits.sum()\nprint(summary.to_string(float_format=lambda v: f'{v:.6f}'))")
markdown('## Activity affected by illness\nThis explicit grouping compares reduced = 0 with reduced > 0. It changes only the grouping, not the source values.')
code("affected = df.assign(activity_affected=df.reduced.gt(0).map({False:'No reduced days', True:'One or more reduced days'}))\nprint(affected.groupby('activity_affected').agg(records=('visits','size'),total_visits=('visits','sum'),mean_visits=('visits','mean')).to_string())")
markdown('## Conclusion\nRecords with more illnesses, reduced activity days, or lchronic = yes generally show higher average visits in this sample. Females average more visits than males. Healthcare support comparisons vary by flag and do not establish access, need, quality of care, or program effectiveness. Age, income and health are reported on their original scales. No population weights, observation dates, causal adjustment, or predictive model are supplied or assumed.')
for i,cell in enumerate(cells): cell['id']=f'healthcare-{i:03d}'
notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':platform.python_version()}},'nbformat':4,'nbformat_minor':5}
(OUT/'Healthcare_Analysis.ipynb').write_text(json.dumps(notebook,indent=1),encoding='utf-8')

intro='''<h1>Healthcare Analytics for Doctor Visits</h1><p>Analysis of the supplied CSV only. All 5,190 records are retained.</p><p><strong>Reading the results:</strong> Average visits means total visits divided by records in that group. These comparisons describe associations. They do not show that one factor causes more visits.</p><p><strong>Units:</strong> Age and income remain in the original CSV scale. Neither supplied reference gives a conversion rule. The observation period and health score direction are unspecified.</p>'''
parts=[intro,'<h2>Overall results</h2>',pd.DataFrame([{'Metric':k,'Value':v} for k,v in metrics.items() if k not in ['source_sha256','source_file']]).to_html(index=False,border=0)]
labels={'gender':'Gender','illness':'Reported illnesses','reduced':'Days of reduced activity','nchronic':'Chronic flag nchronic','lchronic':'Long-term chronic flag lchronic','private':'Private healthcare flag','freepoor':'Financial-need support flag','freerepat':'Repatriation support flag','age':'Age in original CSV scale','income':'Income in original CSV scale','health':'Health score with unspecified direction','visit_distribution':'Visit distribution','activity_affected':'Any reduced activity days','numeric_summary':'Numerical summary','correlations':'Pearson correlations with doctor visits','data_quality':'Data quality'}
for name,t in tables.items():
    parts += ['<h2>'+labels[name]+'</h2>',t.to_html(index=False,border=0,float_format=lambda v:f'{v:,.6f}')]
parts += ['<h2>Actual executed code and output</h2><p>The following code was run against the supplied CSV. The outputs below were captured from that execution.</p>']
for cell in cells:
    if cell['cell_type']=='code':
        parts += ['<section class="execution"><pre class="code">'+html.escape(''.join(cell['source']))+'</pre><pre class="output">'+html.escape(''.join(cell['outputs'][0]['text']))+'</pre></section>']
parts += ['<h2>Limits</h2><p>These are unweighted, unadjusted comparisons within this dataset. We cannot identify unmet medical need from zero visits, infer healthcare program effects, interpret the health score as better or worse, or convert age and income without a supplied rule. Matching measurements do not prove duplicate people. No external data or invented results were used.</p>', '<p>Source: '+html.escape(SOURCE_NAME)+'<br>SHA256: '+metrics['source_sha256']+'</p>']
css='body{font:17px/1.6 Arial,sans-serif;color:#1a2733;max-width:1080px;margin:45px auto;padding:0 28px}h1{font-size:36px;color:#17658c}h2{margin-top:42px;color:#17658c}table{border-collapse:collapse;width:100%;font-size:15px;margin:16px 0 30px}th,td{text-align:right;padding:9px 12px;border-bottom:1px solid #d5e0e6}th{background:#edf5f8}th:first-child,td:first-child{text-align:left}pre{overflow:auto;padding:20px;line-height:1.5;font-size:15px;white-space:pre-wrap}.code{background:#eef4f7}.output{border-left:3px solid #2c8d79}.execution{margin:32px 0}@media print{body{max-width:none}pre{font-size:11px}h2{break-after:avoid}}'
(OUT/'Analysis_Report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Healthcare Analytics for Doctor Visits</title><style>'+css+'</style><body>'+''.join(parts)+'</body></html>',encoding='utf-8')

print(json.dumps(metrics,indent=2))
print('Activity comparison:', affected.to_string(index=False))
print('Age:',tables['age'].to_string(index=False))
print('Income:',tables['income'].to_string(index=False))
print('All calculation groups reconcile to source records and total visits.')
