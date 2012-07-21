#Racoon - Rapid-appraisal crawler for original open data nuggets

Racoon is a targeted crawler and explorer for open data that is typically hidden in government and corporate Web sites. 

* INPUT: a seed URL and crawl parameters (crawl depth, limit, frequency, output format, etc.)
* OUTPUT: description of target 'open data' documents such as PDF, Excel sheets, etc. in JSON as well as crawl info

## Usage

	python racoon.py -s http://example.com/start/

	python racoon.py -s http://example.com/start/ -f json
	
	python racoon.py -s http://example.com/start/ -f json -c depth -p 0.3 -v

## Crawl parameters

	-s or --seed		...	REQUIRED: specifies the seed URL to start the crawl from"

	-f or --format		...	OPTIONAL: sets output format, allowed values are 'plain' or 'json' 
							(defaults to plain text format; when 'json' is selected it creates a
							 valid JSON document in the current directory that reads something like
							 'crawl-result-2012-07-21T18-48-33-406027.json')

	-c or --crawl		...	OPTIONAL: sets crawl strategy, allowed values are 'breadth' or 'depth' 
							(defaults to breadth-first, i.e., all nuggets from a page are extracted,
		 					 then links are followed; depth-first is the other way round ;)

	-l or --limit		...	OPTIONAL: sets crawl limit, allowed are values >0
							(defaults to no limits, that is, follow all available links within the website)

	-p or --politeness	...	OPTIONAL: sets the crawl frequency aka politeness
							(defaults to 0.1 sec between two subsequent requests at a site)

	-v or --verbose		...	OPTIONAL: provide detailed logs of what is happening

## Local testing

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

	 ./rr http://localhost/racoon-test/

... which will store the crawl results in a file called something like `crawl-result-2012-07-21T18-48-33-406027.json` in the directory where you run the script as well as provide you with information about the overall execution time.

Note: if you know what you're doing, you can change the minimal allowed request frequency (aka politeness) in [`racoon.py`](https://github.com/mhausenblas/Racoon/blob/master/racoon.py) by changing `MIN_POLITNESS`.

## Dependencies

Racoon comes out of the box with everything you need. It has been tested under Python 2.6 and 2.7 and depends on [`BeautifulSoup`](http://www.crummy.com/software/BeautifulSoup/), which is included.

## License

This software is Public Domain.
