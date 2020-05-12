data {
    // The number of users
    int<lower=0> J;
    // Each user's number of known-gender books
    int<lower=5> n[J];
    // Each user's number of female-authored books
    int<lower=0> y[J];

    // Number of algorithms
    int<lower=0> A;
    // Number of recommendation lists
    int<lower=0> NL;
    // User for each rec list
    int<lower=1,upper=J> ru[NL];
    // Algorithm for each rec list
    int<lower=1,upper=A> ra[NL];
    // Number of known-gender books in each rec list
    int<lower=0> rn[NL];
    // Number of female-authored books in each rec list
    int<lower=0> ry[NL];

}

parameters {
    // mean of user profile bias
    real mu;
    // SD of user profile bias
    real<lower=0> sigma;
    // Users' smoothed biases, in log-odds
    vector[J] nTheta;

    // Recommender response intercepts
    vector[A] recB;
    // Recommender response slopes
    vector[A] recS;
    // Recommender response variance
    vector<lower=0>[A] recV;

    // Individual recommender noise
    vector[NL] _noiseR;
}

model {
    vector[NL] rbias;
    vector[J] theta = inv_logit(nTheta);

    // profile prior distribution
    mu ~ normal(0, 10);
    sigma ~ exponential(0.1);

    // rec list priors
    recB ~ normal(0, 10);
    recS ~ normal(0, 10);
    recV ~ exponential(2);  // encourage to be small


    // profile likelihood model
    nTheta ~ normal(mu, sigma);
    y ~ binomial(n, theta);

    // rec list likelihood model - noise and binomial choice
    _noiseR ~ normal(0, recV[ra]);
    rbias = inv_logit(recB[ra] + recS[ra] .* nTheta[ru] + _noiseR);
    ry ~ binomial(rn, rbias);
}

generated quantities {
    // compute log_lik for WAIC and friends
    real log_lik [J];
    // Simulate a user + their recommendation output proportions
    real nThetaP;
    real<lower=0, upper=1> thetaP;

    vector[A] biasP;
    vector[A] noiseP;
    vector[A] thetaRP;

    nThetaP = normal_rng(mu, sigma);
    thetaP = inv_logit(nThetaP);

    biasP = recB + recS * nThetaP;
    for (a in 1:A) {
        noiseP[a] = normal_rng(0, recV[a]);
    }
    thetaRP = inv_logit(noiseP + biasP);

    // accumulate profile log_lik
    for (i in 1:J) {
        log_lik[i] = binomial_lpmf(y[i] | n[i], inv_logit(nTheta[i]));
    }
    
    // accumulate list log_lik
    for (i in 1:NL) {
        int ai = ra[i];
        log_lik[ru[i]] += binomial_lpmf(ry[i] | rn[i], inv_logit(recB[ai] + recS[ai] * nTheta[ru[i]] + _noiseR[i]));
        log_lik[ru[i]] += normal_lpdf(_noiseR[i] | 0, recV[ai]);
    }
}
