"""Detect abrupt screen-region changes (proxy for clicks / selections / typing) at 30fps."""
import numpy as np, subprocess, json
SRC = '/tmp/claude-0/work/src/source.mov'
W, H = 270, 153
cmd = ['ffmpeg', '-v', 'error', '-i', SRC, '-vf', f'fps=30,crop=1080:613:0:225,scale={W}:{H},format=gray', '-f', 'rawvideo', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
prev = None; d = []; reg = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    f = np.frombuffer(b, np.uint8).reshape(H, W).astype(np.int16)
    if prev is not None:
        df = np.abs(f - prev); d.append(float((df > 20).mean())); 
        ys, xs = np.where(df > 20)
        reg.append((int(xs.mean()), int(ys.mean())) if len(xs) > 15 else None)
    else: d.append(0); reg.append(None)
    prev = f
d = np.array(d)
ev = [(i / 30, float(d[i]), reg[i]) for i in range(len(d)) if d[i] > 0.003]
json.dump({'diff': d.tolist(), 'events': ev}, open('/tmp/claude-0/work/events.json', 'w'))
print(len(ev), 'event frames')
