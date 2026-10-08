import json
import sys

fname = sys.argv[1]
frecs = json.loads(open(fname).read())
recs = []
for i, rec in enumerate(frecs):
    rec["id"]  = i+1
    recs.append(rec)

with open(fname, 'w') as f:
    f.write(json.dumps(recs, indent=4))