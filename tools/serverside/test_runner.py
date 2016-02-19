#!/usr/bin/python

import glob
import time
import subprocess 
import os
import commands
import datetime

from push_test_result import push_results

# see where we are 
print os.path.abspath(__file__)

def cygpath(path_string):
	return commands.getoutput("cygpath -aw " + path_string)


path = '/home/TESTMONKEY/autotest/'
test_folder = 'pending/'

# Identify pending tests
test_queue = [x.split('/')[-1] for x in glob.iglob(path+test_folder+'*.csv')]
# ['I-44-6_PI-4039.csv', 'I-45-1_PIC-4055.csv']

print 'Running', len(test_queue), 'tests...' 

# Run all tests
for test_file in test_queue:
	# reset error comments
	err = ''

	# define test name
	base = test_file.split('.')[0]

	# create log file
	log_file = path + base + '.log'
	os.system("touch " + log_file)

	# create testbench command
	args = [	path + 'TestBench',
			cygpath(path + test_folder + test_file),
			'-L:' + cygpath(log_file),
			'-S', '-E', '-V', '-O'
			]	

	starttime = time.time()
	return_code = -999

	try:
		p = subprocess.Popen(args, cwd = path)
		p.communicate()
		return_code = p.wait()
	except OSError as err:
		print "Scipt OS error:", 
		print err
		return_code = -1
	
	runtime = time.time()-starttime # runtime in seconds
	
	# check log file for test failure conditions
	with open(log_file, 'rb') as f:
		for line in f.readlines():
			if "Step " + str(return_code) in line:
				err += ':: '+line
				return_code = -2
			elif "Invalid MiMiC" in line:
				err += ':: '+line
				return_code = -3

	# move test to proper folder, based on results
	result = None
	if return_code is 0:
		result = 'PASS'
		print base, result, '\t ({:2.1f} s)'.format(runtime)
		os.rename(path+test_folder+test_file, path+'/passed/'+test_file)
		os.rename(log_file, path+'/passed/'+base+'.log')
		err += "Run time: {:3.1f}s".format(runtime)
	else:
		result = 'FAIL'
		print base, result, '\t ({:2.1f} s)'.format(runtime)
		print '\treturn code:', return_code
		err = 'Return code:'+ str(return_code) + ' ({:2.2f}s)'.format(runtime)
		os.rename(path+test_folder+test_file, path+'/failed/'+test_file)
		os.rename(log_file, path+'/failed/'+base+'.log')

	push_results(base.split('_')[0], base, datetime.datetime.now().ctime(), result, err)


