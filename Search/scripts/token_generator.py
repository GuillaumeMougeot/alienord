from typing import List
import argparse
from uuid import uuid4
from google.cloud.firestore import Client

def generate_user_tokens(number: int):
    user_tokens = []
    for _ in range(number):
        tokens = {}
        tokens['token'] = str(uuid4())
        tokens['valid'] = True
        user_tokens.append(tokens)
    
    return user_tokens

def upload_to_firestore(users: List[dict]):
    db = Client()
    [db.collection('users').add(user) for user in users]

def process_arguments():
    # Initialize the ArgumentParser
    parser = argparse.ArgumentParser(description = "Token generator",
                                     formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('-n',
                        nargs = '?',
                        dest = "n",
                        help = "Set number of tokens to generate",
                        type = int,
                        default = 10)
    
    # Parse the commandline
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = process_arguments()
    user_tokens = generate_user_tokens(args.n)
    upload_to_firestore(user_tokens)