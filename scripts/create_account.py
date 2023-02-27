import pexpect
import sys
import os

import re

if len(sys.argv) < 2:
    print("[+] Usage: python {} </path/to/node.ipc>")
    print("\tWhere </path/to/node.ipc> is the path to the node on which the account will be created via IPC")
    sys.exit(1)

node = sys.argv[1]

if not os.path.exists(node):
    print("[!] Node IPC at path {} not found!".format(node))
    sys.exit(-1)

print("[+] Attemping to create a new account on node at {}".format(node))

gethPrompt = "> "
password = "password"

proc = pexpect.spawn("geth attach {}".format(node))
proc.expect(gethPrompt)
proc.sendline("personal.newAccount()")
proc.expect("Passphrase:")
proc.sendline(password)
proc.expect("Repeat passphrase:")
proc.sendline(password)

_ = proc.readline()
accountAddressLine = proc.readline().decode("utf-8")

pattern = re.compile("(0x[a-fA-F0-9]{40})")
match = pattern.search(accountAddressLine)

proc.sendline("exit")

if match:
    address = accountAddressLine[match.start(): match.end()]
    print("New account address is {}".format(address))
else:
    print("[!] Unable to extra address from command line output. Connect to the node's IPC and call `personal.listAccounts` to see the new account address")

print("Done!")
