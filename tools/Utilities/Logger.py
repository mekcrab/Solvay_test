'''
Module contains base class for generating debug logs.

A new instance of a given log is created for each file.

Example calling:
==============================
from Utilities.Logger import LogTools
import config

dbug_log = LogTools(config.log_path + 'StateModel.log', config.log_level, 'StateModel')
dbug_log.rootlog.warning('StateModel initialized')

class MyClass(object):

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name',
        self.logger = dbug_log.MakeChild('MyClass', self.name) # identifies class and instance, will be added to dbug_log file

    def random_method(self, argument_1):
        self.logger.debug("Calling random method with " + str(argument_1)

        try:
            val = self.do_something()
        except, e:
            self.logger.error('Error in random_method as ' + e.error)
            val = None

        return val
==============================

'''

import logging
import os
import logging.handlers
import tools.config as config

class LogTools(object):
    def __init__(self, log_filename='test.log', module="ModuleName",
                    level=config.log_level,
                     maxSize=500000, maxCount=5,
                     streamLevel=config.log_level):
        '''Initialize Root Logger Instance'''
        self.fileformat = logging.Formatter('%(asctime)s ::%(levelname)8s:: %(name)15s:: %(message)s')
        self.handler = logging.handlers.RotatingFileHandler(
                                                            os.path.join(config.log_path, log_filename),
                                                            maxBytes=maxSize,
                                                            backupCount=maxCount,
                                                            )
        # initialize root logging instance
        self.modulename = module
        self.handler.setFormatter(self.fileformat)
        self.handler.setLevel(logLevel(level))
        self.rootlog = logging.getLogger(self.modulename)
        self.rootlog.addHandler(self.handler)
        if streamLevel:
            self.streamformat = logging.Formatter('%(levelname)s:: %(name)s:: %(message)s')
            self.shandler = logging.StreamHandler()
            self.shandler.setLevel(logLevel(streamLevel))
            self.shandler.setFormatter(self.streamformat)
            self.rootlog.addHandler(self.shandler)
            self.rootlog.propagate = 0

    def MakeChild(self, name=__name__, level_name=None):
        if not level_name:
            level_name = self.handler.level
        childlog = self.rootlog.getChild(name)
        childlog.setLevel(logLevel(level_name))
        return childlog

    def GetLogger(self, name, level_name='debug'):
        newlogger = logging.getLogger(name)
        newlogger.addHandler(self.handler)
        newlogger.addHandler(self.shandler)
        newlogger.setLevel(logLevel(level_name))
        newlogger.propagate = 0
        return newlogger

    def Output2Stdout(self, level='info'):
        '''Method changes log's output from rotating file handler to the standard out'''
        from sys import stdout
        self.rootlog.removeHandler(self.handler)
        self.rootlog.removeHandler(self.shandler)
        stdout_handler = logging.StreamHandler(stdout)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(name)s :: %(message)s'))
        stdout_handler.setLevel(logLevel(level))
        self.rootlog.addHandler(stdout_handler)


def logLevel(level):
    LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL,
              }
    loglvl = LEVELS.get(level, logging.NOTSET)
    return loglvl


class AuxLog(object):
    '''
    Helper class to log errors to a file for system troubleshooting and debugging
    '''

    def __init__(self, log_filename, level, module='Root'):
        ''' Initializes a ErrorLog instance'''
        LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL,
                  }

        if len(level) > 1:
            level_name = level
            self.level = LEVELS.get(level_name, logging.NOTSET)
        self.handler = logging.handlers.RotatingFileHandler(log_filename,
                                                            maxBytes=10000,
                                                            backupCount=5,
                                                            )

        self.handler.setLevel(self.level)
        self.formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s")
        self.handler.setFormatter(self.formatter)
        # logging.basicConfig(filename=log_filename,level=level, format ='%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s' )
        self.rootlogger = logging.getLogger(module)
        self.rootlogger.addHandler(self.handler)
        self.rootlogger.debug('Logger Initialized')
        pass

    def SetLogger(self, module):
        clog = logging.getLogger(module)
        clog.addHandler(self.handler)
        return clog