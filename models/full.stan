// This file is generated from models.md
data {
    int<lower=0> J;
int<lower=5> n[J];
int<lower=0> y[J];

    int<lower=0> A;
int<lower=0> NL;
int<lower=1,upper=J> ru[NL];
int<lower=1,upper=A> ra[NL];
int<lower=0> rn[NL];
int<lower=0> ry[NL];

}
transformed data {
    int<lower=0> shiftN[J];

    vector<lower=0,upper=1>[NL] rp;
vector[NL] rll;

    for (i in 1:J) {
    shiftN[i] = n[i] - 5;
}

    rp = (to_vector(ry) + 1) ./ (to_vector(rn) + 2);
rll = logit(rp);

}
parameters {
    real<lower=0> nMean;
real<lower=0> nDisp;
real mu;
real<lower=0> sigma;
vector[J] nTheta;

    vector[A] recB;
vector[A] recS;
vector<lower=0>[A] recV;

}
transformed parameters {
    vector<lower=0,upper=1>[J] theta;

    vector[NL] rbias;
vector[NL] noiseR;

    theta = inv_logit(nTheta);

    rbias = recB[ra] + recS[ra] .* nTheta[ru];
noiseR = rll - rbias;

}
model {
    // profile prior distribution
    nMean ~ exponential(0.001);
nDisp ~ exponential(0.001);
mu ~ normal(0, 100);
sigma ~ exponential(0.001);

    // rec list priors
    recB ~ normal(0, 100);
recS ~ normal(0, 100);
recV ~ exponential(0.001);


    // profile likelihood model
    shiftN ~ neg_binomial_2(nMean, nDisp);
y ~ binomial(n, theta);
nTheta ~ normal(mu, sigma);

    
    // rec list likelihood model
    noiseR ~ normal(0, recV[ra]);

}
generated quantities {
    real nThetaP;
real<lower=0, upper=1> thetaP;
int<lower=5> nP = 0;
int<lower=0> yP;

    vector[A] biasP;
vector[A] noiseP;
vector[A] thetaRP;

    nThetaP = normal_rng(mu, sigma);
thetaP = inv_logit(nThetaP);
nP = neg_binomial_2_rng(nMean, nDisp) + 5;
yP = binomial_rng(nP, thetaP);

    biasP = recB + recS * nThetaP;
for (a in 1:A) {
    noiseP[a] = normal_rng(0, recV[a]);
}
thetaRP = inv_logit(noiseP + biasP);

}
