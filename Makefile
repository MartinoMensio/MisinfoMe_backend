dump_datasets:
	mongodump -d datasets_resources -o dump && echo "dumped datasets"

dump_credibility:
	mongodump -d credibility -o dump && echo "dumped credibility"

dump_twitter:
	mongodump -d test_coinform -o dump && echo "dumped twitter"

dump_all: dump_datasets dump_twitter
	echo "dumped all"

compress_dump:
	tar -zcvf dump.tar.gz dump && echo "compressed dump"

create_compressed_dump: dump_datasets compress_dump
	echo "done"

extract_dump:
	tar -xvzf dump.tar.gz && echo "extracted"

restore_datasets:
	mongorestore --db datasets_resources dump/datasets_resources && echo "restored datasets"

restore_twitter:
	mongorestore --db test_coinform dump/test_coinform && echo "restored twitter"

restore_all: restore_datasets
	echo "restored all"

import_compressed_dump: extract_dump restore_datasets
	echo "done"

clean:
	rm dump.tar.gz && rm -rf dump