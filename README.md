#Racoon - Rapid-appraisal crawler for original open data nuggets

Racoon is a targeted crawler and explorer for open data that is typically hidden in government and corporate Web sites. 

* INPUT: a seed URL and + config (doc types, crawl depth and blacklist)
* OUTPUT: description of target 'open data' documents (PDF, Excel sheets)

## Usage

	 python racoon.py -s http://example.com/start/

## Test

If you're under MacOS, which has a [built-in Apache](http://macdevcenter.com/pub/a/mac/2001/12/07/apache.html "Apache Web-Serving with Mac OS X: Part 1 - O'Reilly Media"), just copy the `racoon-test` directory to `/Library/Webserver/Documents/` and run:

	python racoon.py -s http://localhost/racoon-test

... you should then see something like:

	Starting crawl at [http://localhost/racoon-test/] ...
	p1.html
	p2.html

## License

This software is Public Domain.
