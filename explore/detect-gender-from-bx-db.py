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

path_output = '../build'

path_author_gender = path_output + '/bx-author-gender.csv'

with open(path_author_gender, 'w') as author_gender:
    writer_author_gender = csv.writer(author_gender, delimiter=',', quoting=csv.QUOTE_ALL)
    writer_author_gender.writerow(['bookID', 'authorName', 'authorGender'])

    count = 1

    # Each row has book_id, author_id, author_name
    # Use view bx_book_info
    cur.execute("SELECT * FROM bx_book_info")
    for row in cur:
        book_id = row[0]
    
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
        sys.stdout.write('{} processed.'.format(count))
        sys.stdout.flush()
        count += 1

