#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 13 12:43:21 2019

@author: zeynep
"""
import numpy as np
import urllib
import math
import re
from bs4 import BeautifulSoup
from pprint import pprint
from threading import Thread
from collections import deque
from time import sleep
        
class GoogleSearch:
    USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/ 58.0.3029.81 Safari/537.36"
    SEARCH_URL = "https://google.co.jp/search"
    RESULT_SELECTOR = ".srg h3.r a"
    TOTAL_SELECTOR = "#resultStats"
    RESULTS_PER_PAGE = 10
    DEFAULT_HEADERS = [
            ('User-Agent', USER_AGENT),
            ("Accept-Language", "en-US,en;q=0.5"),
        ]
    
    def search(self, query, num_results = 10, prefetch_pages = True, prefetch_threads = 10, language = "en"):
        searchResults = []
        pages = int(math.ceil(num_results / float(GoogleSearch.RESULTS_PER_PAGE)));
        fetcher_threads = deque([])
        total = None;
        for i in range(pages) :
            start = i * GoogleSearch.RESULTS_PER_PAGE
            opener = urllib.request.build_opener()
            opener.addheaders = GoogleSearch.DEFAULT_HEADERS
            response = opener.open(GoogleSearch.SEARCH_URL + "?q="+ urllib.parse.quote(query) + \
                                   "&tbm=nws" + "&hl=" + language + ("" if start == 0 else ("&start=" + str(start))))
            soup = BeautifulSoup(response.read(), "lxml")
            response.close()
            if total is None:
                totalText = soup.select(GoogleSearch.TOTAL_SELECTOR)[0].children.__next__().encode('utf-8')
                totalText = totalText.decode('ISO-8859-1')  # encoding may vary!
                total = int(re.sub("[',\. ]", "", re.search("(([0-9]+[',\. ])*[0-9]+)", totalText).group(1)))
            results = self.parseResults(soup.select(GoogleSearch.RESULT_SELECTOR))
            if len(searchResults) + len(results) > num_results:
                del results[num_results - len(searchResults):]
            searchResults += results
            if prefetch_pages:
                for result in results:
                    while True:
                        running = 0
                        for thread in fetcher_threads:
                            if thread.is_alive():
                                running += 1
                        if running < prefetch_threads:
                            break
                        sleep(1)
                    fetcher_thread = Thread(target=result.getText)
                    fetcher_thread.start()
                    fetcher_threads.append(fetcher_thread)
        for thread in fetcher_threads:
            thread.join()
        return SearchResponse(searchResults, total);
        
    def parseResults(self, results):
        searchResults = [];
        for result in results:
            url = result["href"];
            title = result.text
            searchResults.append(SearchResult(title, url))
        return searchResults

class SearchResponse:
    def __init__(self, results, total):
        self.results = results;
        self.total = total;

class SearchResult:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.__text = None
        self.__markup = None
    
    def getText(self):
        if self.__text is None:
            soup = BeautifulSoup(self.getMarkup(), "lxml")
            for junk in soup(["script", "style"]):
                junk.extract()
                self.__text = soup.get_text()
        return self.__text
    
    def getMarkup(self):
        if self.__markup is None:
            opener = urllib.build_opener()
            opener.addheaders = GoogleSearch.DEFAULT_HEADERS
            response = opener.open(self.url);
            self.__markup = response.read()
        return self.__markup
    
    def __str__(self):
        return  str(self.__dict__)
    def __unicode__(self):
        return unicode(self.__str__())
    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    import sys
    search = GoogleSearch()
    result = []
    
    f = open('country_capital_fulllist.txt',encoding="utf8")
    
    cnt_cap_jp = np.loadtxt(f, \
                       delimiter='\t', usecols=(0,1,2,3), \
                       skiprows=0,
                       dtype=np.str  
                       )

     # or use usecols=(0,1) in the above
    count = 10

    for query in cnt_cap_jp:
        
        query_cnt = query[0]
        query_cap = query[1]
       
        
        print ("Fetching first " + str(count) + " results for \"" + query_cnt + "\"...")
        response_cnt = search.search(query_cnt, count)
        print ("TOTAL: " + str(response_cnt.total) + " RESULTS")
        
        print ("Fetching second " + str(count) + " results for \"" + query_cap + "\"...")
        response_cap = search.search(query_cap, count)
        print ("TOTAL: " + str(response_cap.total) + " RESULTS")
        
        result.append([str(query_cnt),str(query_cap),\
                       str(query[2]), str(query[3]),\
                       str(response_cnt.total),str(response_cap.total)])
            
        with open ('result_country_capital_fulllist_v2.txt', 'w', encoding="utf-8") as f:
            for line in result:
                f.write("\t".join(line)+"\n")  
        
        #for result in response.results:
        #    print("RESULT #" +str (i) + ": "+ (result._SearchResult__text if result._SearchResult__text is not None else "[None]") + "\n\n")
        #    i+=1
