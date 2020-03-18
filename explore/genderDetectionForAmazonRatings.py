import psycopg2
import sys
import csv
from gender_detector import GenderDetector
from nameparser import HumanName
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

path_sample_ratings = '../build/Ratings-All-Amazon.csv'
path_book_authors = '../build/Book-Authors-Amazon.csv'
path_author_gender = '../build/author-gender-amazon.csv'


# Keep a dictionary of book ids and authors ids in format ["book_id": "author_id"]
with open(path_book_authors, 'rb') as book_authors:
        book_author_dict = dict((row[0], row[2]) for row in csv.reader(book_authors, delimiter=',', quoting=csv.QUOTE_NONE))
        book_authors.close()

with open(path_sample_ratings, 'rb') as sample_ratings, \
     	open(path_author_gender, 'w') as author_gender:

		reader_ratings = csv.reader(sample_ratings, delimiter=',', quoting=csv.QUOTE_NONE)
		writer_author_gender = csv.writer(author_gender, delimiter=',', quoting=csv.QUOTE_ALL)
		writer_author_gender.writerow(['bookID', 'authorName', 'authorGender'])

		bookIDSet = set()

		it = iter(reader_ratings)

		for row in it:
			bookIDSet.add(row[1])

		count = 1
		print("### Searching for author gender ###")
		for book_id in bookIDSet:
			author_id = book_author_dict.get(book_id)
			if author_id is not None:
				author_key = '/authors/' + author_id
				cur.execute("SELECT author_id, author_key, author_name FROM authors WHERE author_key = %s", (author_key,))
				rows = cur.fetchall()
				for row in rows:
					author_name = row[2]
					name_elements = {}
					try:
						name_elements = HumanName(author_name)
					except Exception:
						continue
					first_name = name_elements.first
					if first_name.isalpha():
						try:
							gender = detector.guess(first_name)
							writer_author_gender.writerow([book_id, author_name, gender])
						except KeyError:
							continue

			sys.stdout.write('\r')
			sys.stdout.write(str(count) + ' out of ' + str(len(bookIDSet)) + ' processed.')
			sys.stdout.flush()
			count += 1

		sample_ratings.close()
		author_gender.close()
	

