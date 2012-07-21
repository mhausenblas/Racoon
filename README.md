#Racoon - Rapid-appraisal crawler for original open data nuggets

Racoon is a targeted crawler and explorer for open data that is typically hidden in government and corporate Web sites. 

* INPUT: a seed URL and + config (doc types, crawl depth and blacklist)
* OUTPUT: description of target 'open data' documents (PDF, Excel sheets)

## Usage

	 python racoon.py -p http://example.com/start/

## Test

If you're under MacOS, which has a [built-in Apache](http://macdevcenter.com/pub/a/mac/2001/12/07/apache.html "Apache Web-Serving with Mac OS X: Part 1 - O'Reilly Media"), just copy the `racoon-test` directory to `/Library/Webserver/Documents/` and run:

	python racoon.py -s http://localhost/racoon-test

... you should then see something like:
	
	starting crawl with plain output at [http://localhost/racoon-test/] ...
	INFO:root:checking: http://localhost/racoon-test/p1.html
	INFO:root:checking: http://localhost/racoon-test/index.html
	INFO:root:checking: http://localhost/racoon-test/p1.html
	INFO:root:checking: http://localhost/racoon-test/p2.html
	INFO:root:checking: http://localhost/racoon-test/d.pdf
	INFO:root:checking: http://localhost/racoon-test/c.pdf
	INFO:root:checking: http://localhost/racoon-test/sub-dir-1/p3.html
	INFO:root:checking: http://localhost/racoon-test/sub-dir-1/e.pdf
	INFO:root:ignoring: http://www.wikipedia.org/
	INFO:root:checking: mailto:abc@def.com
	INFO:root:checking: http://localhost/racoon-test/p2.html	{
		'http://localhost/racoon-test/p2.html':
		[
			{	'URL': 'http://localhost/racoon-test/d.pdf',
				'size': '13055',
				'text': 'document d',
				'type': 'application/pdf'
			},
			{	'URL': 'http://localhost/racoon-test/c.pdf',
				'size': '13055',
				'text': 'document c',
				'type': 'application/pdf'}
		],
		'http://localhost/racoon-test/sub-dir-1/p3.html': 
		[
			{	'URL': 'http://localhost/racoon-test/sub-dir-1/e.pdf',
				'size': '13055',
				'text': 'document e',
				'type': 'application/pdf'
			}
		]
	}
	
Under *nix you can also use the provided shell script [`rr`](https://github.com/mhausenblas/Racoon/blob/master/rr) (short for run racoon), like so:

	 ./rr http://localhost/racoon-test/ r.json

... which will store the crawl results in the file `r.json` and provide you with an overall execution time report.

If you want to, you can restrict the number of pages to be visited by setting the `LIMIT` variable in [`racoon.py`](https://github.com/mhausenblas/Racoon/blob/master/racoon.py).

## License

This software is Public Domain.
