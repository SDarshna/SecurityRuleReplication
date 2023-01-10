# SecurityRuleReplication
Replicating Security Rules from source tenant to destination tenant

#CLI
python3 security_rules_replicate.py -t1 T1-secret.yml -t2 T2-secret.yml -folder Shared -p pre

T1-secret.yml -> Source tenant's client secret
T2-secret.yml -> Destination tenant's client secret
-folder option -> (Shared, MU,RN) folder at which the security rules are present. Same folder is used to create the rules in the destinationn tenant.
-position option -> (pre,post) used to indicate the position where the security rule is created pre rules or post rules.
