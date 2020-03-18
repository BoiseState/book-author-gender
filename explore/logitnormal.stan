data {
    int<lower=0> J;
    int<lower=0> n[J];
    int<lower=0> y[J];
}
parameters {
    real mu;
    real<lower=0.01> sig2;
    real<lower=0> rate;
    real nTheta[J];
}
transformed parameters {
    real<lower=0,upper=1> theta[J];
    theta = inv_logit(nTheta);
}
model {
    mu ~ normal(0, 10);
    n ~ poisson(rate);
    nTheta ~ normal(mu, sig2);
    y ~ binomial(n, theta);
}
generated quantities {
    real<lower=0, upper=1> thetaP;
    int<lower=0> nP;
    int<lower=0> yP;
    thetaP = inv_logit(normal_rng(mu, sig2));
    nP = 5 + poisson_rng(rate);
    yP = binomial_rng(nP, thetaP);
}
