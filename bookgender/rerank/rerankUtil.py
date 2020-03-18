import pandas as pd

def getBookGender():
    book_gender = pd.read_csv('data/author-gender.csv.gz')
    book_gender = book_gender.set_index('item')['gender']
    book_gender.loc[book_gender.str.startswith('no-')] = 'unknown'
    book_gender.loc[book_gender == 'ambiguous'] = 'unknown'
    book_gender.loc[book_gender == 'unlinked'] = 'unknown'
    book_gender = book_gender.astype('category')
    return book_gender
