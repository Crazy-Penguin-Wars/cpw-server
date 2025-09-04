import hashlib

def generate_signature(params, token):
    params = {k: v for k, v in params.items() if k != "sig"}
    sorted_items = sorted(params.items(), key=lambda x: x[0])

    base_string = "&".join(f"{k}={v}" for k, v in sorted_items)
    print(base_string)
    full_string = base_string + token + "PreCr4c4"

    return hashlib.md5(full_string.encode("utf-8")).hexdigest()