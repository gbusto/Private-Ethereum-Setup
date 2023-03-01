# Overview
Following instructions [here](https://geth.ethereum.org/docs/fundamentals/private-network) in order to create a private Ethereum blockchain.

## Setup
Setup Python by running:
```
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt
```

Run the following commands to setup quorum:
```
brew install go
git clone https://github.com/Consensys/quorum.git
cd quorum
make all
```

Ensure that `$PATH` contained `geth` and `bootnode` from the previous step installing Quorum (you'll need to use a modified version of geth).

Next, install geth. If you're on a Mac like me and have Homebrew installed, you can simply run `brew install geth`

You can run the `private-eth-network.py` script manually, but there are two convenience scripts provided once you've run all other instructions above.

To run a Clique PoA network, run `./startCliqueNetwork.sh`.
To run a Quorum IBFT network, run `./startIBFTNetwork.sh`. NOTE: I still haven't fixed the IBFT "unauthorized address" error. Working on it now.

## Q&A
### What is the tmp/ directory?
This is the output from the `quorum-genesis-tool` command when following instructions on [this](https://docs.goquorum.consensys.net/tutorials/private-network/create-ibft-network) page. I have it in here for reference for the time being while I try to massage Quorum's IBFT consensus into my current script, and it might be useful for others as well. It will be removed in the future.

### What is the scripts/ directory?
These are some short scripts that I've used to test various things and automate some simple processes. I would ideally like to turn this whole script into a shell/terminal of some kind to be used as a local tool for quickly spinning up and managing nodes for testing things. The functionality provided by the scripts would then be available through the shell as a command to automate something within the test network.

### What consensus protocols are supported?
Quorum's IBFT and Clique PoA. You can also just run `python private-eth-network.py --help` to see the supported consensus protocols.

### How do I change the consensus protocol being used in this script?
Via the `--consensus` parameter for the `private-eth-network.py` script. See the `startIBFTNetwork.sh` or `startCliqueNetwork.sh` scripts for an example.

### How can I connect to a node locally?
From inside of this directory, you can connect to a node by using a command like this: `geth attach nodes/miners/mnode1/geth.ipc`

### How can I tell if a node is running or see its command output?
You can monitor a node through a terminal by running a command like this: `tail -f nodes/miners/mnode1/proc.out`

The `proc.out` file in each node directory will contain live output for each running node. If a node is not running, you'll see something like a `Fatal` error in the logs in `proc.out` indicating that the process stopped, using `ps aux | grep geth` to see if any geth processes are running, or try connecting to the local unix socket `geth attach nodes/miners/mnode1/proc.out` and see if the connection fails (if it fails, the process is likely not running).

### What should the directory structure look like for the nodes/ directory if things are setup properly?
You should see something similar to what's shown below:
```
nodes/miners/mnode1
nodes/miners/mnode1/geth
nodes/miners/mnode1/geth/nodes
nodes/miners/mnode1/geth/nodes/000001.log
nodes/miners/mnode1/geth/nodes/MANIFEST-000000
nodes/miners/mnode1/geth/nodes/LOCK
nodes/miners/mnode1/geth/nodes/CURRENT
nodes/miners/mnode1/geth/nodes/LOG
nodes/miners/mnode1/geth/LOCK
nodes/miners/mnode1/geth/chaindata
nodes/miners/mnode1/geth/chaindata/000003.log
nodes/miners/mnode1/geth/chaindata/000002.ldb
nodes/miners/mnode1/geth/chaindata/LOCK
nodes/miners/mnode1/geth/chaindata/ancient
nodes/miners/mnode1/geth/chaindata/ancient/receipts.cidx
nodes/miners/mnode1/geth/chaindata/ancient/bodies.0000.cdat
nodes/miners/mnode1/geth/chaindata/ancient/bodies.cidx
nodes/miners/mnode1/geth/chaindata/ancient/diffs.0000.rdat
nodes/miners/mnode1/geth/chaindata/ancient/receipts.0000.cdat
nodes/miners/mnode1/geth/chaindata/ancient/hashes.ridx
nodes/miners/mnode1/geth/chaindata/ancient/FLOCK
nodes/miners/mnode1/geth/chaindata/ancient/headers.0000.cdat
nodes/miners/mnode1/geth/chaindata/ancient/hashes.0000.rdat
nodes/miners/mnode1/geth/chaindata/ancient/diffs.ridx
nodes/miners/mnode1/geth/chaindata/ancient/headers.cidx
nodes/miners/mnode1/geth/chaindata/CURRENT
nodes/miners/mnode1/geth/chaindata/LOG
nodes/miners/mnode1/geth/chaindata/MANIFEST-000004
nodes/miners/mnode1/geth/chaindata/CURRENT.bak
nodes/miners/mnode1/geth/nodekey
nodes/miners/mnode1/geth/transactions.rlp
nodes/miners/mnode1/geth/lightchaindata
nodes/miners/mnode1/geth/lightchaindata/000001.log
nodes/miners/mnode1/geth/lightchaindata/MANIFEST-000000
nodes/miners/mnode1/geth/lightchaindata/LOCK
nodes/miners/mnode1/geth/lightchaindata/CURRENT
nodes/miners/mnode1/geth/lightchaindata/LOG
nodes/miners/mnode1/keystore
nodes/miners/mnode1/keystore/UTC--2023-03-01T16-59-52.671508000Z--63e6dc99e25b66727d3970ac89e6cd250a056def
nodes/miners/mnode1/geth.ipc
nodes/miners/mnode1/proc.out
// Many more nodes after this one
```

## Learnings
* [This](https://geth.ethereum.org/docs/fundamentals/private-network) tutorial for setting up a private PoA network is great. The two things I missed while glancing through this that prevented my network from working correctly are 1) not paying attention to the fact that `extradata` in the genesis file should contain the addresses of all initial signers of the network, and 2) not specifying the `--mine` parameter in the geth command to start the signing nodes. After this, blocks were being mined and I could actually submit transactions
* Commands and things I used to help diagnose what was happening in the network:
  * `eth.blockNumber` to see what the current block number was to see if anything was being mined
  * Reading the output files from nodes (`proc.out`) to see what was happening and get any insight I could
  * Checking `eth.pendingTransactions` to see if the transaction I just submitted was still pending
  * Checking account balances using `eth.getBalance("<0xABCD>")` to see if ETH had actually been sent
  * Checking `clique.proposals` to see what nodes had been proposed (will talk more about this below)
  * Checking `clique.status()` to see who the sealers are in the network (i.e. the signers)
* I learned that in PoA, a node can be either a signing node (also a miner) called a "sealer", or a member node that doesn't mine but acts as a relay
** A member node that is not a signer CAN NOT be a miner. Only signers can mine blocks because they have the authority and can prove it via signing
* If you see the error `unauthorized signer` in the `proc.out` or command output for a node after starting the network up, it likely means that no signers were specified in the `extradata` field of the `genesis.json` file
* You can connect to a node locally using IPC. If that connection fails, it's likely because that node has stopped for some reason and the process is no longer running
* Calling `miner.start()` when there are no nodes in the network doesn't work as expected. I believe you need to specify signers initially and set them up to mine out of the gate. Then on any new signers you want to add to the network, you can call `miner.start()` via the geth console on them to get them mining also. If you start your network off with signers and don't give them the `--mine` parameter, then calling `miner.start()` doesn't kick things off the right way. This is because you need a certain number of specified signers in the network, and the Clique protocol requires that signers rotate. The error I was seeing in this case was something like `err="signed recently, must wait for others"`.
* ~~ChatGPT was actually pretty helpful in troubleshooting some of this stuff!~~ ChatGPT was somewhat helpful in talking through these things. But it was wrong or unclear on some parts of the Clique PoA protocol.
* More learnings coming soon...