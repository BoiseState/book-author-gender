library(readr)
library(dplyr)

db = src_postgres(dbname = 'openlib')
authors = tbl(db, 'cluster_first_author_gender')

genders = authors %>%
    select(bookID=cluster, authorGender=gender) %>%
    collect() %>%
    mutate(authorGender=if_else(startsWith(authorGender, "no-"), "unknown", authorGender))

write_csv(genders, "build/author-gender.csv")
az_ratings = read_csv("build/az-ratings.csv", guess_max=10000)
write_csv(semi_join(genders, az_ratings), "build/az-author-gender.csv")
bx_ratings = read_csv("build/bx-ratings.csv", guess_max=10000)
write_csv(semi_join(genders, bx_ratings), "build/bx-explicit-author-gender.csv")
bx_implicit = read_csv("build/bx-implicit.csv", guess_max=10000)
write_csv(semi_join(genders, bx_implicit), "build/bx-implicit-author-gender.csv")
