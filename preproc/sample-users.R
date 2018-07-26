library(readr)
library(dplyr)
library(getopt)

spec = matrix(c(
    'rating-table', 't', 1, 'character',
    'rating-file', 'f', 1, 'character',
    'user-output', 'u', 1, 'character',
    'rating-output', 'r', 1, 'character',
    'stub-output', 's', 1, 'character'
), byrow=TRUE, ncol=4)
opts = getopt(spec)
if (is.null(opts[['rating-table']])) stop("no rating table specified")
if (is.null(opts[['user-output']])) stop("no user output file specified")
if (is.null(opts[['rating-output']])) stop("no rating output file specified")
if (is.null(opts[['stub-output']])) stop("no stub output file specified")

db = DBI::dbConnect(RPostgreSQL::PostgreSQL(), dbname='openlib')

rating_table = tbl(db, opts[['rating-table']])
author_table = tbl(db, 'cluster_first_author_gender')

# Read rating data for known-gender authors
message("matching ratings")
matched = rating_table %>% inner_join(author_table %>% select(book_id=cluster, gender))
known = matched %>% filter(gender == 'male' | gender == 'female') %>% collect();

message("picking users")
users = known %>%
    rename(userID=user_id) %>%
    group_by(userID) %>%
    summarize(RatingCount=n())
picked.users = users %>%
    filter(RatingCount >= 5) %>%
    sample_n(1000)
    
message("collecting ratings")
ratings = rating_table %>%
    select(userID=user_id, bookID=book_id, rating) %>%
    collect()

message("writing output")
write_csv(ratings, opts[['rating-file']], col_names=TRUE)
write_csv(select(picked.users, userID), opts[['user-output']], col_names=TRUE)
write_csv(inner_join(ratings, select(picked.users, userID)), opts[['rating-output']], col_names=TRUE)
write_csv(picked.users %>% select(userID) %>% mutate(itemId=as.integer(-1), rating=0),
          opts[['stub-output']], col_names=TRUE)
