#!/usr/bin/python

""" 
  Takes  a seed HTTP URI, crawls the HTML within the pay-level domain 
  and generates a description of target 'open data' documents 
  (such as PDFs or Excel sheets).

@author: Michael Hausenblas, http://sw-app.org/mic.xhtml#i
@since: 2012-02-20
@status: init
"""

import sys
import logging
import getopt
import StringIO
from urllib2 import Request, urlopen, URLError, HTTPError
from urlparse import urljoin, urlparse
from BeautifulSoup import BeautifulSoup, SoupStrainer
from pprint import pprint
import simplejson as json
import time
import datetime
import robotparser

# Racoon config
DEBUG = False

if DEBUG:
	FORMAT = '%(asctime)-0s %(levelname)s %(message)s [at line %(lineno)d]'
else:
	FORMAT = '%(asctime)-0s %(message)s'
	
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt='%Y-%m-%dT%I:%M:%S')

DEFAULT_POLITNESS = 0.2 # that is, wait 0.2 sec between two sub-sequent requests at a site
DEFAULT_FORMAT = 'plain' # output the plain object dump - 'json' outputs a valid JSON string instead
MIN_POLITNESS = 0.05 # wait at least wait 50ms between two sub-sequent requests at a site - set it only lower when you know what you're doing

HTML_CONTENT_TYPES = ['text/html', 'application/xhtml+xml'] # based on http://www.whatwg.org/specs/web-apps/current-work/multipage/iana.html
EXCLUDED_URI_REFS = ['mailto', 'ftp']

RACOON_AGENT = 'Racoon v0.1'

class RCrawler(object):
	# init with the base URL of the site and a default politness of 1s wait between two hits
	def __init__(self, base, politeness = DEFAULT_POLITNESS, verbose = False):
		self.base = base
		self.seen = []
		self.nuggets = {}
		self.politeness = politeness
		self.rp = robotparser.RobotFileParser()
		self.rp.set_url(urljoin(self.base, 'robots.txt'))
		self.rp.read()
		self.verbose = verbose
	
	# crawl from a seed URL
	def crawl(self, seed_URL, descend = False):
		self.seed = seed_URL
		self.breadth_first(self.seed, descend)
		try:
			return ('Crawl completed with %d locations seen in total and found nuggets in %d locations.' %(len(self.seen), len(self.nuggets)))
		except:
			return ('Crawl completed with %d locations seen in total but found no nuggets.' %(len(self.seen)))
	
	# breadth first crawl: 
	# 1. fetch content from current location
	# 2. extracts all links from current location
	# 3. extract all nuggets from current location
	# 4. ... and then recursively crawl remaining links within site
	def breadth_first(self, cur_loc, descend):
		
		# if descend crawl strategy has been selected, 
		# make sure we don't bother inspecting URLs that are beyond the
		# crawl scope (only paths below seed URL)
		if descend:
			if not cur_loc.startswith(self.seed):
				if self.verbose: logging.info('The URL %s is beyond the crawl scope, retreating ...' %cur_loc)
				return
		
		# check if we're allowed to crawl the current location (as of robots.txt) and
		# if we're not going in circles (by cheking seen locations) and 
		# ignore URI schemes such as mailto: and ftp: - we only want HTTP URI
		if self.rp.can_fetch(RACOON_AGENT, cur_loc) and cur_loc not in self.seen and not urlparse(cur_loc).scheme in EXCLUDED_URI_REFS: 
			self.seen.append(cur_loc) # remember that we have already seen the current location
			
			# 1. fetch content from current location and try to determine content type (ct) and content length (cl):
			(ct, cl, content) = self.get(cur_loc)
			if ct:
				logging.info('At URL %s with media type [%s] and [%s bytes] content length' %(cur_loc, ct, cl))
				# 2. extract all (relative and absolute) links from current location
				# along with their link text (like so: <a href='LINK'>LINK_TEXT</a>):
				(links, links_text) = self.extract_hyperlinks(content) 
				# determine base URL to resolve relative links against - takes <base href="" /> into acccount:
				base_URL = self.extract_base(cur_loc, content)

				# 3. extract all nuggets from current location:
				for link in links:
					# use only relative links to stay within the site by checking if it starts with 'http://'
					if not link.startswith('http://'):
						nugget = urljoin(base_URL, link)
						time.sleep(self.politeness)
						(ct, cl, content) = self.get(nugget)
						# if it turns out the nugget leads to open data gold, that is, we got a non-HTML content type
						# add it to the result list ...
						if ct and not self.is_html(ct):  
							if self.verbose: logging.info('- adding nugget %s (from %s)' %(nugget, cur_loc))
							lt = links_text[link]
							try:
								self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
							except KeyError, e:
								self.nuggets[cur_loc] = []
								self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
							# ... as well as put it on the list of already seen links to minimise crawl footprint:
							self.seen.append(nugget)
					else:
						if self.verbose: logging.info('- ignoring outgoing link %s' %link)
				try:
					logging.info('Added %d nugget(s) from %s, now following further links ...' %(len(self.nuggets[cur_loc]), cur_loc))
				except KeyError, e:
					logging.info('No nuggets found at %s, now following further links ...' %(cur_loc))

				# 4. ... and then recursively crawl remaining links within site:
				for link in links:
					# use only relative links to stay within the site by checking if it starts with 'http://'
					if not link.startswith('http://'):
						if self.verbose: logging.info('- considering relative link %s resolving to %s' %(link, urljoin(base_URL, link)))
						self.breadth_first(urljoin(base_URL, link), descend)
					else:
						if self.verbose: logging.info('- ignoring outgoing link %s' %link)
		elif not self.rp.can_fetch(RACOON_AGENT, cur_loc):
			if self.verbose: logging.info('- skipping %s as I am not allowed to crawl it' %cur_loc)
			return
		elif cur_loc in self.seen:
			if self.verbose: logging.info('- skipping %s as already seen it' %cur_loc)
			return
		elif urlparse(cur_loc).scheme in EXCLUDED_URI_REFS:
			if self.verbose: logging.info('- skipping %s as not an HTTP URI' %cur_loc)
			return
		
	# check if we're really dealing with an HTML media type
	def is_html(self, content_type):
		if content_type in HTML_CONTENT_TYPES: return True
		else: return False
	
	# extract and resolve all hyperlinks (<a href='LINK'>LINK_TEXT</a>) from an HTML content and return as list
	def extract_hyperlinks(self, content):
		links = []
		links_text = {}
		for link in BeautifulSoup(content, parseOnlyThese=SoupStrainer('a')):
			if link.has_key('href'):
				links.append(link['href'])
				links_text[link['href']] = link.renderContents()
		return (links, links_text)
	
	# extract base URL from an HTML content
	def extract_base(self, cur_loc, content):
		baseURL = cur_loc
		for base in BeautifulSoup(content, parseOnlyThese=SoupStrainer('base')):
			if base.has_key('href'):
				baseURL = base['href']
		return baseURL
	
	# dereference a URL and try to return the HTTP headers and the content 
	def get(self, url):
		try:
			#response = urlopen(url)
			req = Request(url)
			req.add_header('User-agent', RACOON_AGENT)
			response = urlopen(req)
		except HTTPError, e:
			if DEBUG: logging.debug('Server could not fulfill the request to GET %s and responded with %s' %(url, e.code))
			return (None, None, e.code)
		except URLError, e:
			if DEBUG: logging.debug('Seems we failed to reach the server; reason: %s ' %e.reason)
			return (None, None, e.reason)
		else:
			content = response.read() 
			headers = response.info()
			if headers:
				try:
					ct = headers['content-type']
					# in case there is an additional parameter such as the character set specified
					# ignore it, for example, 'text/html;charset=UTF-8' -> 'text/html'
					# see also http://tools.ietf.org/html/rfc2616#section-14.17
					if ';' in ct:
						ct = ct.split(';')[0]
				except:
					ct = 'unknown'
				try:
					cl = headers['content-length']
				except:
					cl = 'unknown'
				return (ct, cl, content)
			else:
				if DEBUG: logging.debug('Something went wrong when evaluating the HTTP response')
				return (None, None, None)
	
	# return the description of the crawled Open Data documents
	def desc(self, format = 'plain'):
		if format == 'plain':
			return self.nuggets
		if format == 'json':
			encoder = json.JSONEncoder()
			return encoder.encode(self.nuggets)
	
	
def usage():
	print("Usage: python racoon.py -s {seed URL}")
	print("="*80)
	print("Example 1 : python racoon.py -s http://localhost/racoon-test/")
	print("Example 2 : python racoon.py -s http://localhost/racoon-test/ -f json")
	print("Example 3 : python racoon.py -s http://localhost/racoon-test/ -f json -p 0.3 -v")
	print("="*80)
	print("Parameter:")
	print("-s or --seed ... REQUIRED: specifies the seed URL to start the crawl from")
	print("-f or --format ... OPTIONAL: sets output format, allowed values are 'plain' or 'json' - defaults to plain text format")
	print("-p or --politeness ... OPTIONAL: sets the crawl frequency aka politeness - defaults to 0.1 sec between two subsequent requests at a site")
	print("-d or --descend ... OPTIONAL: perform descend crawl, that is, only follow links to paths below seed URL, not up or same level")
	print("-v or --verbose ... OPTIONAL: provide detailed logs of what is happening")

# a very naive way to check if we have a valid seed URL
def is_valid_seed(url):
	if url and url.startswith("http://"): return True
	else: return False

# check if we have a valid format
def is_valid_format(format):
	if format in ( "plain", "json"): return True
	else: return False

# check if we have a valid politeness value
def is_valid_politeness(politeness):
	try:
		politeness = float(politeness)
		if politeness > MIN_POLITNESS: return (True , politeness)
		else: return (False , 0)
	except:
		return (False , 0)


# tha main script that validates CLI input, configures and runs RCrawler
if __name__ == "__main__":
	seed_url = ""
	format = DEFAULT_FORMAT
	politeness = DEFAULT_POLITNESS
	verbose = False
	descend = False
	
	try:
		# extract and validate options and their arguments
		print("="*80)
		opts, args = getopt.getopt(sys.argv[1:], "hs:f:p:vd", ["help", "seed", "format", "politeness", "verbose", "descend"])
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				usage()
				sys.exit()
			elif opt in ("-s", "--seed"): # sets seed URL - required
				seed_url = arg
				if is_valid_seed(seed_url): 
					print("Starting crawl at seed URL: %s" %seed_url)
				else:
					print("The seed URL you have provided is not valid - use an HTTP URL as parameter.")
					sys.exit()
			elif opt in ("-f", "--format"): # sets output format - optional, defaults to plain text format
				format = arg.strip()
				if is_valid_format(format): 
					print("Selected output format: %s" %format)
				else:
					print("The output format you have specified is not valid - use either 'plain' or 'json' as parameter.")
					sys.exit()
			elif opt in ("-p", "--politeness"): # sets the crawl frequency aka politeness - optional, defaults to 0.1 sec between two subsequent requests at a site
				(valid_politeness, ppoliteness) = is_valid_politeness(arg)
				if valid_politeness:
					politeness = ppoliteness
					print("Selected politeness: wait %s sec between two subsequent requests at a site." %politeness)
				else:
					print("The politeness value you have specified is not valid - use a positive float greater than %f as parameter." %float(MIN_POLITNESS))
					sys.exit()
			elif opt in ("-d", "--descend"): # perform descend crawl (only follow links to paths below seed URL, not up or same level)
				descend = True
				print("Selected crawl type: descend, that is, only follow links to paths below seed URL, not up or same level.")
			elif opt in ("-v", "--verbose"): # provide detailed logs of what is happening
				verbose = True
				print("Selected level of reporting detail: verbose, that is, provide details of crawl status.")

		# configure and run RCrawler
		print("="*80)
		base = urlparse(seed_url)
		base = ''.join([base.scheme, '://', base.netloc, '/'])
		print("Using base URL %s" %base)
		r = RCrawler(base = base, politeness = politeness, verbose = verbose)
		cstats = r.crawl(seed_URL = seed_url, descend = descend)

		print("="*80)
		print(cstats)
		
		if format == "plain":
			print("Result:\n")
			pprint(r.desc())
		else:
			now = datetime.datetime.now().isoformat()
			result_filename = 'crawl-result-' + now.replace(':', '-').replace('.', '-') + '.json'
			ds_file = open(result_filename, 'w')
			ds_file.write(r.desc(format = 'json'))
			ds_file.close()
			print("Results are available in %s" %result_filename)
		
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)