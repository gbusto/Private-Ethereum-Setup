# Overview
Following instructions [here](https://geth.ethereum.org/docs/fundamentals/private-network) in order to create a private Ethereum blockchain.

## Setup
Setup Python by running:
```
python3 -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt
```

Next, install geth. If you're on a Mac like me and have Homebrew installed, you can simply run `brew install geth`

After that, all that's left is to run `python private-eth.py`

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
* ChatGPT was actually pretty helpful in troubleshooting some of this stuff!


