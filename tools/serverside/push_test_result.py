#!/usr/bin/python


import requests
import sys

# define URL to push results
status_url = 'https://script.google.com/macros/s/AKfycbwnl_EirtDka43d14aTuQMh4cOx5ZWLydqFvh1_jib95r4_foo/exec'

headers = ['Interlock Specification', 'Test Name', 
	 'Last Run', 'Result', 'Comment']

def push_results(spec, test_name, last_run, result, comment):

	payload = dict(zip(headers, [spec, test_name, last_run, result, comment]))

	requests.post(status_url, data=payload)

if __name__ == "__main__":
	push_results(sys.argv[1:])
