#!/usr/bin/env python
# coding:utf-8

"""
-----Introduction-----
[Core][forward] Device class for Depp.
Author: Cheung Kei-chuen
"""
from forward.devclass.baseSSHV2 import BASESSHV2
import re
import os


class BASEDEPP(BASESSHV2):
    """This is a manufacturer of depp, using the
    SSHV2 version of the protocol, so it is integrated with BASESSHV2 library.
    """
    def showSnmp(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "show run"
        prompt = {
            # Problems caused by special characters cannot be added with host prompt
            "success": "end",
            "error": "Unknown command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.findall("target-host address ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", result["content"])
            if tmp:
                njInfo["content"] = tmp
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showVersion(self):
        # Get software version of device.
        njInfo = {
            'status': False,
            'content': "",
            'errLog': ''
        }
        cmd = "show version"
        prompt = {
            "success": "Software Release[\s\S]+[\r\n]+\S+(#|>|\]|\$) ?$",
            "error": "Unknown command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            tmp = re.search("Software Release (.*)", result["content"], flags=re.IGNORECASE)
            if tmp:
                njInfo["content"] = tmp.group(1).strip()
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showRoute(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "show ip route"
        prompt = {
            "success": "Codes[\s\S]+[\r\n]+\S+(#|>|\]|\$) ?$",
            "error": "Unknown command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            for _interfaceInfo in result["content"].split("\r\n"):
                lineInfo = {
                    "net": "",
                    "mask": "",
                    "metric": "",
                    "via": [{"interface": "", "via": "", "type": ""}],
                }
                if re.search("\S?>\* [0-9]", _interfaceInfo):
                    tmp = re.search(">\* ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/([0-9]{1,2})", _interfaceInfo)
                    lineInfo["net"] = tmp.group(1)
                    lineInfo["mask"] = tmp.group(2)
                    via = re.search("via ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", _interfaceInfo)
                    if via:
                        lineInfo["via"][0]["via"] = via.group(1)
                    # Match the route table
                    tmp = re.search("([A-Z])>\*", _interfaceInfo)
                    if tmp:
                        _type = tmp.group(1)
                        if _type == "C":
                            _type = "connected"
                        elif _type == "S":
                            _type = "static"
                        elif _type == "R":
                            _type = "rip"
                        elif _type == "O":
                            _type = "ospf"
                        elif _type == "K":
                            _type = "kernel"
                        elif _type == "I":
                            _type = "isis"
                        elif _type == "B":
                            _type = "bgp"
                        elif _type == "G":
                            _type == "guard"
                        elif _type == "*":
                            _type = "fib"
                    else:
                        _type == "select"
                    lineInfo["via"][0]["type"] = _type
                    njInfo["content"].append(lineInfo)
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def showInterfaces(self):
        njInfo = {
            'status': False,
            'content': [],
            'errLog': ''
        }
        cmd = "show interface"
        prompt = {
            "success": "Virtual machine support[\s\S]+[\r\n]+\S+(#|>|\]|\$) ?$",
            "error": "Unknown command[\s\S]+",
        }
        result = self.command(cmd=cmd, prompt=prompt)
        if result["state"] == "success":
            interfacesFullInfo = re.split("[\r\n]{0,}Interface", result["content"])[1::]
            for _interfaceInfo in interfacesFullInfo:
                lineInfo = {"members": [],
                            "interfaceState": "",
                            "speed": "",
                            "type": "",
                            "inputRate": "",
                            "outputRate": "",
                            "crc": ""}
                # Get name of the interface.
                lineInfo['interfaceName'] = _interfaceInfo.split("\r")[0].strip(" ")
                # Get admin state of the interface and remove extra character.
                lineInfo['adminState'] = re.search("administration state is (.*),", _interfaceInfo).group(1)
                # Get state of line protocol of the interface and remove extra character.
                lineInfo['lineState'] = re.search("line.*is (.*)", _interfaceInfo).group(1).strip()
                # Get description of the interface.
                lineInfo['description'] = re.search("Description:(.*)", _interfaceInfo).group(1).strip()
                # Get MUT of the interface.
                tmp = re.search("MTU        : ([0-9]+)", _interfaceInfo)
                if tmp:
                    lineInfo["mtu"] = tmp.group(1)
                else:
                    lineInfo["mtu"] = ""
                # Get duplex of the interface.
                tmp = re.search("([a-z]+)\-duplex mode", _interfaceInfo)
                if tmp:
                    lineInfo["duplex"] = tmp.group(1)
                else:
                    lineInfo["duplex"] = ""
                # Get ip of the interface.
                tmp = re.search("ipv4 address primary: (.*)", _interfaceInfo)
                if tmp:
                    lineInfo["ip"] = tmp.group(1).split("/")[0]
                else:
                    lineInfo["ip"] = ""
                # Get mac of the interface.
                tmp = re.search("Hardware address is (.*)", _interfaceInfo)
                if tmp:
                    lineInfo["mac"] = tmp.group(1).strip()
                else:
                    lineInfo["mac"] = ""
                njInfo["content"].append(lineInfo)
            njInfo["status"] = True
        else:
            njInfo["errLog"] = result["errLog"]
        return njInfo

    def getMore(self, bufferData):
        """Automatically get more echo infos by sending a blank symbol
        """
        # if check buffer data has 'more' flag, at last line.
        # if re.search(self.moreFlag, bufferData.split('\n')[-1]):
        # can't used to \n and ' \r' ,because produce extra enter character
        self.shell.send(' ')
        # if re.search(self.moreFlag, bufferData.split('\n')[-1]):
        #    # can't used to \n and ' \r' ,because product enter character
        #   self.shell.send(' ')

    def updateIPObject(self, name, oldName, ip=None, vsysName="PublicSystem",
                       applyTime=None):
        # load module of suds.
        from suds.client import Client
        # create a ip or ip-range
        """
        parameter oldName : str type, originally name
        parameter name    : str type, any
        parameter ip      : str type, ip address, such as 10.0.0.1  or  10.0.0.100-10.0.0.200
        parameter url     : str type, webservice URL
        parameter username: str type, device's username,for authentiction
        parameter password: str typedevice's password,for authentication
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        url = "http://" + self.ip + "/func/web_main/wsdl/netaddr/netaddr.wsdl"
        # parameters check
        if re.search("\/", ip):
            # for 10.0.0.1/32
            ip = "{ip}/32".format(ip.split("/")[0])
        elif re.search("\-", ip):
            # The other one is 10.0.0.100-10.0.200,remove mask
            ip = re.sub("\/[0-9]+", "", ip)
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        try:
            client.service.modAddrObj(**{"oldname": oldName, "name": name, "ip": ip})
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result

    def deleteIPObject(self, name, vsysName="PublicSystem"):
        # load module of suds.
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/netaddr/netaddr.wsdl"
        # delete ip object
        """
        parameter name    : str type, any
        parameter ip      : str type, ip address, such as 10.0.0.1  or  10.0.0.100-10.0.0.200
        parameter url     : str type, webservice URL
        parameter username: str type, device's username,for authentiction
        parameter password: str typedevice's password,for authentication
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        try:
            client.service.delAddrObj(name=name)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result

    def createIPObject(self, name, ip=None, vsysName="PublicSystem",
                       applyTime=None):
        # load module of suds.
        from suds.client import Client
        # create a ip or ip-range
        """
        parameter name    : str type, any
        parameter ip      : str type, ip address, such as 10.0.0.1  or  10.0.0.100-10.0.0.200
        parameter url     : str type, webservice URL
        parameter username: str type, device's username,for authentiction
        parameter password: str typedevice's password,for authentication
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        url = "http://" + self.ip + "/func/web_main/wsdl/netaddr/netaddr.wsdl"
        # parameters check
        if re.search("\/", ip):
            # for 10.0.0.1/32
            ip = "{ip}/32".format(ip.split("/")[0])
        elif re.search("\-", ip):
            # The other one is 10.0.0.100-10.0.200,remove mask
            ip = re.sub("\/[0-9]+", "", ip)
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        try:
            client.service.addAddrObj(**{"name": name, "ip": ip})
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result

    def updateServiceObject(self, name, protocol=None, sRange=None,
                            dRange=None, vsysName="PublicSystem", applyTime=None):
        # load module of suds.
        from suds.client import Client
        """
        create a service object
        parameter name: str type, any
        parameter url : str type, webservice url
        parameter protocol : str type, tcp,udp or icmp
        parameter sRange   : str type, such as 90-91
        parameter dRange   : str type, suce as 100-101
        parameter vsysName : str type, default is PublicSystem
        parameter username : str type, device's username
        parameter password : str type, device's password
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        url = "http://" + self.ip + "/func/web_main/wsdl/netservice/netservice.wsdl"
        # parameters check.
        if protocol is None or sRange is None or dRange is None:
            raise IOError("Specify url,protocol,url,sRange and dRange parameters.")
        # Protocol code conversion
        if re.search("tcp", protocol, re.IGNORECASE):
            protocolNumber = 6
        elif re.search("udp", protocol, re.IGNORECASE):
            protocolNumber = 17
        elif re.search("icmp", protocol, re.IGNORECASE):
            protocolNumber = 1
        else:
            result["errLog"] = "Unkow protocol"
            return result
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
        p = {"name": name,
             "protocol": protocolNumber,
             "sourcePortRange": sRange,
             "destinationPortRange": dRange,
             "vsysName": vsysName}
        try:
            client.service.updateServerObject(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def deleteServiceObject(self, name, protocol=None, sRange=None,
                            dRange=None, vsysName="PublicSystem"):
        # load module of suds.
        from suds.client import Client
        """
        delete a service object
        parameter name: str type, any
        parameter url : str type, webservice url
        parameter protocol : str type, tcp,udp or icmp
        parameter sRange   : str type, such as 90-91
        parameter dRange   : str type, suce as 100-101
        parameter vsysName : str type, default is PublicSystem
        parameter username : str type, device's username
        parameter password : str type, device's password
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        url = "http://" + self.ip + "/func/web_main/wsdl/netservice/netservice.wsdl"
        # parameters check.
        if protocol is None or sRange is None or dRange is None:
            raise IOError("Specify url,protocol,url,sRange and dRange parameters.")
        # Protocol code conversion
        if re.search("tcp", protocol, re.IGNORECASE):
            protocolNumber = 6
        elif re.search("udp", protocol, re.IGNORECASE):
            protocolNumber = 17
        elif re.search("icmp", protocol, re.IGNORECASE):
            protocolNumber = 1
        else:
            result["errLog"] = "Unkow protocol"
            return result
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
        p = {"name": name,
             "protocol": protocolNumber,
             "sourcePortRange": sRange,
             "destinationPortRange": dRange,
             "vsysName": vsysName}
        try:
            client.service.deleteServerObject(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def createServiceObject(self, name, protocol=None, sRange=None,
                            dRange=None, vsysName="PublicSystem",
                            applyTime=None):
        # load module of suds.
        from suds.client import Client
        """
        create a service object
        parameter name: str type, any
        parameter url : str type, webservice url
        parameter protocol : str type, tcp,udp or icmp
        parameter sRange   : str type, such as 90-91
        parameter dRange   : str type, suce as 100-101
        parameter vsysName : str type, default is PublicSystem
        parameter username : str type, device's username
        parameter password : str type, device's password
        """
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        url = "http://" + self.ip + "/func/web_main/wsdl/netservice/netservice.wsdl"
        # parameters check.
        if protocol is None or sRange is None or dRange is None:
            raise IOError("Specify url,protocol,url,sRange and dRange parameters.")
        # Protocol code conversion
        if re.search("tcp", protocol, re.IGNORECASE):
            protocolNumber = 6
        elif re.search("udp", protocol, re.IGNORECASE):
            protocolNumber = 17
        elif re.search("icmp", protocol, re.IGNORECASE):
            protocolNumber = 1
        else:
            result["errLog"] = "Unkow protocol"
            return result
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
        p = {"name": name,
             "protocol": protocolNumber,
             "sourcePortRange": sRange,
             "destinationPortRange": dRange,
             "vsysName": vsysName}
        try:
            client.service.createServerObject(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def updateStaticNAT(self, name, interface=None, globalAddress=None, localAddress=None, enable="true",
                        vsysName="PublicSystem", applyTime=None):
        # notice： the parameter enable must be as string type.
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        if localAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the localAddress"
        if globalAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the globalAddress"
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "globalAddress": globalAddress,
             "enable": enable,
             "localAddress": localAddress}
        try:
            client.service.updateStaticNat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def deleteStaticNAT(self, name, interface=None, globalAddress=None, localAddress=None, enable="true",
                        vsysName="PublicSystem"):
        # notice： the parameter enable must be as string type.
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        if localAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the localAddress"
        if globalAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the globalAddress"
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "globalAddress": globalAddress,
             "enable": enable,
             "localAddress": localAddress}
        try:
            client.service.deleteStaticNat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def createStaticNAT(self, name, interface=None, globalAddress=None, localAddress=None, enable="true",
                        vsysName="PublicSystem", applyTime=None):
        # notice： the parameter enable must be as string type.
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        if localAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the localAddress"
        if globalAddress is None:
            result["errLog"] = "[Forward Error] Please specify the value of the globalAddress"
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "globalAddress": globalAddress,
             "enable": enable,
             "localAddress": localAddress}
        try:
            client.service.createStaticNat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def updateDNAT(self, name, interface=None, globalAddress="", localAddress=None, enable=True,
                   vsysName="PublicSystem", applyTime=None):
        return self.createDNAT(name, interface=interface, globalAddress=globalAddress, localAddress=localAddress,
                               enable=enable, vsysName=vsysName,
                               applyTime=applyTime)

    def deleteDNAT(self, name, interface=None, globalAddress="", localAddress=None, enable=True,
                   vsysName="PublicSystem"):
        result = {
            'status': False,
            'content': '',
            'errLog': ''}
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        if not re.search("\-", localAddress):
            result["errLog"] = "[Forward Error] Please specify the value of the localAddress as a address range."
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "globalAddress": globalAddress,
             "enable": enable,
             "localAddress": localAddress}
        try:
            client.service.deleteDnat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def createDNAT(self, name, interface=None, globalAddress="", localAddress=None, enable=True,
                   vsysName="SPublicystem", applyTime=None):
        result = {
            'status': False,
            'content': '',
            'errLog': ''}
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        if not re.search("\-", localAddress):
            result["errLog"] = "[Forward Error] Please specify the value of the localAddress as a address range."
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "globalAddress": globalAddress,
             "enable": enable,
             "localAddress": localAddress}
        try:
            client.service.createDnat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def updateSNAT(self, name, interface=None, addressPool="", enable=True, vsysName="PublicSystem",
                   applyTime=None):
        return self.createSNAT(name, interface=interface, addressPool=addressPool, enable=enable,
                               vsysName=vsysName, applyTime=applyTime)

    def deleteSNAT(self, name, interface=None, addressPool="", enable=True, vsysName="PublicSystem",
                   username=None, password=None):
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "addressPool": addressPool,
             "enable": enable}
        try:
            client.service.deleteSnat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def createSNAT(self, name, interface=None, addressPool="", enable=True, vsysName="PublicSystem",
                   applyTime=None):
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/nat/NatManager.wsdl"
        if interface is None:
            result["errLog"] = "[Forward Error] Please specify the value of the interface."
            return result
        try:
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {"vsysName": vsysName,
             "name": name,
             "interface": interface,
             "addressPool": addressPool,
             "enable": enable}
        try:
            client.service.createSnat(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,the configuration-name already exist,or vsysName not exist"
            else:
                result["errLog"] = "Unknow error."
        return result

    def updateSecurityPolicy(self, name, action=None,
                             sZone=None, dZone=None,
                             sIPType=None, sIPName=None,
                             dIPType=None, dIPName=None,
                             serviceType=None, serviceName=None,
                             vsysName="PublicSystem",
                             applyTime=None):
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/pf_policy/pf_policy/pf_policy.wsdl"
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        # default parameters
        # default sort 1
        position = 1
        # default should  be true
        enabled = "true"
        """
        Create security policy
        parameter name : str type, any
        parameter vsysName : str type, it must exist ,such as PublicSystem
        parameter position : int type, sort
        parameter enable   : str type, true/false
        parameter sZone    : str type, source security zone,must be exist
        parameter dZone    : str type, destination security zone,must be  exist
        parameter action   : str type, allow/deny
        parameter sIPType  : str type, source ip object name, single/group
        parameter sIPName  : str type, source ip object name ,must be exist
        parameter dIPType  : str type, destination ip object name, single/group
        parameter dIPName  : str type, destination ip object name ,must be exist
        parameter serviceType  : str type, service object,single/group
        parameter serviceName  : str type, service object name ,must be exist

        """
        # parameters check
        if action is None or (not action == "allow" and not action == "deny"):
            result["errLog"] = "[Forward Error] Please specify the value of the parameter action as allow/deny."
            return result
        if sZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the sZone."
            return result
        if dZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dZone."
            return result
        if sIPType is None or (not sIPType == "single" and not sIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPType,and value is single/group"
            return result
        if sIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPName,and value is single/group"
            return result
        if dIPType is None or (not dIPType == "single" and not dIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the dIPType,and value is single/group"
            return result
        if dIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dIPName."
            return result
        if serviceType is None or (not serviceType == "single" and not serviceType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the serviceType,and value is single/group"
            return result
        if serviceName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the serviceName."
            return result
        # Parameter transformation
        if sIPType == "single":
            sIPTypeCode = "0"
        else:
            sIPTypeCode = "1"
        if dIPType == "single":
            dIPTypeCode = "0"
        else:
            dIPTypeCode = "1"
        if serviceType == "single":
            serviceTypeCode = "0"
        else:
            serviceTypeCode = "1"
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {
            "name": name,
            "vsysName": vsysName,
            "position": position,
            "enabled": enabled,
            "action": action,
            "sourceSecurityZone": sZone,
            "destinationSecurityZone": dZone,
            "sourceIpObjects": [
                {
                    "type": sIPTypeCode,
                    "name": sIPName,
                }
            ],
            "destinationIpObjects": [
                {
                    "type": dIPTypeCode,
                    "name": dIPName,
                }
            ],
            "serverObjects": [
                {
                    "type": serviceTypeCode,
                    "name": serviceName
                }
            ]
        }
        try:
            client.service.updateSecurityPolicy(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result

    def deleteSecurityPolicy(self, name, action=None,
                             sZone=None, dZone=None,
                             sIPType=None, sIPName=None,
                             dIPType=None, dIPName=None,
                             serviceType=None, serviceName=None,
                             vsysName="PublicSystem"):
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/pf_policy/pf_policy/pf_policy.wsdl"
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        # default parameters
        # default sort 1
        position = 1
        # default should  be true
        enabled = "true"
        """
        Create security policy
        parameter name : str type, any
        parameter vsysName : str type, it must exist ,such as PublicSystem
        parameter position : int type, sort
        parameter enable   : str type, true/false
        parameter sZone    : str type, source security zone,must be exist
        parameter dZone    : str type, destination security zone,must be  exist
        parameter action   : str type, allow/deny
        parameter sIPType  : str type, source ip object name, single/group
        parameter sIPName  : str type, source ip object name ,must be exist
        parameter dIPType  : str type, destination ip object name, single/group
        parameter dIPName  : str type, destination ip object name ,must be exist
        parameter serviceType  : str type, service object,single/group
        parameter serviceName  : str type, service object name ,must be exist

        """
        # parameters check
        if action is None or (not action == "allow" and not action == "deny"):
            result["errLog"] = "[Forward Error] Please specify the value of the parameter action as allow/deny."
            return result
        if sZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the sZone."
            return result
        if dZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dZone."
            return result
        if sIPType is None or (not sIPType == "single" and not sIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPType,and value is single/group"
            return result
        if sIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPName,and value is single/group"
            return result
        if dIPType is None or (not dIPType == "single" and not dIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the dIPType,and value is single/group"
            return result
        if dIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dIPName."
            return result
        if serviceType is None or (not serviceType == "single" and not serviceType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the serviceType,and value is single/group"
            return result
        if serviceName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the serviceName."
            return result
        # Parameter transformation
        if sIPType == "single":
            sIPTypeCode = "0"
        else:
            sIPTypeCode = "1"
        if dIPType == "single":
            dIPTypeCode = "0"
        else:
            dIPTypeCode = "1"
        if serviceType == "single":
            serviceTypeCode = "0"
        else:
            serviceTypeCode = "1"
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {
            "name": name,
            "vsysName": vsysName,
            "position": position,
            "enabled": enabled,
            "action": action,
            "sourceSecurityZone": sZone,
            "destinationSecurityZone": dZone,
            "sourceIpObjects": [
                {
                    "type": sIPTypeCode,
                    "name": sIPName,
                }
            ],
            "destinationIpObjects": [
                {
                    "type": dIPTypeCode,
                    "name": dIPName,
                }
            ],
            "serverObjects": [
                {
                    "type": serviceTypeCode,
                    "name": serviceName
                }
            ]
        }
        try:
            client.service.deleteSecurityPolicy(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result

    def createSecurityPolicy(self, name, action=None,
                             sZone=None, dZone=None,
                             sIPType=None, sIPName=None,
                             dIPType=None, dIPName=None,
                             serviceType=None, serviceName=None,
                             vsysName="PublicSystem", applyTime=None):
        from suds.client import Client
        url = "http://" + self.ip + "/func/web_main/wsdl/pf_policy/pf_policy/pf_policy.wsdl"
        result = {
            'status': False,
            'content': '',
            'errLog': ''
        }
        # default parameters
        # default sort 1
        position = 1
        # default should  be true
        enabled = "true"
        """
        Create security policy
        parameter name : str type, any
        parameter vsysName : str type, it must exist ,such as PublicSystem
        parameter position : int type, sort
        parameter enable   : str type, true/false
        parameter sZone    : str type, source security zone,must be exist
        parameter dZone    : str type, destination security zone,must be  exist
        parameter action   : str type, allow/deny
        parameter sIPType  : str type, source ip object name, single/group
        parameter sIPName  : str type, source ip object name ,must be exist
        parameter dIPType  : str type, destination ip object name, single/group
        parameter dIPName  : str type, destination ip object name ,must be exist
        parameter serviceType  : str type, service object,single/group
        parameter serviceName  : str type, service object name ,must be exist

        """
        # parameters check
        if action is None or (not action == "allow" and not action == "deny"):
            result["errLog"] = "[Forward Error] Please specify the value of the parameter action as allow/deny."
            return result
        if sZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the sZone."
            return result
        if dZone is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dZone."
            return result
        if sIPType is None or (not sIPType == "single" and not sIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPType,and value is single/group"
            return result
        if sIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the sIPName,and value is single/group"
            return result
        if dIPType is None or (not dIPType == "single" and not dIPType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the dIPType,and value is single/group"
            return result
        if dIPName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the dIPName."
            return result
        if serviceType is None or (not serviceType == "single" and not serviceType == "group"):
            result["errLog"] = "[Forward Error] Please specify a parameter\
                                for the serviceType,and value is single/group"
            return result
        if serviceName is None:
            result["errLog"] = "[Forward Error] Please specify a parameter for the serviceName."
            return result
        # Parameter transformation
        if sIPType == "single":
            sIPTypeCode = "0"
        else:
            sIPTypeCode = "1"
        if dIPType == "single":
            dIPTypeCode = "0"
        else:
            dIPTypeCode = "1"
        if serviceType == "single":
            serviceTypeCode = "0"
        else:
            serviceTypeCode = "1"
        try:
            # connect to url
            client = Client(url, username=self.username, password=self.password)
        except Exception, e:
            result["errLog"] = "[Forward Error] Connected to {url} was\
                                failure, reason: {err}".format(err=str(e), url=url)
            return result
        p = {
            "name": name,
            "vsysName": vsysName,
            "position": position,
            "enabled": enabled,
            "action": action,
            "sourceSecurityZone": sZone,
            "destinationSecurityZone": dZone,
            "sourceIpObjects": [
                {
                    "type": sIPTypeCode,
                    "name": sIPName,
                }
            ],
            "destinationIpObjects": [
                {
                    "type": dIPTypeCode,
                    "name": dIPName,
                }
            ],
            "serverObjects": [
                {
                    "type": serviceTypeCode,
                    "name": serviceName
                }
            ]
        }
        try:
            client.service.createSecurityPolicy(p)
            result["status"] = True
        except Exception, e:
            num = e.message[0]
            if num == 401:
                result["errLog"] = "username or password invalid."
            elif num == 506:
                result["errLog"] = "Specify parameters error,or the configuration-name already exist."
            else:
                result["errLog"] = "Unknow error."
        return result
