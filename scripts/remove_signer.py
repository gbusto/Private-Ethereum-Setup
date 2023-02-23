import pexpect
import sys
import os

if len(sys.argv) < 2:
    print("[+] Usage: python {} <0xaddress>")
    print("\tWhere <0xaddress> is the address of the node you would like to become a signer on the network")
    sys.exit(1)

address = sys.argv[1]

print("[+] Attemping to remove address {} as a signer on the private network".format(address))

gethPrompt = "> "

minerDir = "nodes/miners"
geth1 = os.path.join(minerDir, "mnode1", "geth.ipc")
geth2 = os.path.join(minerDir, "mnode2", "geth.ipc")
geth3 = os.path.join(minerDir, "mnode3", "geth.ipc")
geth4 = os.path.join(minerDir, "mnode4", "geth.ipc")

for geth in [geth1, geth2, geth3, geth4]:
    print("Connecting to geth IPC at {}".format(geth))

    proc = pexpect.spawn("geth attach {}".format(geth))
    proc.expect(gethPrompt)
    proc.sendline("clique.propose(\"{}\", false)".format(address))
    proc.expect(gethPrompt)
    proc.sendline("exit")
    proc.wait()

    print("Ended geth IPC session")

print("Done!")
