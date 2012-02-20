#!/usr/bin/python

""" 
  Takes  a seed HTTP URI, crawls the HTML within the pay-level domain and generates a description of target 'open data' documents (such as PDFs or Excel sheets.)

@author: Michael Hausenblas, http://sw-app.org/mic.xhtml#i
@since: 2012-02-20
@status: init
"""
import sys
import getopt
import StringIO
import urllib2
from HTMLParser import HTMLParser

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
		
	def crawl(self, cur_loc):
		response = urllib2.urlopen(cur_loc).read() # get HTML content
		le = LinkExtractor()
		le.feed(response) # extract links
		links = le.get_links()
		self.seen.append(links) # remeber what links we have already traversed
		for link in links:
			if not link.startswith('http://'):
				if link not in self.seen:
					# self.crawl(self.base + link)
					print link

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
				print("Starting crawl at [%s] ..." %arg)
				seed_url = arg
				r = RCrawler(seed_url)
				r.crawl(seed_url)
				pass
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)