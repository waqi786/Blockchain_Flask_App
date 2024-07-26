# Blockchain_Flask_App

This repository contains a simple blockchain implementation using Flask and SQLite. It allows for basic blockchain functionalities such as adding new transactions, mining new blocks, registering nodes, and reaching a consensus among nodes.


**Features:**

1. Blockchain and Transaction Management: Basic blockchain structure with transaction handling.
2. Proof of Work: Simple proof of work algorithm to mine new blocks.
3. Consensus Algorithm: Resolve conflicts by replacing the chain with the longest one in the network.
4. Persistent Storage: Uses SQLite database to store the blockchain and transactions.
5. Flask API: RESTful API endpoints to interact with the blockchain.

**Requirements:**

Flask
SQLite3
Requests

**Installation:**

1. Clone the repository:
      git clone https://github.com/yourusername/Blockchain_Flask_App.git

2. Navigate to the project directory:
      cd Blockchain_Flask_App
3. Install the required packages:
      pip install flask requests

**Usage:**

1. Run the Flask application:
      python blockchain_app.py
2. Use the following endpoints to interact with the blockchain:
   
**API Endpoints**

Mine a new block

    GET /mine
    
Create a new transaction
    
    POST /transactions/new
    {
      "sender": "address",
      "recipient": "address",
      "amount": 0
    }
    
Get the full blockchain
    
    GET /chain
    
Register new nodes
    
    POST /nodes/register
    {
      "nodes": ["http://node_address"]
    }
    
Resolve conflicts
    
    GET /nodes/resolve


**Example:**

response = requests.get('http://127.0.0.1:5000/mine')
print(response.json())


Author
Waqar Ali

Uploaded Date
July 25, 2024
