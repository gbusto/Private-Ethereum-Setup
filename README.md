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
