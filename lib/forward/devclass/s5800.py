#!/usr/bin/env python
# coding:utf-8

"""
-----Introduction-----
[Core][forward] Device class for S5800.
Author: Cheung Kei-Chuen
"""
from forward.devclass.baseFenghuo import BASEFENGHUO
from forward.utils.forwardError import ForwardError
import re


class S5800(BASEFENGHUO):
    """This is a manufacturer of fenghuo, so it is integrated with BASEFENGHUO library.
    """

    def createVlan(self, vlan):
        """Create a Vlan.
        """
        info = {"status": False,
                "content": "",
                "errLog": ""}
        """Warning: that vlan should be checked
           by the 'self.isvlan(vlan) method
           before setting up the vlan"""
        # swith to config mode
        info = self._configMode()
        if not info["status"]:
            raise ForwardError(info["errLog"])
        try:
            # enter vlan
            self.shell.send("vlan {vlan}\n".format(vlan=vlan))
            # Host prompt is modified
            info["content"] = ""
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            self.getPrompt()
            if not re.search('vlan.*{vlan}'.format(vlan=vlan), self.prompt):
                raise ForwardError("Failed to enter vlan mode,command:vlan {vlan}".format(vlan=vlan))
            # exit vlan,switch to config mode
            self.shell.send("quit\n")
            # Host prompt is modified
            info["content"] = ""
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            # Get host prompt.
            self.getPrompt()
            # Failure to search for Vlan information.
            if re.search('vlan.*{vlan}'.format(vlan=vlan), self.prompt):
                raise ForwardError("Failed to exit vlan mode,command:quit")
            # Save the configuration.
            tmp = self._commit()
            if not tmp["status"]:
                raise ForwardError("The configuration command has been executed,\
                                    but the save configuration failed!")
            else:
                # Check is Vlan.
                tmp = self.isVlan(vlan)
                if not tmp["status"]:
                    # check vlan
                    raise ForwardError("Vlan has been set and has been saved, but the final\
                                        check found no configuration, so failed.\
                                        show vlan {vlan} verbose: [{content}]".format(vlan=vlan, content=tmp["errLog"]))
                else:
                    # create successed. exit config mode
                    info["status"] = True
        except Exception, e:
            info["errLog"] = str(e)
            info["status"] = False
        return info

    def isVlanInPort(self, vlan=None, port=None):
        """Check that the Vlan exists in the port.
        """
        info = {"status": False,
                "content": "",
                "errLog": ""}
        # Parameters check.
        if (vlan is None) or (port is None):
            raise ForwardError('Specify the `vlan` and `port` parameters')
        # Execute command.
        info = self.execute("show  run")
        if not info["status"]:
            raise ForwardError(info["errLog"])
        try:
            # Keyword search
            tmp = re.search("\![\r\n]+interface gigaethernet {port}[\s\S]*por\
t link-type (access|trunk)[\s\S]*port .* vlan .*{vlan}".format(vlan=vlan, port=port), info["content"])
            if tmp:
                # Vlan in the port, case 1
                if tmp.group(1) == "access":
                    raise ForwardError("Configuration found, but port link - type is 'access', Not a trunk")
                info["content"] = tmp.group().split("ABCDEFG")
                info["status"] = True
            else:
                # No exists'
                raise ForwardError('No exists')
        except Exception, e:
            info["errLog"] = str(e)
            info["status"] = False
        return info

    def createVlanInPort(self, port=None, vlan=None):
        """Create a vlan on the port.
        """
        # Prameters check.
        if (port is None) or (vlan is None):
            raise ForwardError('Specify the `port` parameter')
        info = {"status": False,
                "content": "",
                "errLog": ""}
        try:
            # switch to enable mode
            tmp = self.privilegeMode()
            if not tmp["status"]:
                raise ForwardError(tmp['errLog'])
            # else ,successed
            # switch to config mode
            tmp = self._configMode()
            if not tmp["status"]:
                raise ForwardError(tmp['errLog'])
            # else ,successed
            # switch to port mode
            info["content"] = ""
            self.shell.send("interface gigaethernet {port}\n".format(port=port))
            # Host prompt is modified
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            # release host prompt
            self.getPrompt()
            # Check the port mode
            if not re.search('config.*-ge', self.prompt):
                raise ForwardError('Switch to port mode is failed [%s]' % info["content"])
            # else successed.
            tmp = self.execute("port link-type trunk")
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            tmp = self.execute("port trunk allow-pass vlan {vlan}".format(vlan=vlan))
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            else:
                # Check the returned 'tmp['content']', which indicates failure if it contains' Failed '
                if re.search('%Failed', tmp["content"]):
                    raise ForwardError('Execute the command "port trunk allow-pass vlan" is failed ,\
                                        result is [%s] ' % tmp["content"])
                # else  successed
            tmp = self.execute("no shutdown")
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            # quit port mode
            self.shell.send("quit\n")
            info["content"] = ""
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            self.getPrompt()
            # save configuration
            tmp = self._commit()
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            # Verify that it is correct
            tmp = self.isVlanInPort(port=port, vlan=vlan)
            if not tmp["status"]:
                raise ForwardError("The configuration command has been executed,\
                                    but the check configuration does not exist! [%s]" % tmp["errLog"])
            else:
                # successed
                info["content"] = "successed"
                info["status"] = True
        except Exception, e:
            info["errLog"] = str(e)
            info["status"] = False
        return info

    def isTrunkInInterface(self, port=None, vlan=None):
        """Check the relationship between interface and turnk.
        """
        info = {"status": False,
                "content": "",
                "errLog": ""}
        # Prameters check.
        if (vlan is None) or (port is None):
            raise ForwardError('Specify the `vlan` and `port` parameters')
        while True:
            # Execute command.
            info = self.execute("show  run")
            if not info["status"]:
                raise ForwardError(info["errLog"])
            try:
                # Keyword search.
                tmp = re.search("interface eth-trunk {port}[\r\n]+ mode .*[\r\n]+ por\
    t .*[\r\n]+ port .* vlan .*{vlan}".format(port=port, vlan=vlan), info['content'])
                if tmp:
                    # Exists.
                    info["status"] = True
                    break
                elif re.search('Command is in use by', info["content"]):
                    # Rechecking...
                    continue
                else:
                    info["errLog"] = info['errLog']
                    break
            except Exception, e:
                info["errLog"] = str(e)
                info["status"] = False
                break
        return info

    def trunkOpenVlan(self, port=None, vlan=None):
        """Create a vlan on turnk.
        """
        info = {"status": False,
                "content": "",
                "errLog": ""}
        # Parameters check.
        if (vlan is None) or (port is None):
            raise ForwardError('Specify the `vlan` and `port` parameters')
        try:
            # switch to enable mode
            tmp = self.privilegeMode()
            if not tmp["status"]:
                raise ForwardError(tmp['errLog'])
            # else ,successed
            # switch to config mode
            tmp = self._configMode()
            if not tmp["status"]:
                raise ForwardError(tmp['errLog'])
            # else ,successed
            # switch to port mode
            self.shell.send("interface eth-trunk {port}\n".format(port=port))
            # Host prompt is modified
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            # release host prompt
            self.getPrompt()
            # Keyword search.
            if not re.search("config.*-eth.*-trunk.*-{port}".format(port=port), self.prompt):
                raise ForwardError('[trunkOpenVlan] Switch to port mode is failed [%s]' % info["content"])
            # Execute command.
            tmp = self.execute("port trunk allow-pass vlan {vlan}".format(vlan=vlan))
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            else:
                # Check the returned 'tmp['content']', which indicates failure if it contains' Failed '
                if re.search('%Failed', tmp["content"]):
                    raise ForwardError('Execute the command "port trunk allow-pass vlan" is failed ,\
                                        result is [%s] ' % tmp["content"])
            # quit port mode
            self.shell.send("quit\n")
            info["content"] = ""
            while not re.search(self.basePrompt, info['content'].split('\n')[-1]):
                info['content'] += self.shell.recv(1024)
            # save configuration
            self.getPrompt()
            # Save the configuration.
            tmp = self._commit()
            if not tmp["status"]:
                raise ForwardError(tmp["errLog"])
            # Verify that it is correct
            tmp = self.isTrunkInInterface(port=port, vlan=vlan)
            if not tmp["status"]:
                raise ForwardError("The configuration command has been executed,\
                                    but the check configuration does not exist! [%s]" % tmp['errLog'])
            info["status"] = True
        except Exception, e:
            info["errLog"] = str(e)
            info["status"] = False
        return info
