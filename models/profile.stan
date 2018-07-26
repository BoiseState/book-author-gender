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
real mu;
real<lower=0> sigma;
vector[J] nTheta;

}
transformed parameters {
    vector<lower=0,upper=1>[J] theta;

    theta = inv_logit(nTheta);

}
model {
    // prior distribution
    nMean ~ exponential(0.001);
nDisp ~ exponential(0.001);
mu ~ normal(0, 100);
sigma ~ exponential(0.001);

    // likelihood model
    shiftN ~ neg_binomial_2(nMean, nDisp);
y ~ binomial(n, theta);
nTheta ~ normal(mu, sigma);

}
generated quantities {
    real nThetaP;
real<lower=0, upper=1> thetaP;
int<lower=5> nP = 0;
int<lower=0> yP;

    nThetaP = normal_rng(mu, sigma);
thetaP = inv_logit(nThetaP);
nP = neg_binomial_2_rng(nMean, nDisp) + 5;
yP = binomial_rng(nP, thetaP);

}
