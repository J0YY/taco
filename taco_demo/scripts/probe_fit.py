import numpy as np, sys
def load(p):
    d = np.load(p); h = np.asarray(d["h3"], dtype=np.float32)  # [steps, envs, hid]
    return h.reshape(-1, h.shape[-1])
A, B, tag = load(sys.argv[1]), load(sys.argv[2]), sys.argv[3]
rng = np.random.RandomState(0)
n = min(len(A), len(B), 6000)
A = A[rng.choice(len(A), n, replace=False)]; B = B[rng.choice(len(B), n, replace=False)]
ka, kb = int(0.7*n), int(0.7*n)
Atr, Ate, Btr, Bte = A[:ka], A[ka:], B[:kb], B[kb:]
mu = np.concatenate([Atr, Btr]).mean(0); sd = np.concatenate([Atr, Btr]).std(0) + 1e-6
z = lambda X: (X - mu) / sd
w = z(Btr).mean(0) - z(Atr).mean(0); w /= np.linalg.norm(w) + 1e-8
pa, pb = z(Atr) @ w, z(Btr) @ w
thr = (pa.mean() + pb.mean()) / 2
flip = pb.mean() < pa.mean()
pate, pbte = z(Ate) @ w, z(Bte) @ w
if flip: acc = (np.mean(pate >= thr) + np.mean(pbte < thr)) / 2
else:    acc = (np.mean(pate < thr) + np.mean(pbte >= thr)) / 2
print(f"PROBE {tag} acc={acc:.3f} n={n}")
