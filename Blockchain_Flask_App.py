import hashlib
import json
from time import time
from uuid import uuid4
import sqlite3
import requests
from flask import Flask, jsonify, request

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()  # Set to store node addresses
        self.db_connection = sqlite3.connect('blockchain.db')
        self.create_tables()
        self.new_block(previous_hash='1', proof=100)  # Genesis block

    def create_tables(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chain (
                            index INTEGER PRIMARY KEY,
                            timestamp REAL,
                            proof INTEGER,
                            previous_hash TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS transaction (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sender TEXT,
                            recipient TEXT,
                            amount REAL,
                            block_index INTEGER,
                            FOREIGN KEY (block_index) REFERENCES chain (index)
                          )''')
        self.db_connection.commit()

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]) if self.chain else None,
        }
        self.current_transactions = []
        self.chain.append(block)
        cursor = self.db_connection.cursor()
        cursor.execute('''INSERT INTO chain (index, timestamp, proof, previous_hash)
                          VALUES (?, ?, ?, ?)''',
                       (block['index'], block['timestamp'], block['proof'], block['previous_hash']))
        self.db_connection.commit()
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"  # Simple proof condition (adjustable difficulty)

    def register_node(self, address):
        self.nodes.add(address)

    def resolve_conflicts(self):
        """
        Consensus algorithm: resolves conflicts by replacing the chain with the longest one in the network.
        """
        neighbors = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid.
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def save_transaction_to_db(self, sender, recipient, amount, block_index):
        cursor = self.db_connection.cursor()
        cursor.execute('''INSERT INTO transaction (sender, recipient, amount, block_index)
                          VALUES (?, ?, ?, ?)''',
                       (sender, recipient, amount, block_index))
        self.db_connection.commit()

    def load_chain_from_db(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''SELECT * FROM chain''')
        rows = cursor.fetchall()
        self.chain = []
        for row in rows:
            block = {
                'index': row[0],
                'timestamp': row[1],
                'proof': row[2],
                'previous_hash': row[3],
            }
            self.chain.append(block)

    def load_transactions_from_db(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''SELECT * FROM transaction''')
        rows = cursor.fetchall()
        self.current_transactions = []
        for row in rows:
            transaction = {
                'sender': row[1],
                'recipient': row[2],
                'amount': row[3],
            }
            self.current_transactions.append(transaction)

    def clear_db(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''DELETE FROM chain''')
        cursor.execute('''DELETE FROM transaction''')
        self.db_connection.commit()

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",  # "0" signifies a reward transaction (new block mined)
        recipient=node_identifier,
        amount=1,
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    blockchain.save_transaction_to_db(values['sender'], values['recipient'], values['amount'], index)

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

if __name__ == '__main__':
    blockchain.load_chain_from_db()
    blockchain.load_transactions_from_db()

    app.run(host='0.0.0.0', port=5000)

