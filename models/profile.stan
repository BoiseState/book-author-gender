data {
    // The number of users
    int<lower=0> J;
    // Each user's number of known-gender books
    int<lower=5> n[J];
    // Each user's number of female-authored books
    int<lower=0> y[J];
}

transformed data {
    // The model performs better when we model number of books _after 5_ from negative binomial
    int<lower=0> shiftN[J];

    for (i in 1:J) {
        shiftN[i] = n[i] - 5;
    }
}

parameters {
    // Rate and probability of profile sizes
    real<lower=0> nRate;
    real<lower=0, upper=1> nProb;
    // beta params
    real<lower=0> nAlpha;
    real<lower=0> nBeta;
    // Mean of user profile bias
    real mu;
    // SD of user profile bias
    real<lower=0> sigma;
    // Users' smoothed biases, in log-odds
    vector[J] nTheta;
}

transformed parameters {
    // Users' smoothed biases, as proportions
    vector<lower=0,upper=1>[J] theta;
    // Beta for the negative binomial
    real nNB;

    theta = inv_logit(nTheta);

    nNB = 1.0 / nProb - 1;
}

model {
    // prior distribution
    // put vague priors on everything
    nRate ~ exponential(0.01);
    nAlpha ~ exponential(0.01);
    nBeta ~ exponential(0.01);
    nProb ~ beta(nAlpha, nBeta);

    mu ~ normal(0, 100);
    sigma ~ exponential(0.01);

    // likelihood model
    // user profile size
    shiftN ~ neg_binomial(nRate, nNB);
    // users' female-authored books
    y ~ binomial(n, theta);
    // and users' smoothed biases!
    nTheta ~ normal(mu, sigma);
}

generated quantities {
    // compute log_lik for WAIC and friends
    real log_lik [J];
    // we want to draw synthetic users, with their smoothed biases
    // and simulated proportions
    // this is for posterior predictive checks
    real nThetaP;
    real<lower=0, upper=1> thetaP;
    int<lower=5> nP = 0;
    int<lower=0> yP;

    nThetaP = normal_rng(mu, sigma);
    thetaP = inv_logit(nThetaP);
    nP = neg_binomial_rng(nRate, nNB) + 5;
    yP = binomial_rng(nP, thetaP);

    for (i in 1:J) {
        log_lik[i] = binomial_lpmf(y[i] | n[i], theta[i]) + neg_binomial_lpmf(shiftN[i] | nRate, nNB);
    }
}
