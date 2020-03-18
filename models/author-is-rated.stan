data {
    // the number of histogram entries
    int<lower=0> CN;
    // the count (x axis) for each histogram entry
    int<lower=0> count[CN];
    // the number of male authors with each count
    int<lower=0> bc_m[CN];
    // the number of female authors with each book count
    int<lower=0> bc_f[CN];
}
parameters {
    real<lower=0,upper=1> nzp_m;
    real<lower=0,upper=1> nzp_f;
    real<lower=0> sc_m;
    real<lower=0> sc_f;
    real<lower=0> p_m;
    real<lower=0> p_f;
}
model {
    sc_m ~ exponential(0.001);
    sc_f ~ exponential(0.001);
    p_m ~ exponential(0.001);
    p_f ~ exponential(0.001);
    // and go!
    for (i in 1:CN) {
        real n = count[i];
        int m = bc_m[i];
        int f = bc_f[i];
        if (n == 0) {
            target += m * log_sum_exp(bernoulli_lpmf(0|nzp_m), bernoulli_lpmf(1|nzp_m) + pareto_type_2_lcdf(0.5 | 0, sc_m, p_m));
            target += f * log_sum_exp(bernoulli_lpmf(0|nzp_f), bernoulli_lpmf(1|nzp_f) + pareto_type_2_lcdf(0.5 | 0, sc_f, p_f));
        } else {
            if (m > 0) {
                target += m * (bernoulli_lpmf(1|nzp_m) + log_diff_exp(pareto_type_2_lcdf(n + 0.5 | 0, sc_m, p_m),
                                           pareto_type_2_lcdf(n - 0.5 | 0, sc_m, p_m)));
            }
            if (f > 0) {
                target += f * (bernoulli_lpmf(1|nzp_f) + log_diff_exp(pareto_type_2_lcdf(n + 0.5 | 0, sc_f, p_f),
                                           pareto_type_2_lcdf(n - 0.5 | 0, sc_f, p_f)));
            }
        }
    }
}
generated quantities {
    real rc_m[500];
    real rc_f[500];
    
    for (i in 1:500) {
        if (bernoulli_rng(nzp_m) == 1) {
            rc_m[i] = pareto_type_2_rng(0, sc_m, p_f);
        } else {
            rc_m[i] = 0;
        }
        if (bernoulli_rng(nzp_f) == 1) {
            rc_f[i] = pareto_type_2_rng(0, sc_f, p_f);
        } else {
            rc_f[i] = 0;
        }
    }
}
