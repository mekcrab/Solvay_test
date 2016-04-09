'''
Module contains base class for generating debug logs.

A new instance of a given log is created for each file.

Example calling:
==============================
from Utilities.Logger import LogTools
import config

dbug_log = LogTools(config.log_path + 'StateModel.log', 'StateModel', level=config.log_level)
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
from sys import stdout

# logging output level dictionary, lowest --> highest levels.
# Lower levels include all higher levels (ex. 'debug' gives everything.
LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL,}


def get_log_level(level):
    '''Converts logging level sting names to logging module's level constant'''
    if level not in LEVELS.values():
        return LEVELS.get(level, logging.NOTSET)  # defaults to NOTSET (the lowest level possible)
    else:
        return level


class LogTools(object):
    def __init__(self,
                 log_filename='test.log',
                 module="ModuleName",
                 level=config.log_level,
                 maxSize=1000000,
                 maxCount=5,
                 streamLevel=None):

        '''Initialize root logger instance and create initial handlers'''

        # self.modulename is the string name of the log handled by this LogTools instance
        self.modulename = module

        # define log printing format
        self.fileformat = logging.Formatter('%(asctime)s ::%(levelname)8s:: %(name)15s::\t %(message)s')

        # create new log handler
        self.handler = logging.handlers.RotatingFileHandler(
                                                            os.path.join(config.log_path, log_filename),
                                                            maxBytes=maxSize,
                                                            backupCount=maxCount,
                                                            )
        # initialize root logging instance, set logging options
        self.handler.setFormatter(self.fileformat)
        self.handler.setLevel(get_log_level(level))

        # set the root log based on module name (log already created, needs to be fetched by python logging module)
        self.rootlog = self.get_root_log()

        # bind our handler specification to this log
        self.rootlog.addHandler(self.handler)

        # set initial level for this logs stream output - applies to console outputs or log pipes
        if streamLevel is None:
            streamLevel = level

        self.streamformat = logging.Formatter('%(levelname)s:: %(name)s:: %(message)s')
        self.shandler = logging.StreamHandler()
        self.shandler.setLevel(get_log_level(streamLevel))
        self.shandler.setFormatter(self.streamformat)
        self.rootlog.addHandler(self.shandler)
        self.rootlog.propagate = False

    def get_root_log(self):
        '''Returns a handle to the root log of this LogTools instance hierarchy'''
        return logging.getLogger(self.modulename)

    def MakeChild(self, name=None, level=None):
        '''Makes a child logger of the logger specified by name'''
        if name is None:
            name = self.rootlog.name

        # inherit logging level from rootlog RotatingFileHandler unspecified
        if level is None:
            level = self.handler.level
        else:
            level = get_log_level(level)

        childlog = self.rootlog.getChild(name)
        childlog.setLevel(level)
        return childlog

    def GetLogger(self, name, level_name='debug'):
        '''
        Wrapper method to combine logger outputs to the
        logger referenced by name. Sets logging level if passed optional argument level_name
        '''
        newlogger = logging.getLogger(name)
        newlogger.addHandler(self.handler)
        newlogger.addHandler(self.shandler)
        newlogger.setLevel(get_log_level(level_name))
        newlogger.propagate = False
        return newlogger

    def Output2Stdout(self, level_name='info', stop_log_file=False):
        '''
        Method changes log's output from rotating file handler to the standard out
        :param level_name: logging level to push to stdout
        :param stop_log_file: flag to stop logging to original output file
        '''
        # create new handler for console output
        stdout_handler = logging.StreamHandler(stdout)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s :: %(name)s :: %(message)s'))
        stdout_handler.setLevel(get_log_level(level_name))
        # add handler to rootlog
        self.rootlog.addHandler(stdout_handler)
        # inform user of logging level change
        self.rootlog.info("Logging output directed to console")
        # disable original log file handler if flag set
        if stop_log_file:
            self.rootlog.warning("Logging output to file disabled, all output directed to console")
            self.rootlog.removeHandler(self.handler)
            self.rootlog.removeHandler(self.shandler)


class AuxLog(object):
    '''
    Helper class to log errors to a new file for (hopefully) easier troubleshooting and debugging
    '''

    def __init__(self, log_filename, level, module='Root'):
        ''' Initializes a new auxiliary log instance.'''
        # create new log file handler
        self.handler = logging.handlers.RotatingFileHandler(
                                                    log_filename,
                                                    maxBytes=10000,
                                                    backupCount=5,
                                                    )
        # set handler options
        if level not in LEVELS.values():
            self.level = LEVELS.get(level, logging.NOTSET)
        self.handler.setLevel(self.level)

        self.formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s")
        self.handler.setFormatter(self.formatter)

        # bind the log defined by <module> to the new handler
        self.rootlogger = logging.getLogger(module)
        self.rootlogger.addHandler(self.handler)
        self.rootlogger.info('New auxillary log initialized.')

    def SetLogger(self, log_name):
        '''
        Adds the output of log specified by string <log name> to the auxillary log
        :param module:
        :return: logger instance with added handler to output to AuxLog file
        '''
        clog = logging.getLogger(log_name)
        clog.addHandler(self.handler)
        return clog