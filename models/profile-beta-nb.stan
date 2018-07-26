data {
    int<lower=0> J;
    int<lower=0> n[J];
    int<lower=0> y[J];
}
parameters {
    real<lower=0,upper=1> phi;
    real<lower=0> lambda;

    real<lower=0> nMu;
    real<lower=0> nDisp;

    real<lower=0,upper=1> theta[J];
}
transformed parameters {
    real<lower=0> alpha;
    real<lower=0> beta;
    alpha = lambda * phi;
    beta = lambda * (1 - phi);
}
model {
    phi ~ beta(1,1);
    lambda ~ lognormal(0, 5);

    nMu ~ lognormal(0, 5);
    nDisp ~ lognormal(0, 5);

    theta ~ beta(alpha, beta);
    n ~ neg_binomial_2(nMu, nDisp);
    y ~ binomial(n, theta);
}
generated quantities {
    real thetaP;
    int<lower=0> nP;
    int<lower=0> yP;
    
    thetaP = beta_rng(alpha, beta);
    nP = neg_binomial_2_rng(nMu, nDisp);
    yP = binomial_rng(nP, thetaP);
}
