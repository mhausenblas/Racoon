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
import robotparser

# Racoon config
logging.basicConfig(level=logging.DEBUG)
DEBUG = False
DEFAULT_STRATEGY = 'breadth' # change to 'depth' if you prefer a depth-first crawl over a breadth-first crawl
DEFAULT_POLITNESS = 0.1 # that is, wait 0.2 sec between two sub-sequent requests at a site
LIMIT = -1 # visit only LIMIT pages - if you want to crawl without limits, set to -1
HTML_CONTENT_TYPES = ['text/html', 'application/xhtml+xml'] # based on http://www.whatwg.org/specs/web-apps/current-work/multipage/iana.html
EXCLUDED_URI_REFS = ['mailto', 'ftp']

class RCrawler(object):
	# init with the base URL of the site and a default politness of 1s wait between two hits
	def __init__(self, base, politeness = 1):
		self.base = base
		self.seen = []
		self.nuggets = {}
		self.politeness = politeness
		self.rp = robotparser.RobotFileParser()
		self.rp.set_url(urljoin(self.base, 'robots.txt'))
		self.rp.read()
	
	# crawl from a seed URL
	def crawl(self, host_loc, cur_loc, link_text='', limit=LIMIT, strategy=DEFAULT_STRATEGY):
		if limit > 0:
			if strategy == 'breadth':
				if len(self.seen) <= LIMIT:
					if DEBUG: logging.debug('link count: %s' %len(self.seen))
					self.breadth_first(host_loc, cur_loc, link_text, limit)
				else: return
			else:
				if len(self.seen) <= LIMIT:
					if DEBUG: logging.debug('link count: %s' %len(self.seen))
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
				logging.info('currently looking at url: %s, type: %s, size: %s' %(cur_loc, ct, cl))
				time.sleep(self.politeness)
				(links, links_text) = self.extract_hyperlinks(cur_loc, content, limit)
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
								logging.info('adding nugget: %s from page: %s' %(nugget, host_loc))
								lt = links_text[link]
								try:
									self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
								except KeyError, e:
									self.nuggets[cur_loc] = []
									self.nuggets[cur_loc].append({ 'URL' : nugget, 'text' : lt, 'type' : ct , 'size' : cl})
				# ... and now crawl the rest of the site-internal hyperlinks
				for link in links:
					if not link.startswith('http://'): # stay in the domain, only relative links, no outbound links 
						self.breadth_first(host_loc, urljoin(host_loc, link), links_text[link], limit)
	
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
				logging.info('currently looking at url: %s, type: %s, size: %s' %(cur_loc, ct, cl))
				if self.is_html(ct): # we are on an HTML page, so recursively crawl
					time.sleep(self.politeness)
					self.follow_hyperlinks(cur_loc, content, limit)
				else: # potentially found a nugget, add to list
					if link_text: lt = link_text
					else: lt = ''
					logging.info('adding nugget: %s from page: %s' %(cur_loc, host_loc))
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
					logging.info('consider outgoing: %s' %urljoin(host_loc, link['href']))
					self.crawl(host_loc, urljoin(host_loc, link['href']), links_text[link['href']], limit)
				else:
					logging.info('ignoring outgoing: %s' %link['href'])
	
	# dereference a URL and try to return the HTTP headers and the content 
	def get(self, url):
		try:
			#response = urlopen(url)
			req = Request(url)
			req.add_header('User-agent', 'Racoon v0.1')
			response = urlopen(req)
		except HTTPError, e:
			if DEBUG: logging.debug('Sorry, the server could not fulfill the request.')
			if DEBUG: logging.debug('Error code: %s ' %e.code)
			return (None, e.code)
		except URLError, e:
			if DEBUG: logging.debug('Sorry, seems we failed to reach a server.')
			if DEBUG: logging.debug('Reason: %s ' %e.reason)
			return (None, e.reason)
		else:
			content = response.read() 
			headers = response.info()
			return (headers, content)
	
	# return the description of the crawled Open Data documents
	def desc(self, as = 'text'):
		if as == 'text':
			return self.nuggets
		if as == 'json':
			encoder = json.JSONEncoder()
			return encoder.encode(self.nuggets)
	
	
def usage():
	print("Usage: python racoon.py -p|-j {seed URL} where -p produces a plain output and -j a JSON output.")
	print("Example: python racoon.py -p http://localhost/racoon-test/")

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hp:j:", ["help", "plain", "json"])
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				usage()
				sys.exit()
			elif opt in ("-p", "--plain"):
				print("starting crawl with plain output at [%s] ..." %arg)
				seed_url = arg
				r = RCrawler(seed_url, DEFAULT_POLITNESS)
				r.crawl(seed_url, seed_url)
				print("result:")
				pprint(r.desc())
			elif opt in ("-j", "--json"):
				seed_url = arg
				r = RCrawler(seed_url, DEFAULT_POLITNESS)
				r.crawl(seed_url, seed_url)
				print r.desc(as = 'json')
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	
	