data {
    int<lower=0> total_male;
    int<lower=0> total_female;
    int<lower=0> J;
    int<lower=0> user_male[J];
    int<lower=0> user_female[J];
}
parameters {
    real mu_m;
    real mu_f;
    real<lower=0> sigma_m;
    real<lower=0> sigma_f;
    
    real u_m_odds[J];
    real u_f_odds[J];
}
transformed parameters {
    real u_m_prob[J];
    real u_f_prob[J];
    
    u_m_prob = inv_logit(u_m_odds);
    u_f_prob = inv_logit(u_f_odds);
}
model {
    mu_m ~ normal(0, 100);
    mu_f ~ normal(0, 100);
    sigma_m ~ exponential(0.001);
    sigma_f ~ exponential(0.001);
    
    u_m_odds ~ normal(mu_m, sigma_m);
    u_f_odds ~ normal(mu_f, sigma_f);
    
    user_male ~ binomial(total_male, u_m_prob);
    user_female ~ binomial(total_female, u_f_prob);
}
generated quantities {
    real u_lor[J];
    real mloP;
    real floP;
    real lorP;
    
    for (u in 1:J) {
        u_lor[u] = u_f_odds[u] - u_m_odds[u];
    }
    
    mloP = normal_rng(mu_m, sigma_m);
    floP = normal_rng(mu_f, sigma_f);
    lorP = floP - mloP;
}
