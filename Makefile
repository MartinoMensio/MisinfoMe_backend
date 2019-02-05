dump_db:
	mongodump -d test_coinform -o dump && mongodump -d datasets_resources -o dump && echo "dumped!"

compress_dump:
	tar -zcvf dump.tar.gz dump && echo "compressed!"

create_compressed_dump: dump_db compress_dump
	echo "done"

extract_dump:
	tar -xvzf dump.tar.gz && echo "extracted"

restore:
	mongorestore --db test_coinform dump/test_coinform && mongorestore datasets_resources dump/dataset_resources && echo "restored"

import_compressed_dump: extract_dump restore
	echo "done"

clean:
	rm dump.tar.gz && rm -rf dump