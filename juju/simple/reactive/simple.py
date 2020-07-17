from charmhelpers.core.hookenv import (
    function_get,
    function_fail,
    function_set,
    status_set,
)
from charms.reactive import (
    clear_flag,
    set_flag,
    when,
    when_not,
)
import charms.sshproxy

from . import VDUHelper

vduHelper = VDUHelper.VDUHelper()


@when('sshproxy.configured')
@when_not('simple.installed')
def install_simple_proxy_charm():
    set_flag('simple.installed')
    status_set('active', 'Ready!')


@when('actions.touch')
def touch():

    vduHelper.beginBlock('Touch')
    try:
        vduHelper.touchFile('/tmp/touch1')
        vduHelper.testNetworking('8.8.4.4', 2)
        vduHelper.testNetworking('8.8.8.8', 2)
        vduHelper.touchFile('/tmp/touch2')

        fileName = function_get('filename')
        vduHelper.touchFile(fileName)

        message = vduHelper.endBlock()
        function_set( { 'outout': message } )
    except:
        message = vduHelper.endBlockInException()
        function_fail(message)
    finally:
        clear_flag('actions.touch')

    #err = ''
    #try:
        #filename = function_get('filename')
        #cmd = ['touch {}'.format(filename)]
        #result, err = charms.sshproxy._run(cmd)
    #except:
        #action_fail('command failed:' + err)
    #else:
        #function_set({'outout': result})
    #finally:
        #clear_flag('actions.touch')
