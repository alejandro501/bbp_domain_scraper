# todo

## exception handling on authentication error

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

# binary prereq

## make cookie - and other args - as a flag from command line or outside cfg file
