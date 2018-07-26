data {
    int<lower=0> B;
    int<lower=0,upper=1> book_gender[B];
    int<lower=0> book_count[B];
}
parameters {
    real<lower=0,upper=1> zp[2];
    real<lower=0> pr[2];
}
model {
    // zp is uniform
    // pr is a vague exponential
    pr ~ exponential(0.001);

    for (b in 1:B) {
        if (book_count[b] > 0) {
            target += bernoulli_lpmf(0 | zp[book_gender[b]+1]) +
                poisson_lpmf(book_count[b] | pr[book_gender[b]+1]);
        } else {
            target += log_sum_exp(bernoulli_lpmf(1 | zp[book_gender[b]+1]),
                bernoulli_lpmf(0 | zp[book_gender[b]+1]) +
                    poisson_lpmf(book_count[b] | pr[book_gender[b]+1]));
        }
    }
}
