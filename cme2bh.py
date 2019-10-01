import sqlite3
import requests
import base64
import argparse

parser = argparse.ArgumentParser(description='Mark Bloodhound owned from CME database.')
parser.add_argument('-c','--creds',  default="neo4j:neo4j", help='Credentials for Neo4j (Default: neo4j:neo4j)')
parser.add_argument('-s','--server',  default="localhost:7474", help='Server for Neo4j (Default: localhost:7474)')
parser.add_argument('-f','--fqdn',  help='FQDN for the domain ("ad.domain.com")', required=True)
parser.add_argument('-n','--netbios', help='NetBIOS domain name ("ad")', required=True)
parser.add_argument('-p','--path',  default="~/.cme/cme.db", help='Path to CME DB file (Default: "~/.cme/cme.db")')

args = parser.parse_args()

auth = base64.b64encode(args.creds.encode())

#Run Cypher query in Neo4j
def runcypher(server,statement,auth):
    headers = { "Accept": "application/json; charset=UTF-8",
                "Content-Type": "application/json",
                "Authorization": auth }
    data = {"statements": [{'statement': statement}]}
    url = 'http://{}/db/data/transaction/commit'.format(server)
    r = requests.post(url=url,headers=headers,json=data)
    r.raise_for_status()

conn = sqlite3.connect(args.path)
c = conn.cursor()
# for host with a link in links database (host has an account with admin), mark as owned.
for host in c.execute('SELECT DISTINCT hostname FROM hosts WHERE id IN (SELECT hostid FROM links);'):
    statement = "MATCH (n) WHERE n.name =~ '(?i)^{}\..*$' SET n.owned=true RETURN n".format(host[0])
    runcypher(args.server,statement,auth)
    print('marked computer: {} owned'.format(host[0]))
# for username in credentials database, mark as owned.
for user in c.execute("SELECT DISTINCT username FROM credentials WHERE domain LIKE '{}';".format(args.netbios)):
    statement = "MATCH (n) WHERE n.name =~ '(?i)^{}@{}$' SET n.owned=true RETURN n".format(user[0],args.fqdn)
    runcypher(args.server,statement,auth)
    print('marked user: {} owned'.format(user[0]))

conn.close()
