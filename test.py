import os
lc = []
dd = "save"
for w in os.walk(dd):
    if len(w[2]) == 0: continue
    for f in w[2]:
        d = w[0].replace(f'{dd}/', '')
        lc.append(os.path.join(d, f))
print(lc)