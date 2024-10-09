# todo

## exception handling on authentication error

## more fine-tuned regex to treat custom tld's

### code

```py
# checks if a string is a legit URL, keeping the bad ones at bay
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp|wss)s?://'  # http://, https://, ftp://, wss://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,20}\.?|[A-Z0-9-]{2,}\.?)|'  # Domain name with wider range of TLDs
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or IPv6
        r'(?::\d+)?'  # Optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # Optional path
    return re.match(regex, url) is not None
```

## fix targets.txt encoding error if funny characters are in

- Problem: If we purely start for `targets.txt` the script treats the file as empty. It's because if we get unusual charcodes (they can happen) something breaks, but I haven't investigated how to circumvent it

### code

```py
    try:
        # Open the file with UTF-8 encoding
        with open(targets_file, 'r', encoding='utf-8') as file:
            targets = file.readlines()
            print(f"Content of {targets_file} (first 10 lines):")
            print("".join(targets[:10]))
```