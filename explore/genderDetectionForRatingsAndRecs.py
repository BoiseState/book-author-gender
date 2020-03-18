import psycopg2
import sys
import csv
from gender_detector import GenderDetector
import os

# Set gender detector database
detector = GenderDetector('us') # It can also be ar, uk, uy.

# Set up database connection
bias_db = os.environ['BIAS_DB']
bias_user = os.environ['BIAS_USER'] 
bias_host = os.environ['BIAS_HOST'] 
bias_passwd = os.environ['BIAS_PASSWORD'] 


try:
    conn = psycopg2.connect(dbname=bias_db, user=bias_user, port='5432', host=bias_host, password=bias_passwd, sslmode='require')
except:
    print "I am unable to connect to the database"

cur = conn.cursor()

# Set this to max size to avoid exceeded field limit error
csv.field_size_limit(sys.maxsize)

path_output = '../build'


path_sample_ratings = path_output + '/Ratings-All.csv'
path_book_authors = path_output + '/Book-Authors.csv'
path_author_gender = path_output + '/author-gender.csv'
path_recommendation = path_output + '/eval-recommendation.csv'


# Keep a dictionary of book ids and authors ids in format ["book_id": "author_id"]
with open(path_book_authors, 'rb') as book_authors:
        book_author_dict = dict((row[0], row[2]) for row in csv.reader(book_authors, delimiter=',', quoting=csv.QUOTE_NONE))
        book_authors.close()

with open(path_sample_ratings, 'rb') as sample_ratings, \
     	open(path_author_gender, 'w') as author_gender, \
		open(path_recommendation, 'rb') as recommendations:

		reader_ratings = csv.reader(sample_ratings, delimiter=',', quoting=csv.QUOTE_NONE)
		reader_recs = csv.reader(recommendations, delimiter=',', quoting=csv.QUOTE_NONE)
		writer_author_gender = csv.writer(author_gender, delimiter=',', quoting=csv.QUOTE_ALL)
		writer_author_gender.writerow(['bookID', 'authorName', 'authorGender'])

		bookIDSet = set()

		# Combine all book ids from ratings and recommendations
		it = iter(reader_ratings)
		# Skip the first row (usually csv column headers)
		next(it, None)
		for row in it:
			bookIDSet.add(row[1])

		it = iter(reader_recs)
		next(it, None)
		for row in it:
			bookIDSet.add(row[4])

		for book_id in bookIDSet:
			count = 1
			author_id = book_author_dict.get(book_id)
			if author_id is not None:
				author_key = '/authors/' + author_id
				cur.execute("SELECT author_id, author_key, author_name FROM authors WHERE author_key = %s", (author_key,))
				rows = cur.fetchall()

				for row in rows:
					author_name = row[2]
					full_name = author_name.split()
					first_name = full_name[0]
					if first_name.isalpha():
						gender = detector.guess(first_name)
						writer_author_gender.writerow([book_id, author_name, gender])

			sys.stdout.write('\r')
			sys.stdout.write(str(count) + ' out of ' + str(len(bookIDSet)) + ' processed.')
			sys.stdout.flush()
			count += 1

		sample_ratings.close()
		author_gender.close()
	

