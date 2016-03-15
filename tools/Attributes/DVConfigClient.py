'''
Module contains client definitions to get DeltaV configuration data from a DVConfigServer
'''

import jsocket
import time

class DVConfigClient(jsocket.JsonClient):

    def __init__(self, address='127.0.0.1', port=5489):
        self.address = address
        self.port = port
        super(DVConfigClient, self).__init__()

        if address:
            self.address = address

        if port:
            self.port = port

    def disconnect(self):
        self.close()

    def set_server(self, address=None, port=None):
        if address:
            self.address = address
        if port:
            self.port = port

    def get_module_info(self, tag):
        '''
        Returns dictionary of information about DeltaV module
        :param tag: reference tag of module query
        :return: dictionary
        '''
        rpc_req = {
            "method": "get_module_info",
            "tag": tag
                   }


        self.send_obj(rpc_req)
        time.sleep(1)
        info = self.read_obj()
        print info


        return info


if __name__ == "__main__":
    dv_client = DVConfigClient()

    dv_client.connect()

    dv_client.get_module_info('CV-4148')

