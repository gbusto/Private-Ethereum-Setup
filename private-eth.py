import subprocess
from subprocess import Popen, PIPE

import pexpect

import json
import os
import shutil

genesisJson = {
  "config": {
    "chainId": 12345,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "muirGlacierBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "arrowGlacierBlock": 0,
    "grayGlacierBlock": 0,
    "clique": {
      "period": 5,
      "epoch": 30000
    }
  },
  "difficulty": "1",
  "gasLimit": "800000000",
  "extradata": "0x00000000000000000000000000000000000000000000000000000000000000007df9a875a174b3bc565e6424a0050ebc1b2d1d820000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {
  }
}

def makeDirs(directories):
    for directory in directories:
        os.mkdir(directory)

def removeDirs(directories):
    for directory in directories:
        shutil.rmtree(directory)

def printCommand(cmd):
    print("[+] Running cmd '{}'".format(cmd))

def _executeCommand(cmd):
    return Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)

def initNodeDirs(directories, password):
    for directory in directories:
        cmd = "geth --datadir {} account new".format(directory)
        printCommand(cmd)
        proc = pexpect.spawn(cmd)
        while True:
            i = proc.expect([pexpect.EOF, pexpect.TIMEOUT, "Password", "Repeat password"])

            if i == 0:
                print("Program finished")
                break

            elif i == 1:
                print("Program timed out")
                break

            elif i == 2 or i == 3:
                proc.sendline(password)

            else:
                print("Unexpected state?")
                break

def gethInitGenesis(directories):
    for directory in directories:
        cmd = "geth init --datadir {} genesis.json".format(directory)
        printCommand(cmd)
        proc = _executeCommand(cmd)
        proc.wait()

def createBootNode():
    cmd = "bootnode -genkey boot.key"
    printCommand(cmd)
    proc = _executeCommand(cmd)
    proc.wait()

def startBootNode():
    cmd = "bootnode -nodekey boot.key -addr :30305"
    printCommand(cmd)
    proc = _executeCommand(cmd)
    return proc

def readFromFile(filename):
    data = ""
    with open(filename, "r") as f:
        data = f.read()

    return data.strip()

def parseBootnodeOutput(proc):
    if proc.poll() is None and len(proc.stdout.peek()) > 0:
        return proc.stdout.readline().decode("utf8").strip()

    return ""

def startNodes(dirsAddrsZipped, enodeString, passwordFilePath):
    # geth --datadir node1 --port 30306 --bootnodes enode://f7aba85ba369923bffd3438b4c8fde6b1f02b1c23ea0aac825ed7eac38e6230e5cadcf868e73b0e28710f4c9f685ca71a86a4911461637ae9ab2bd852939b77f@127.0.0.1:0?discport=30305  --networkid 123454321 --unlock 0xC1B2c0dFD381e6aC08f34816172d6343Decbb12b --password node1/password.txt --authrpc.port 8551
    basePort = 30306
    baseRpcPort = 8551

    procs = []

    for i in range(len(dirsAddrsZipped)):
        directory = dirsAddrsZipped[i][0]
        address = dirsAddrsZipped[i][1]
        
        cmd = "geth --datadir {} --port {} --bootnodes \"{}\" --networkid 12345 --unlock 0x{} --password {} --authrpc.port {}".format(
                    directory, basePort + i, enodeString, address, passwordFilePath, baseRpcPort + i
                )
        printCommand(cmd)

        proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        procs.append(proc)

    return procs

def getNodeAddresses(directories):
    addresses = []

    for directory in directories:
        keystoreFilename = findKeystorePathForNode(directory)
        jsonData = loadJsonFromFile(keystoreFilename)
        addresses.append(jsonData.get("address"))

    return addresses

def findKeystorePathForNode(directory):
    searchIn = os.path.join(directory, "keystore")
    for root, dirs, files in os.walk(searchIn):
        for f in files:
            return os.path.join(root, f)

    return ""

def createGenesisFile(genesisJson, addresses):
    for address in addresses:
        genesisJson["alloc"][address] = { "balance": "500000" }

    with open("genesis.json", "w") as f:
        json.dump(genesisJson, f)

def loadJsonFromFile(filename):
    with open(filename, "r") as f:
        return json.load(f)

    return json.loads("{}")

def removeFile(filename):
    if os.path.exists(filename):
        os.remove(filename)

def cleanup(directories, bootnodeProcess, nodeProcesses):
    removeDirs(directories)
    if bootnodeProcess:
        print("[+] Ending bootnode process")
        bootnodeProcess.kill()
    else:
        print("[-] Bootnode process already killed")

    for proc in nodeProcesses:
        print("[+] Ending a node process")
        proc.kill()

    removeFile("boot.key")
    removeFile("genesis.json")

if __name__ == "__main__":
    passwordFilename = "password.txt"
    bootnodeProcess = None
    nodeProcesses = []

    try:
        password = readFromFile(passwordFilename)

        directories = ["node1", "node2", "node3", "node4"]

        makeDirs(directories)

        initNodeDirs(directories, password)

        addresses = getNodeAddresses(directories)

        createGenesisFile(genesisJson, addresses)

        gethInitGenesis(directories)

        createBootNode()

        bootnodeProcess = startBootNode()

        enode = parseBootnodeOutput(bootnodeProcess)

        dirsAddrsZipped = list(zip(directories, addresses))
        nodeProcesses = startNodes(dirsAddrsZipped, enode, passwordFilename)
    except Exception as e:
        print(e)

    input("There are {} nodes listening now. Press Enter to stop all nodes...".format(len(nodeProcesses)))

    cleanup(directories, bootnodeProcess, nodeProcesses)
