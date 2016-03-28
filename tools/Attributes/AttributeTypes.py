'''
Module contains class definitions for various types of attibutes encountered during testing


Attributes are separated into two major sub categories: execution and data
    execution categories:     based on execution method involving
        subtypes:
            * write, write followed by read confirmation
            * computation based on repeated writes
            * logical comparison (including checking for equivalency based on read value)

    data categories:        based on the data type of the OPC parameter
        subtypes:
            * boolean - value is either true or false, written/read as 1 or 0
            * named set - value is based on a string<->integer mapping, written/read as integer
            * mode (special type of named set) - value is based on special MODE attribute;
                                                    written as MODE.TARGET, read as MODE.ACTUAL
            * command (special type of named set) - specifically for reading/writing EM and phase commands
            * status (special type of named set) - used to read .ST attributes, that is, OPC status values
            * string - value is a string, written/read as a string datatype
            * floating point - value is floating point
            * SP/PV (special type of floating point, boolean, or named set) - reads/writes depend on MODE

All attribute classes should be defined as a mixin of one or more parent
    classes from each execution and data categories. For example, closing a valve would be a combination
    of execution subtype <write> combined with data subtypes <boolean> <mode> and <SP/PV>.
'''

from AttributeBase import AttributeBase
from DataAttributes import Constant
from ExecutionAttributes import *

from tools.Utilities.Logger import LogTools
dlog = LogTools('AttributeTypes.log', 'AttributeTypes')
dlog.rootlog.warning('AttributeTypes initialized')

__author__ = 'ekopache'

if __name__ == "__main__":
    from tools.serverside.OPCclient import OPC_Connect

    connection = OPC_Connect()

    m1 = ModeAttribute('CV-1423', 'DC1/MODE')
    m2 = ModeAttribute('CV-3854', 'MODE')

    attrs = [m1, m2]

    for attr in attrs:
        attr.set_read_hook(connection.read)
        attr.set_write_hook(connection.write)
