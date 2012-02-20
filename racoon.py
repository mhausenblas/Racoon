#!/usr/bin/python

""" 
  Takes  a seed HTTP URI, crawls the HTML within the pay-level domain and generates a description of target 'open data' documents (such as PDFs or Excel sheets.)

@author: Michael Hausenblas, http://sw-app.org/mic.xhtml#i
@since: 2012-02-20
@status: init
"""

import sys
import logging
import getopt
import StringIO
from urllib2 import Request, urlopen, URLError, HTTPError
from HTMLParser import HTMLParser
from pprint import pprint
import simplejson as json

# Racoon config
logging.basicConfig(level=logging.DEBUG)
DEBUG = False

class LinkExtractor(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.links = []
	
	def handle_starttag(self, tag, attrs):
		if tag != 'a':
			return
		for name, value in attrs:
			if name == 'href':
				self.links.append(value)
				break
			else:
				return

	def get_links(self):
		return self.links
	
	
class RCrawler(object):
	def __init__(self, base):
		self.base = base
		self.seen = []
		self.nuggets = {}
		
	# crawl from a seed URL
	def crawl(self, host_loc, cur_loc):
		if cur_loc not in self.seen: # make sure we avoid cycles
			self.seen.append(cur_loc) # remeber what links we have already traversed
			if DEBUG: logging.debug('visited: %s' %self.seen)
			(headers, content) = self.get(cur_loc)
			if headers:
				if DEBUG: logging.debug('url: %s, type: %s, size: %s' %(cur_loc, headers['content-type'], headers['content-length']))
				if(headers['content-type'] == 'text/html'):
					self.follow_hyperlinks(cur_loc, content)
				else:
					if DEBUG: logging.debug('host: %s, doc: %s' %(host_loc, cur_loc))
					try:
						self.nuggets[host_loc].append({ 'URL' : cur_loc, 'type' : headers['content-type'] , 'size' : headers['content-length']})
					except KeyError, e:
						self.nuggets[host_loc] = []
						self.nuggets[host_loc].append({ 'URL' : cur_loc, 'type' : headers['content-type'] , 'size' : headers['content-length']})
						
	# extract all hyperlinks (<a href='' ...>) from an HTML content and follow them recursively
	def follow_hyperlinks(self, host_loc, content):
		le = LinkExtractor()
		le.feed(content) # extract links
		links = le.get_links()
		if DEBUG: logging.debug('outgoing: %s' %links)
		for link in links:
			if DEBUG: logging.debug('checking %s' %link)
			if not link.startswith('http://'): # stay in the domain, only relative links, no outbound links
				self.crawl(host_loc, self.base + link)
				#print link
	

	# dereference a URL and try to return the HTTP headers and the content 
	def get(self, url):
		try:
			response = urlopen(url)
		except HTTPError, e:
			print 'Sorry, the server could not fulfill the request.'
			print 'Error code: ', e.code
			return (None, e.code)
		except URLError, e:
			print 'Sorry, seems we failed to reach a server.'
			print 'Reason: ', e.reason
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
	print("Usage: python racoon.py -s {seed URL} ")
	print("Example: python racoon.py -s http://localhost/racoon-test/")

if __name__ == "__main__":
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hs:", ["help", "seed"])
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				usage()
				sys.exit()
			elif opt in ("-s", "--seed"):
				print("starting crawl at [%s] ..." %arg)
				seed_url = arg
				r = RCrawler(seed_url)
				r.crawl(seed_url, seed_url)
				pprint(r.desc())
				# print r.desc(as = 'json')
				pass
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)