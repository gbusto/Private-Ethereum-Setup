import pexpect
import sys
import os
import argparse
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware

parser = argparse.ArgumentParser(description='Deploy a contract to the private network')
parser.add_argument('--ipc', dest='geth_ipc', help='Path to the local node\'s geth IPC socket', required=True)
parser.add_argument('--contract-json', dest='contract_artifacts', help='Path to the compiled contract artifacts JSON file', required=True)
parser.add_argument('--deploy-from', dest='deploying_address', help='Address of the account that will deploy the contract', required=True)
parser.add_argument('--password-file', dest='password_file', help='Path to the password file for the deploying account', required=True)
args = parser.parse_args()

gethIpc = args.geth_ipc
contractArtifacts = args.contract_artifacts
deployingAddress = args.deploying_address
passwordFile = args.password_file

deployingAddress = Web3.toChecksumAddress(deployingAddress)

print("[+] Attemping to deploy contract at {} from address {} with password file {}".format(contractArtifacts, deployingAddress, passwordFile))

if not os.path.exists(gethIpc):
    print("[-] Could not find geth IPC at {}".format(gethIpc))
    sys.exit(1)

if not os.path.exists(contractArtifacts):
    print("[-] Could not find contract abi at {}".format(contractArtifacts))
    sys.exit(1)

if not os.path.exists(passwordFile):
    print("[-] Could not find password file at {}".format(passwordFile))
    sys.exit(1)

# Inject geth_poa_middleware so that we can properly send transactions over a PoA network
w3 = Web3(Web3.IPCProvider(gethIpc))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contractArtifactsJson = json.load(open(contractArtifacts, 'r'))
password = open(passwordFile, 'r').read().strip()

abi = contractArtifactsJson['abi']
bytecode = contractArtifactsJson['data']['bytecode']['object']

result = w3.geth.personal.unlock_account(deployingAddress, password)
if not result:
    print("[-] Could not unlock account {}".format(deployingAddress))
    sys.exit(1)

contract = w3.eth.contract(abi=abi, bytecode=bytecode)
contractTxn = contract.constructor().buildTransaction({
    'from': deployingAddress,
    'chainId': 12345,
})

txnHash = w3.eth.send_transaction(contractTxn)
txnReceipt = w3.eth.wait_for_transaction_receipt(txnHash)

print("[+] Contract deployed at address {}".format(txnReceipt.contractAddress))

# targetAddress = Web3.toChecksumAddress("0xe71995019dcb6ce92e799b15fcadea5e89bf6108")

# contract = w3.eth.contract(address=txnReceipt.contractAddress, abi=abi)
# txnHash = contract.functions.sendMessage("Hello, world!", targetAddress).transact({'from': deployingAddress})
# txnReceipt = w3.eth.wait_for_transaction_receipt(txnHash)

# messages = contract.functions.getMessages(targetAddress).call({'from': deployingAddress})