# Historical invocation notes

These commands preserve the original working notes. They reference an older local environment, placeholder paths, and a `test.py` entry point that is not included in this directory. The flags shown for `test.py` belong to that historical ETL workflow.

For the current corporate-action extraction and snapshot-comparison commands, use the [component README](README.md).

## Original command notes

```bash
/anaconda3/bin/python diff_between_timestamped_records.py  --working-directory /xxx/

git status; git pull; git add xxx.csv; git commit -m "Art's manual ticker look up"; git push

git status; git pull; git add test.py; git commit -m "Art's SQL/Python script"; git push

/anaconda3/bin/python test.py   --start-date 1990-01-01 --working-directory ./temp/ --nblocks 100 --archive --email-notification

/anaconda3/bin/python test.py   --start-date 2017-12-01 --working-directory ./temp/ --nblocks 100 --archive 

/anaconda3/bin/python test.py   --start-date 2017-12-01 --working-directory ./temp/ --nblocks 100 --archive --top 10000

/anaconda3/bin/python test.py  --start-date 2010-01-01 --working-directory ./temp/ --nblocks 100 --top 10000 > log.txt

python test.py --top 100 -s 2019-11-01 -d ./temp/ -n 100
```
