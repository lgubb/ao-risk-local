import re

def classify_piece(text: str) -> str:
    if re.search(r'cctp|cahier des clauses techniques', text, re.IGNORECASE):
        return 'CCTP'
    elif re.search(r'ccap|cahier des clauses administratives', text, re.IGNORECASE):
        return 'CCAP'
    elif re.search(r'reglement de consultation|rc', text, re.IGNORECASE):
        return 'RC'
    elif re.search(r'acte d\'engagement|ae', text, re.IGNORECASE):
        return 'AE'
    return 'UNKNOWN'
