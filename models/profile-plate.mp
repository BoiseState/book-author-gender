input metaobj

beginfig(1);
nd = 0.8in;

newCircle.pth(btex $\theta_j$ etex);
pth.c = origin;

newCircle.py(btex $y_j$ etex);
py.c - pth.c = (nd, 0);

newCircle.pn(btex $n_j$ etex);
pn.c - py.c = (0, nd);

drawObj(pth);
drawObj(py);
drawObj(pn);

z.hpmu = pth.c - (.8nd, -0.4nd);
label.lft(btex $\mu$ etex, z.hpmu);
ncline(z.hpmu)(pth.w);

z.hpsig = pth.c - (.8nd, 0.4nd);
label.lft(btex $\sigma$ etex, z.hpsig);
ncline(z.hpsig)(pth.w);

z.hpnu = pn.c + (-0.4nd, .8nd);
label.top(btex $\nu$ etex, z.hpnu);
ncline(z.hpnu)(pn.n);

z.hpgam = pn.c + (0.4nd, .8nd);
label.top(btex $\gamma$ etex, z.hpgam);
ncline(z.hpgam)(pn.n);

z.plse = py.se + (18pt, -18pt);
x.plne = x.plse;
y.plne = ypart pn.n + 12pt;
y.plsw = y.plse;
x.plsw = xpart pth.w - 12pt;
x.plnw = x.plsw;
y.plnw = y.plne;

draw z.plsw--z.plnw--z.plne--z.plse--cycle;
label.ulft(btex $j \in U$ etex, z.plse);

ncline(pth)(py);
ncline(pn)(py);

endfig;
end;