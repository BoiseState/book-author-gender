data {
    // The number of algorithms
    int<lower=0> A;
    // The number of data points
    int<lower=0> J;
    // The number of user,rec pairs
    int<lower=0> NL;
    // The user profile sizes
    int<lower=0> n[J];
    // The user profile female author counts
    int<lower=0> y[J];
    // The user rec list users
    int<lower=0> ru[NL];
    // The user rec list algorithms
    int<lower=0> ra[NL];
    // The user rec list sizes
    int<lower=0> rn[NL];
    // The user rec list female author counts
    int<lower=0> ry[NL];
}
parameters {
    // user profile distribution parameters
    real<lower=0> rate;
    real<lower=0,upper=1> phi;
    real<lower=0.1> lambda;
    // recommender intercepts
    vector[A] recB;
    // recommender slopes
    vector[A] recS;
    // user profile biases (ignored)
    real<lower=0,upper=1> theta[J];
}
transformed parameters {
    // user profile distribution parameters
    real<lower=0> alpha;
    real<lower=0> beta;

    // recommender profile biases (ignored)
    real<lower=0,upper=1> thetaR[NL];

    alpha = lambda * phi;
    beta = lambda * (1 - phi);

    // RL bias is a function of user bias
    for (i in 1:NL) {
        thetaR[i] = inv_logit(recB[ra[i]] + recS[ra[i]] * logit(theta[ru[i]]));
    }
}
model {
    // priors for user profile distribution
    phi ~ beta(1,1);
    lambda ~ pareto(0.1, 1.5);
    
    // priors for recommender biases and slopes
    recB ~ normal(0, 10);
    recS ~ normal(0, 10);
    
    // model user profile
    n ~ poisson(rate);
    theta ~ beta(alpha, beta);
    y ~ binomial(n, theta);
    
    // model recommendation lists
    // then we generate
    ry ~ binomial(rn, thetaR);
    // ry ~ binomial(rn, thetaR);
}
generated quantities {
    real thetaP;
    int nP;
    int yP;
    vector[A] thetaRP;
    int yRP[A];
    thetaP = beta_rng(alpha, beta);
    nP = poisson_rng(rate);
    yP = binomial_rng(nP, thetaP);
    thetaRP = inv_logit(recB + recS * logit(thetaP));
    for (i in 1:A) {
        yRP[i] = binomial_rng(50, thetaRP[i]);
    }
}
