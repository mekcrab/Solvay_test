'''Example module to handle OpenOPC connections

Module must be run from windows python (C:\python.exe)
OPC access is via OPC gateway, with OPC gateway service run as DeltaVAdmin

'''

# aliased class names based on import sucess
OPC_AVAILABLE = False
try:
    import OpenOPC
    OPC_AVAILABLE = True
except ImportError:
    print "No OpenOPC package found, revert to dummy client"

import time


class OPCconnect(object):
    '''
    OPC read/write client connection
    '''
    def __init__(self, srv_name='OPC.DeltaV.1'):
        self.client = self.connect_local(srv_name)

    def connect_local(self, svr_name, host='localhost'):
        opc_client = OpenOPC.open_client(host)
        opc_client.connect(svr_name)
        return opc_client

    def read(self, PV):
        return self.client.read(str(PV))

    def write(self, PV, SP):
        if type(SP) in [str, unicode]:
            SP = str(SP)
        else:
            SP = float(SP)
        print self.client.write((str(PV), SP))


class OPCdummy(object):
    '''
    Dummy class for development without OPC communications
    '''
    def __init__(self, srv_name='OPC.DeltaV.1'):
        self.client = self.connect_local(srv_name)

        self.path_dict = dict()  # dictionary of paths for write loopback testing

    def connect_local(self, srv_name, host='dummy'):
        return 'Dummy client connection'

    def read(self, path, dummy_val=-99):
        print "Dummy read: ", path
        if path in self.path_dict:
            dummy_val = self.path_dict[path]
        return (dummy_val, 'Dummy', time.ctime(time.time()))

    def write(self, path, value):
        print "Dummy write: ", path, ' as ', value
        self.path_dict[path] = value
        return 'Sucess'

# Determine OPC client type from OpenOPC availability
if OPC_AVAILABLE:
    OPC_Connect = OPCconnect
else:
    OPC_Connect = OPCdummy

# testing
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
