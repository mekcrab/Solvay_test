'''
Example module to handle OpenOPC connections

Module must be run from windows python (C:\python.exe) on Cygwin installations.
OPC access is via an OPC gateway, run OPC gateway service run as DeltaVAdmin to avoid DCOM
permissions errors when interacting with a DeltaV system.

Includes dummy OPC client to allow for testing if OPC connections are not available. Module will
select real/dummy client based on import errors and bind the required class to the name OPC_connect

Use this construct to allow for real/dummy client autoselect:
from OPCclient import OPC_connect
'''

import time

from tools.Utilities.Logger import LogTools
dlog = LogTools('OPCclient.log', module='OPCclient')
dlog.rootlog.info('OPCclient module initialized.')

# aliased class names based on import sucess
OPC_AVAILABLE = False
try:
    import OpenOPC
    import Pyro.core
    OPC_AVAILABLE = True
except ImportError:
    dlog.rootlog.error("No OpenOPC package found, reverting to dummy client.")


class OPCclient(object):
    '''
    OPC read/write client connection
    '''
    def __init__(self, srv_name='OPC.DeltaV.1'):
        self.server_name = srv_name
        self.client = self.connect_local(srv_name)
        self.is_dummy = False  # marker to determine real client use at runtime

    @staticmethod
    def connect_local(svr_name, host='localhost'):
        '''
        Make connection to OPC server.
        :param svr_name: string name of OPC server
        :param host: hostname to search for OPC server, defaults to localhost
        :returns newly connected OPCclient
        '''
        opc_client = OpenOPC.open_client(host)
        opc_client.connect(svr_name)
        dlog.rootlog.info("Connected to OPC server %s on %s", svr_name, host)
        return opc_client

    def read(self, PV):
        '''Reads OPC value from the OPC path given by PV'''
        try:
            return self.client.read(str(PV))
        except OpenOPC.TimeoutError:
            dlog.rootlog.error("OPC timeout waiting for response on %s', PV")
            #try again - FOREVER!!!!! (actually until we hit the recursion limit)
            return self.read(PV)

    def write(self, PV, SP):
        '''Write value SP to OPC path specified by PV'''
        if type(SP) in [str, unicode]:
            SP = str(SP)
        else:
            SP = float(SP)
        result = self.client.write((str(PV), SP))
        dlog.rootlog.debug("OPC write: %s --> %s", PV, SP)
        return result


class OPCdummy(object):
    '''
    Dummy class for development without OPC communications
    '''
    def __init__(self, srv_name='OPC.DeltaV.1'):
        self.server_name = srv_name
        self.client = self.connect_local(srv_name)
        self.is_dummy = True  # marker to determine if using dummy class at runtime

        self.path_dict = dict()  # dictionary of paths for write loopback testing

    @staticmethod
    def connect_local(srv_name, host='dummy'):
        '''Dummy OPC connection'''
        dlog.rootlog.warning("Connected to dummy OPC client, attempted to get %s on %s", srv_name, host)
        return 'Dummy client connection'

    def read(self, path, dummy_val=-99):
        '''Dummy OPC read'''
        if path in self.path_dict:
            dummy_val = self.path_dict[path]
        dlog.rootlog.debug("Dummy read: %s <-- %s", path, dummy_val)
        return (dummy_val, 'Dummy', time.ctime(time.time()))

    def write(self, path, value):
        dlog.rootlog.debug("Dummy write: %s --> %s", path, value)
        self.path_dict[path] = value
        return 'Success'


# Determine OPC client type from OpenOPC availability, bind to OPC_Connect name
if OPC_AVAILABLE:
    OPC_Connect = OPCclient
else:
    OPC_Connect = OPCdummy


# trashy testing
if __name__ == "__main__":
    client = OPC_Connect('OPC.DeltaV.1')

    # example read
    # function returns (value, status, timestamp) on suceessful read
    print client.read('HS-4092/SP_D.CV')

    # example write
    # function returns 'success' or 'error'
    print client.write('HS-4092/MODE.TARGET', 16)  # AUTO
    print client.write('HS-4092/SP_D.CV', 1)
    print client.read('HS-4092/PV_D.CV')
