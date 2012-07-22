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

DEFAULT_STRATEGY = 'breadth' # change to 'depth' if you prefer a depth-first crawl over a breadth-first crawl
DEFAULT_POLITNESS = 0.2 # that is, wait 0.2 sec between two sub-sequent requests at a site
DEFAULT_FORMAT = 'plain' # output the plain object dump - 'json' outputs a valid JSON string instead
MIN_POLITNESS = 0.05 # wait at least wait 50ms between two sub-sequent requests at a site - set it only lower when you know what you're doing

LIMIT = -1 # visit only LIMIT pages - if you want to crawl without limits, set to -1
HTML_CONTENT_TYPES = ['text/html', 'application/xhtml+xml'] # based on http://www.whatwg.org/specs/web-apps/current-work/multipage/iana.html
EXCLUDED_URI_REFS = ['mailto', 'ftp']

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
	def crawl(self, host_loc, cur_loc, link_text='', limit=LIMIT, strategy=DEFAULT_STRATEGY):
		if limit > 0:
			if strategy == 'breadth':
				if len(self.seen) <= LIMIT:
					if self.verbose: logging.info('link count: %s' %len(self.seen))
					self.breadth_first(host_loc, cur_loc, link_text, limit)
				else: return
			else:
				if len(self.seen) <= LIMIT:
					if self.verbose: logging.info('link count: %s' %len(self.seen))
					self.breadth_first(host_loc, cur_loc, link_text, limit)
				else: return
		else:
			if strategy == 'breadth':
				self.breadth_first(host_loc, cur_loc, link_text, limit)
			else:
				self.depth_first(host_loc, cur_loc, link_text, limit)
	
	# breadth first crawl: fetches from location, extract all nuggets and then extracts hyperlinks and recursively crawl them
	def breadth_first(self, host_loc, cur_loc, link_text='', limit = LIMIT):
		# check if we're allowed to crawl it (as of robots.txt) and we're not going in circles and ignore schemes such as mailto: and ftp:
		if self.rp.can_fetch("*", cur_loc) and cur_loc not in self.seen and not urlparse(cur_loc).scheme in EXCLUDED_URI_REFS: 
			self.seen.append(cur_loc) # remeber what links we have already traversed
			if DEBUG: logging.debug('visited: %s' %self.seen)
			(headers, content) = self.get(cur_loc)
			if headers:
				try:
					ct = headers['content-type']
				except:
					ct = 'unknown'
				try:
					cl = headers['content-length']
				except:
					cl = 'unknown'
				logging.info('At URL %s with media type %s and %s bytes content length' %(cur_loc, ct, cl))
				time.sleep(self.politeness)
				(links, links_text) = self.extract_hyperlinks(cur_loc, content, limit)
				baseURL = self.extract_base(content, cur_loc)
				# first get all the nuggets from the current location
				for link in links:
					if not link.startswith('http://'): # stay in the domain, only relative links, no outbound links 
						nugget = urljoin(cur_loc, link)
						(headers, content) = self.get(nugget)
						if headers:
							try:
								ct = headers['content-type']
							except:
								ct = 'unknown'
							try:
								cl = headers['content-length']
							except:
								cl = 'unknown'
							if not self.is_html(ct):  # potentially found a nugget, add to list
								logging.info('- adding nugget %s (from %s)' %(nugget, host_loc))
								lt = links_text[link]
								try:
									self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
								except KeyError, e:
									self.nuggets[cur_loc] = []
									self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
				# ... and now crawl the rest of the site-internal hyperlinks
				for link in links:
					if not link.startswith('http://'): # stay in the domain, only relative links, no outbound links
						logging.info('- considering relative link %s resolving to %s' %(link, urljoin(baseURL, link)))
						self.breadth_first(host_loc, urljoin(host_loc, link), links_text[link], limit)
					else:
						logging.info('- ignoring outgoing link %s' %link)
	
	# depth first crawl: fetches from location, extracts hyperlinks, recursively crawl them and then extract nuggets
	def depth_first(self, host_loc, cur_loc, link_text='', limit = LIMIT):
		# check if we're allowed to crawl it (as of robots.txt) and we're not going in circles and ignore schemes such as mailto: and ftp:
		if self.rp.can_fetch("*", cur_loc) and cur_loc not in self.seen and not urlparse(cur_loc).scheme in EXCLUDED_URI_REFS: 
			self.seen.append(cur_loc) # remeber what links we have already traversed
			if DEBUG: logging.debug('visited: %s' %self.seen)
			(headers, content) = self.get(cur_loc)
			if headers:
				try:
					ct = headers['content-type']
				except:
					ct = 'unknown'
				try:
					cl = headers['content-length']
				except:
					cl = 'unknown'
				logging.info('At URL %s with media type %s and %s bytes content length' %(cur_loc, ct, cl))
				if self.is_html(ct): # we are on an HTML page, so recursively crawl
					time.sleep(self.politeness)
					self.follow_hyperlinks(cur_loc, content, limit)
				else: # potentially found a nugget, add to list
					if link_text: lt = link_text
					else: lt = ''
					logging.info('- adding nugget %s (from %s)' %(cur_loc, host_loc))
					try:
						self.nuggets[host_loc].append({ 'URL' : cur_loc, 'text' : lt, 'type' : ct , 'size' : cl})
					except KeyError, e:
						self.nuggets[host_loc] = []
						self.nuggets[host_loc].append({ 'URL' : cur_loc, 'text' : lt, 'type' : ct , 'size' : cl})
	
	# check if we're really dealing with an HTML media type
	def is_html(self, content_type):
		if content_type in HTML_CONTENT_TYPES: return True
		else: return False
	
	# extract all hyperlinks (<a href='' ...>) from an HTML content and return as list
	def extract_hyperlinks(self, host_loc, content, limit):
		links = []
		links_text = {}
		for link in BeautifulSoup(content, parseOnlyThese=SoupStrainer('a')):
			if link.has_key('href'):
				links.append(link['href'])
				links_text[link['href']] = link.renderContents()
		return (links, links_text)
	
	# extract base URL from an HTML content
	def extract_base(self, content, cur_loc):
		baseURL = cur_loc
		for base in BeautifulSoup(content, parseOnlyThese=SoupStrainer('base')):
			if base.has_key('href'):
				baseURL = base['href']
		return baseURL
	
	# extract all hyperlinks (<a href='' ...>) from an HTML content and follow them recursively
	def follow_hyperlinks(self, host_loc, content, limit):
		links = []
		links_text = {}
		for link in BeautifulSoup(content, parseOnlyThese=SoupStrainer('a')):
			if link.has_key('href'):
				links.append(link['href'])
				links_text[link['href']] = link.renderContents()
				if DEBUG: logging.debug('checking %s' %link)
				if not link['href'].startswith('http://'): # stay in the domain, only relative links, no outbound links 
					logging.info('- considering relative link %s resolving to %s' %(link['href'], urljoin(host_loc, link['href'])))
					self.depth_first(host_loc, urljoin(host_loc, link['href']), links_text[link['href']], limit)
				else:
					logging.info('- ignoring outgoing link %s' %link['href'])
	
	# dereference a URL and try to return the HTTP headers and the content 
	def get(self, url):
		try:
			#response = urlopen(url)
			req = Request(url)
			req.add_header('User-agent', 'Racoon v0.1')
			response = urlopen(req)
		except HTTPError, e:
			if DEBUG: logging.debug('Server could not fulfill the request to GET %s and responded with %s' %(url, e.code))
			return (None, e.code)
		except URLError, e:
			if DEBUG: logging.debug('Seems we failed to reach the server; reason: %s ' %e.reason)
			return (None, e.reason)
		else:
			content = response.read() 
			headers = response.info()
			return (headers, content)
	
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
	print("Example 3 : python racoon.py -s http://localhost/racoon-test/ -f json -c depth -p 0.3 -v")
	print("="*80)
	print("Parameter:")
	print("-s or --seed ... REQUIRED: specifies the seed URL to start the crawl from")
	print("-f or --format ... OPTIONAL: sets output format, allowed values are 'plain' or 'json' - defaults to plain text format")
	print("-c or --crawl ... OPTIONAL: sets crawl strategy, allowed values are 'breadth' or 'depth' - defaults to breadth-first (all nuggets from a page are extracted, then links are followed)")
	print("-l or --limit ... OPTIONAL: sets crawl limit, allowed are values >0 - defaults to no limits, that is, follow all available links within the website")
	print("-p or --politeness ... OPTIONAL: sets the crawl frequency aka politeness - defaults to 0.1 sec between two subsequent requests at a site")
	print("-v or --verbose ... OPTIONAL: provide detailed logs of what is happening")


# a very naive way to check if we have a valid seed URL
def is_valid_seed(url):
	if url and url.startswith("http://"): return True
	else: return False

# check if we have a valid format
def is_valid_format(format):
	if format in ( "plain", "json"): return True
	else: return False

# check if we have a valid crawl strategy
def is_valid_strategy(strategy):
	if strategy in ( "breadth", "depth"): return True
	else: return False

# check if we have a valid limit
def is_valid_limit(limit):
	try:
		limit = int(limit)
		if limit > 0: return (True , limit)
		else: return (False , 0)
	except:
		return (False , 0)

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
	strategy = DEFAULT_STRATEGY
	limit = -1
	politeness = DEFAULT_POLITNESS
	verbose = False
	
	try:
		# extract and validate options and their arguments
		print("="*80)
		opts, args = getopt.getopt(sys.argv[1:], "hs:f:c:l:p:v", ["help", "seed", "format", "crawl", "limit", "politeness", "verbose"])
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
			elif opt in ("-c", "--crawl"): # sets crawl strategy - optional, defaults to breadth-first (all nuggets from page are extracted, then links are followed)
				strategy = arg.strip()
				if is_valid_strategy(strategy): 
					print("Selected crawl strategy: %s" %strategy)
				else:
					print("The crawl strategy you have specified is not valid - use either 'breadth' or 'depth' as parameter.")
					sys.exit()
			elif opt in ("-l", "--limit"): # sets crawl limit - optional, defaults to no limits, that is, follow all available links within the website
				(valid_limit, plimit) = is_valid_limit(arg)
				if valid_limit:
					limit = plimit
					print("Selected crawl limit: %s" %limit)
				else:
					print("The crawl limit you have specified is not valid - use a positive integer as parameter.")
					sys.exit()
			elif opt in ("-p", "--politeness"): # sets the crawl frequency aka politeness - optional, defaults to 0.1 sec between two subsequent requests at a site
				(valid_politeness, ppoliteness) = is_valid_politeness(arg)
				if valid_politeness:
					politeness = ppoliteness
					print("Selected politeness: wait %s sec between two subsequent requests at a site." %politeness)
				else:
					print("The politeness value you have specified is not valid - use a positive float greater than %f as parameter." %float(MIN_POLITNESS))
					sys.exit()
			elif opt in ("-v", "--verbose"): # provide detailed logs of what is happening
				verbose = True

		# configure and run RCrawler
		print("="*80)
		r = RCrawler(seed_url, politeness)
		r.crawl(seed_url, seed_url,limit=limit, strategy=strategy)
		
		if format == "plain":
			print("result:")
			pprint(r.desc())
		else:
			fn = datetime.datetime.now().isoformat()
			ds_file = open('crawl-result-' + fn.replace(':', '-').replace('.', '-') + '.json', 'w')
			ds_file.write(r.desc(format = 'json'))
			ds_file.close()
		
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	
	