// This file is generated from models.md
data {
    int<lower=0> J;
int<lower=5> n[J];
int<lower=0> y[J];

}
transformed data {
    int<lower=0> shiftN[J];

    for (i in 1:J) {
    shiftN[i] = n[i] - 5;
}

}
parameters {
    real<lower=0> nMean;
real<lower=0> nDisp;
real<lower=0,upper=1> mu;
real<lower=0> lambda;
vector<lower=0,upper=1>[J] theta;

}
transformed parameters {
    real<lower=0> alpha;
real<lower=0> beta;
real[J] nTheta;

    alpha = lambda * mu;
beta = lambda * (1 - mu);
nTheta = logit(theta);

}
model {
    // prior distribution
    nMean ~ lognormal(0, 5);
nDisp ~ lognormal(0, 5);
mu ~ beta(1,1);
lambda ~ lognormal(0, 5);

    // likelihood model
    shiftN ~ neg_binomial_2(nMean, nDisp);
y ~ binomial(n, theta);
theta ~ beta(alpha, beta);

}
generated quantities {
    real<lower=0, upper=1> thetaP;
int<lower=5> nP = 0;
int<lower=0> yP;

thetaP = beta_rng(alpha, beta);
nP = neg_binomial_2_rng(nMean, nDisp) + 5;
yP = binomial_rng(nP, thetaP);

}
