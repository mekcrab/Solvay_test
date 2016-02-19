'''Example module to handle OpenOPC connections

Module must be run from windows python (C:\python.exe)
OPC access is via OPC gateway, with OPC gateway service run as DeltaVAdmin

'''

import OpenOPC

def connect_local(svr_name):

	opc_client = OpenOPC.open_client('localhost')
	opc_client.connect(svr_name)
	return opc_client

if __name__ == "__main__":

	client = connect_local('OPC.DeltaV.1')

	#example read
	# function returns (value, status, timestamp) on suceessful read
	print client.read('HS-4092/SP_D.CV')

	# example write
	# function returns 'success' or 'error'
	print client.write(('HS-4092/MODE.TARGET', 16)) # AUTO
	print client.write(('HS-4092/SP_D.CV', 1))
	print client.read('HS-4092/PV_D.CV')
