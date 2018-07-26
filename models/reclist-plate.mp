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

z.hpmu = pth.c - (.8nd, -0.25nd);
label.lft(btex $\mu$ etex, z.hpmu);
ncline(z.hpmu)(pth.w);

z.hpsig = pth.c - (.8nd, 0.25nd);
label.lft(btex $\sigma$ etex, z.hpsig);
ncline(z.hpsig)(pth.w);

z.hpnu = pn.c + (-0.25nd, .8nd);
label.top(btex $\nu$ etex, z.hpnu);
ncline(z.hpnu)(pn.n);

z.hpgam = pn.c + (0.25nd, .8nd);
label.top(btex $\gamma$ etex, z.hpgam);
ncline(z.hpgam)(pn.n);

newCircle.pep(btex $\epsilon_i$ etex);
newBox.pthr(btex $\bar \theta_i$ etex);
pthr.c - pep.c = (0, nd);
pthr.c - pth.c = (0, -nd);
drawObj(pep);
drawObj(pthr);
ncline(pep)(pthr);
ncline(pth)(pthr);

z.pb = pthr.c - (.8nd, -.25nd);
label.lft(btex $b_a$ etex, z.pb);
ncline(z.pb)(pthr.w);
z.ps = pthr.c - (.8nd, .25nd);
label.lft(btex $s_a$ etex, z.ps);
ncline(z.ps)(pthr.w);

z.pv = pep.c - (.8nd, 0);
label.lft(btex $\sigma_a$ etex, z.pv);
ncline(z.pv)(pep.w);

newCircle.pyr(btex $\bar y_i$ etex);
pyr.c - pthr.c = (nd, 0);
drawObj(pyr);

newCircle.pnr(btex $\bar n_i$ etex);
pyr.c - pnr.c = (0, nd);
drawObj(pnr);
ncline(pnr)(pyr);
ncline(pthr)(pyr);

z.uplse = pnr.se + (18pt, -36pt);
x.uplne = x.uplse;
y.uplne = ypart pn.n + 12pt;
y.uplsw = y.uplse;
x.uplsw = xpart pth.w - 12pt;
x.uplnw = x.uplsw;
y.uplnw = y.uplne;

draw z.uplsw--z.uplnw--z.uplne--z.uplse--cycle;
label.ulft(btex $j \in U$ etex, z.uplse);

z.aplse = pnr.se + (52pt, -18pt);
x.aplne = x.aplse;
y.aplne = ypart z.pb + 12pt;
y.aplsw = y.aplse;
x.aplsw = xpart z.pv - 24pt;
x.aplnw = x.aplsw;
y.aplnw = y.aplne;

draw z.aplsw--z.aplnw--z.aplne--z.aplse--cycle;
label.ulft(btex $a \in A$ etex, z.aplse);

ncline(pth)(py);
ncline(pn)(py);

endfig;
end;