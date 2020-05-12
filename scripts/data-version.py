"""
Output version stamp to data/version-stamp.txt.
"""

from bookgender.logutils import start_script
from bookgender.config import data_dir, db_uri

import pandas as pd

_log = start_script(__file__)

dv_file = data_dir / 'version-stamp.txt'

with open(dv_file, 'w') as f:
    _log.info('reading source file data')
    df = pd.read_sql('''
        SELECT filename, checksum FROM source_file ORDER BY filename
    ''', db_uri())
    _log.info('read checksums for %d files', len(df))
    dv_file = data_dir / 'version-stamp.txt'
    df.to_csv(f, sep='\t', header=False, index=False, encoding='utf-8')

    df = pd.read_sql('''
        SELECT stage_name, stage_key FROM stage_status ORDER BY stage_name
    ''', db_uri())
    _log.info('read checksums for %d files', len(df))
    df.to_csv(f, sep='\t', header=False, index=False, encoding='utf-8')
