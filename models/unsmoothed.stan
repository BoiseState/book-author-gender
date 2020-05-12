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

transformed data {
    // User profile - smoothed log odds
    vector[J] pLO = logit((to_vector(y) + 1) ./ (to_vector(n) + 2));
    // Recommendation list (smoothed) proportion female
    // vector[NL] rLO = logit((to_vector(ry) + 1) ./ (to_vector(rn) + 2));
}

parameters {
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

    // rec list priors
    recB ~ normal(0, 10);
    recS ~ normal(0, 10);
    recV ~ exponential(2);  // encourage to be small

    // rec list likelihood model - noise and binomial choice
    _noiseR ~ normal(0, recV[ra]);
    rbias = inv_logit(recB[ra] + recS[ra] .* pLO[ru] + _noiseR);
    ry ~ binomial(rn, rbias);
}

generated quantities {
    // compute log_lik for WAIC and friends
    real log_lik [J] = rep_array(0, J);

    // accumulate list log_lik
    for (i in 1:NL) {
        log_lik[ru[i]] += binomial_lpmf(ry[i] | rn[i], inv_logit(recB[ra[i]] + recS[ra[i]] * pLO[ru[i]] + _noiseR[i]));
        log_lik[ru[i]] += normal_lpdf(_noiseR[i] | 0, recV[ra[i]]);
    }
}
