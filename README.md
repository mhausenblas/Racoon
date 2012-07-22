#Racoon - dig up Open Data nuggets!

The _r_apid-_a_ppraisal _c_rawler for _o_riginal _o_pen data _n_uggets (_Racoon_) is a targeted crawler and explorer for Open Data nuggets, typically hidden in government and corporate Web sites. Racoon takes a *seed URL* and crawl parameters (crawl strategy, frequency, output format, etc.) as input and produces a description of potential Open Data nuggets, that is, documents such as PDF, Excel sheets, etc. as output.

The description of the identified Open Data nuggets is provided in JSON along with some crawl info (overall visited locations and locations with nuggets) and has the following structure:

	{
		'URL of location where nuggets occured': // e.g., http://example.com/start/
		[
			{	
				'URL': 'URL of the Open Data nugget', // e.g., http://example.com/start/nugget.pdf
				'size': 'content length of Open Data nugget in bytes', // e.g., 1234
				'text': 'link text to Open Data nugget', // e.g., a sample nugget
				'type': 'media type of Open Data nugget' // e.g., application/pdf
			},
			...
		],
		...
	}

## Usage

The only thing Racoon really needs to know is where to start the crawl, hence you MUST supply the seed URL via the `-s` parameter, all the other parameters are optional (see below for their meaning and allowed values). So, a minimal way to crawl a site would be:

	python racoon.py -s http://example.com/start/

If you fancy storing the result of the crawl in a file, use the `-f` parameter set to `json` like so:

	python racoon.py -s http://example.com/start/ -f json
	
You can also change the crawl frequency also known as politeness (that is, the time Racoon will wait between two subsequent HTTP requests) using the `-p` parameter and supplying a numerical value in seconds (below: wait 0.3 sec) as well as get a bit more details what is going on during the crawl using the `-v` parameter, meaning Racoon is supposed to be verbose:

	python racoon.py -s http://example.com/start/ -f json -p 0.3 -v

It is in general a good idea to use the `-d` parameter which activates the descending crawl strategy, meaning that Racoon only looks at paths that are below a given seed URL, so, for example:

	python racoon.py -s http://example.com/start/sub/ -d

... would only crawl locations below `http://example.com/start/sub/`, that is, Racoon would visit `http://example.com/start/sub/page1.html` but not `http://example.com/start/index.html`. When you first crawl a site (especially if it's not your own)  consider using this option in the first place as restricting the crawl increases the chances that you don't get banned ;)

### Examples

A number of [exemplary crawls](https://github.com/mhausenblas/Racoon/wiki/Example-crawls) are available via the project Wiki page, including the command used and the crawl result.

### Shell script

Under *nix you can also use the provided shell script [`rr`](https://github.com/mhausenblas/Racoon/blob/master/rr) (short for run racoon), like so:

	 ./rr  http://example.com/start/

... which will store the crawl results in a file called something like `crawl-result-2012-07-21T18-48-33-406027.json` in the directory where you run the script as well as provide you with information about the overall execution time. 

Note: the script is configured to be verbose in nature and to use the descend crawl strategy.


## Crawl parameters

Racoon takes the following parameters as command line options:

	-s or --seed		...	REQUIRED: specifies the seed URL to start the crawl from"

	-f or --format		...	OPTIONAL: sets output format, allowed values are 'plain' or 'json' 
							(defaults to plain text format; when 'json' is selected it creates a
							 valid JSON document in the current directory that reads something like
							 'crawl-result-2012-07-21T18-48-33-406027.json')

	-p or --politeness	...	OPTIONAL: sets the crawl frequency aka politeness, allowed are values greater MIN_POLITNESS 
							(defaults to 0.1 sec between two subsequent requests at a site)

	-d or --descend		... OPTIONAL: perform descend crawl, that is, only follow links to paths below seed URL, not up or same level

	-v or --verbose		...	OPTIONAL: provide detailed logs of what is happening

Note: if you know what you're doing, you can change the minimal allowed request frequency (aka politeness) in [`racoon.py`](https://github.com/mhausenblas/Racoon/blob/master/racoon.py) by changing `MIN_POLITNESS`.

## Local testing

If you're under MacOS, which has a [built-in Apache](http://macdevcenter.com/pub/a/mac/2001/12/07/apache.html "Apache Web-Serving with Mac OS X: Part 1 - O'Reilly Media"), just copy the `racoon-test` directory to `/Library/Webserver/Documents/` and run:

	python racoon.py -s http://localhost/racoon-test/

... you should then see something like:
	
	================================================================================
	Starting crawl at seed URL: http://localhost/racoon-test/
	================================================================================
	2012-07-22T12:29:34 At URL http://localhost/racoon-test/ with media type [text/html] and [162 bytes] content length
	2012-07-22T12:29:34 No nuggets found at http://localhost/racoon-test/, now following further links ...
	2012-07-22T12:29:34 At URL http://localhost/racoon-test/p1.html with media type [text/html] and [346 bytes] content length
	2012-07-22T12:29:35 Added 1 nugget(s) from http://localhost/racoon-test/p1.html, now following further links ...
	2012-07-22T12:29:35 At URL http://localhost/racoon-test/index.html with media type [text/html] and [162 bytes] content length
	2012-07-22T12:29:36 No nuggets found at http://localhost/racoon-test/index.html, now following further links ...
	2012-07-22T12:29:36 At URL http://localhost/racoon-test/p2.html with media type [text/html] and [142 bytes] content length
	2012-07-22T12:29:36 Added 2 nugget(s) from http://localhost/racoon-test/p2.html, now following further links ...
	2012-07-22T12:29:36 At URL http://localhost/racoon-test/p4.html with media type [text/html] and [210 bytes] content length
	2012-07-22T12:29:36 No nuggets found at http://localhost/racoon-test/p4.html, now following further links ...
	2012-07-22T12:29:36 At URL http://localhost/racoon-test/sub-dir-1/p3.html with media type [text/html] and [111 bytes] content length
	2012-07-22T12:29:37 Added 1 nugget(s) from http://localhost/racoon-test/sub-dir-1/p3.html, now following further links ...
	================================================================================
	Crawl completed with 10 locations seen in total and found nuggets in 3 locations.
	Result:

	{u'http://localhost/racoon-test/p1.html': [{'URL': u'http://localhost/racoon-test/d.pdf',
	                                            'size': '13055',
	                                            'text': 'document d',
	                                            'type': 'application/pdf'}],
	 u'http://localhost/racoon-test/p2.html': [{'URL': u'http://localhost/racoon-test/d.pdf',
	                                            'size': '13055',
	                                            'text': 'document d',
	                                            'type': 'application/pdf'},
	                                           {'URL': u'http://localhost/racoon-test/c.pdf',
	                                            'size': '13055',
	                                            'text': 'document c',
	                                            'type': 'application/pdf'}],
	 u'http://localhost/racoon-test/sub-dir-1/p3.html': [{'URL': u'http://localhost/racoon-test/sub-dir-1/e.pdf',
	                                                      'size': '13055',
	                                                      'text': 'document e',
	                                                      'type': 'application/pdf'}]}


## Dependencies

Racoon comes out of the box with everything you need. It has been tested under Python 2.6 and 2.7 and depends on [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/), which is included.

The (experimental) HTML+JavaScript [display](https://github.com/mhausenblas/Racoon/wiki/Display) of Racoon's crawl results uses the [D3](http://d3js.org/) library.

## License

This software is Public Domain.
