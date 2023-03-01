from subprocess import Popen, PIPE

import pexpect

import json
import os
import sys
import shutil

import rlp

import argparse

config = {
    "period": 5,
    "epoch": 30000,
    "chainId": 12345,
    "passwordFile": "password.txt",
    "initialBalance": "10000000000000000000",
    "baseNodePort": 30306,
    "baseRpcPort": 8551,
    "nodesDir": "nodes",
    "minerNodes": ["mnode1", "mnode2", "mnode3", "mnode4", "mnode5", "mnode6", "mnode7", "mnode8"],
    "memberNodes": ["node1", "node2", "node3", "node4"],
    "minerNodesRoot": os.path.join("nodes", "miners"),
    "memberNodesRoot": os.path.join("nodes", "members"),
}

genesisJsonClique = {
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
      "period": config.get("period"),
      "epoch": config.get("epoch"),
    }
  },
  "difficulty": "1",
  "gasLimit": "800000000",
  "extradata": "",
  "alloc": {
  }
}

genesisJsonIBFT = {
  "nonce": "0x0",
  "timestamp": "0x0",
  # In the Clique genesis file, this is called "extradata" (all lowercase)
  "extraData": "",
  "gasLimit": "0xFFFFFF",
  "gasUsed": "0x0",
  "number": "0x0",
  "difficulty": "0x1",
  "coinbase": "0x0000000000000000000000000000000000000000",
  # Fixed magic number for Istanbul block identification
  # https://github.com/ethereum/EIPs/issues/650
  "mixHash": "0x63746963616c2062797a616e74696e65206661756c7420746f6c6572616e6365",
  "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "config": {
    "chainId": config.get("chainId"),
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip150Hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "muirglacierblock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "isQuorum": True,
    "maxCodeSizeConfig": [
      {
        "block": 0,
        "size": 64
      }
    ],
    "txnSizeLimit": 64,
    "ibft": {
      "policy": 0,
      "epoch": config.get("epoch"),
      "ceil2Nby3Block": 0,
      "blockperiodseconds": config.get("period")
    }
  },
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

def initNodeDirs(gethBin, directories, password):
    for directory in directories:
        cmd = "{} --datadir {} account new".format(gethBin, directory)
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

def gethInitGenesis(gethBin, directories):
    for directory in directories:
        cmd = "{} init --datadir {} genesis.json".format(gethBin, directory)
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

def startNodes(gethBin, consensus, dirsAddrsZipped, enodeString, passwordFilePath):
    if consensus == "ibft":
        _func = startNodesIBFT
    else:
        _func = startNodesClique

    return _func(gethBin, dirsAddrsZipped, enodeString, passwordFilePath)

def startNodesClique(gethBin, dirsAddrsZipped, enodeString, passwordFilePath):
    # geth --datadir node1 --port 30306 --bootnodes enode://f7aba85ba369923bffd3438b4c8fde6b1f02b1c23ea0aac825ed7eac38e6230e5cadcf868e73b0e28710f4c9f685ca71a86a4911461637ae9ab2bd852939b77f@127.0.0.1:0?discport=30305  --networkid 123454321 --unlock 0xC1B2c0dFD381e6aC08f34816172d6343Decbb12b --password node1/password.txt --authrpc.port 8551
    basePort = 30306
    baseRpcPort = 9550
    baseHttpPort = 8545

    procs = []

    for i in range(len(dirsAddrsZipped)):
        directory = dirsAddrsZipped[i][0]
        address = dirsAddrsZipped[i][1]

        if "miner" in directory:
            cmd = "{} --datadir {} --port {} --bootnodes \"{}\" --networkid 12345 --unlock 0x{} --password {} --authrpc.port {} --mine --allow-insecure-unlock".format(
                        gethBin, directory, basePort + i, enodeString, address, passwordFilePath, baseRpcPort
                    )
            baseRpcPort += 1
        else:
            cmd = "{} --datadir {} --port {} --bootnodes \"{}\" --networkid 12345 --authrpc.port {} --http --http.addr 127.0.0.1 --http.port {} --allow-insecure-unlock".format(
                        gethBin, directory, basePort + i, enodeString, baseRpcPort + i, baseHttpPort
                    )
            baseHttpPort += 1

        printCommand(cmd)

        if " --allow-insecure-unlock" in cmd:
            print("[-] WARNING: Using --allow-insecure-unlock which is insecure")

        filename = os.path.join(directory, "proc.out")
        with open(filename, "w") as f:
            proc = Popen(cmd, shell=True, stdout=f, stderr=f)
            procs.append(proc)

    return procs

def startNodesIBFT(gethBin, dirsAddrsZipped, enodeString, passwordFilePath):
    basePort = 30306
    baseRpcPort = 9550
    baseHttpPort = 8545

    procs = []

    for i in range(len(dirsAddrsZipped)):
        directory = dirsAddrsZipped[i][0]
        address = dirsAddrsZipped[i][1]

        if "miner" in directory:
            cmd = "{} --datadir {} --syncmode full --port {} --bootnodes \"{}\" --networkid 12345 --unlock 0x{} --password {} --mine --miner.threads 1 --miner.gasprice 0 --emitcheckpoints --allow-insecure-unlock".format(
                        gethBin, directory, basePort + i, enodeString, address, passwordFilePath
                    )
            baseRpcPort += 1
        else:
            cmd = "{} --datadir {} --syncmode full --port {} --bootnodes \"{}\" --networkid 12345 --http --http.addr 127.0.0.1 --http.port {} --allow-insecure-unlock".format(
                        gethBin, directory, basePort + i, enodeString, baseHttpPort
                    )
            baseHttpPort += 1

        printCommand(cmd)

        if " --allow-insecure-unlock" in cmd:
            print("[-] WARNING: Using --allow-insecure-unlock which is insecure")

        filename = os.path.join(directory, "proc.out")
        with open(filename, "w") as f:
            proc = Popen(cmd, shell=True, stdout=f, stderr=f)
            procs.append(proc)

    return procs

def getNodeAddresses(directories):
    minerAddresses = []
    memberAddresses = []

    for directory in directories:
        keystoreFilename = findKeystorePathForNode(directory)
        jsonData = loadJsonFromFile(keystoreFilename)
        if "member" in directory:
            memberAddresses.append(jsonData.get("address"))
        else:
            minerAddresses.append(jsonData.get("address"))

    return (minerAddresses, memberAddresses)

def findKeystorePathForNode(directory):
    searchIn = os.path.join(directory, "keystore")
    for root, dirs, files in os.walk(searchIn):
        for f in files:
            return os.path.join(root, f)

    return ""

def createExtraDataClique(addresses):
    extraData = "0x" + "00" * 32

    for address in addresses:
        extraData += address
    
    extraData += "00" * 65

    return extraData
    
def createExtraDataIBFT(addresses):
    old_string = "f841"
    new_string = "b841"

    for i in range(0, 65):
        old_string = old_string + "80"
        new_string = new_string + "00"

    vanity = "0x0000000000000000000000000000000000000000000000000000000000000000"

    seal = []

    for i in range(0, 65):
        seal.append(0x00)

    committed_seal = []

    validators = []

    for address in addresses:
        validators.append(int("0x" + address, 16))

    extra_data = vanity + rlp.encode([validators, seal, committed_seal]).hex()

    extra_data = extra_data.replace(old_string,  new_string)

    return extra_data

def createGenesisFile(genesisJson, minerAddresses, memberAddresses):
    for address in minerAddresses + memberAddresses:
        genesisJson["alloc"][address] = { "balance": config.get("initialBalance") }

    # Unclear if this is significant yet, but in the clique genesis, its "extradata" (not camelcase)
    # In the IBFT genesis, its "extraData" (camelcase)

    if genesisJson.get("config").get("ibft", None) is not None:
        extraData = createExtraDataIBFT(minerAddresses)
        genesisJson["extraData"] = extraData
    else:
        extraData = createExtraDataClique(minerAddresses)
        genesisJson["extradata"] = extraData

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
    parser = argparse.ArgumentParser(description="Start a private Ethereum network using either Clique PoA or Quorum IBFT")
    parser.add_argument("--consensus", help="The consensus algorithm to use. Either 'clique' or 'ibft'", choices=["ibft", "clique"], required=True)
    parser.add_argument("--geth-bin", help="The path to the desired geth binary", required=True)
    args = parser.parse_args()

    consensus = args.consensus
    gethBin = args.geth_bin

    if not os.path.exists(gethBin):
        print("[-] The specified geth binary does not exist")
        sys.exit(1)

    print("[+] Consensus is {}".format(consensus))
    print("[+] Using geth binary at {}".format(gethBin))

    passwordFilename = config.get("passwordFile")
    bootnodeProcess = None
    nodeProcesses = []

    try:
        password = readFromFile(passwordFilename)

        makeDirs([config.get("nodesDir"), config.get("minerNodesRoot"), config.get("memberNodesRoot")])
        minerNodesDirs = [os.path.join(config.get("minerNodesRoot"), x) for x in config.get("minerNodes")]
        memberNodesDirs = [os.path.join(config.get("memberNodesRoot"), x) for x in config.get("memberNodes")]
        combinedDirs = minerNodesDirs + memberNodesDirs
        makeDirs(combinedDirs)

        initNodeDirs(gethBin, combinedDirs, password)

        minerAddresses, memberAddresses = getNodeAddresses(combinedDirs)

        if consensus == "ibft":
            print("[+] Using IBFT genesis JSON")
            genesisJson = genesisJsonIBFT
        else:
            print("[+] Using Clique genesis JSON")
            genesisJson = genesisJsonClique
            
        createGenesisFile(genesisJson, minerAddresses, memberAddresses)

        gethInitGenesis(gethBin, combinedDirs)

        createBootNode()

        bootnodeProcess = startBootNode()

        enode = parseBootnodeOutput(bootnodeProcess)

        addresses = minerAddresses + memberAddresses

        dirsAddrsZipped = list(zip(combinedDirs, addresses))
        nodeProcesses = startNodes(gethBin, consensus, dirsAddrsZipped, enode, passwordFilename)
    except Exception as e:
        print("ERROR!")
        print(e)

    input("There are {} nodes listening now. Press Enter to stop all nodes...".format(len(nodeProcesses)))

    cleanup(["nodes"], bootnodeProcess, nodeProcesses)
