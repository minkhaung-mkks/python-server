import re

def europenize(input_string):
    # Replace periods that are directly before commas, and then replace commas with periods
    input_string = re.sub(r'\.(?=,)', '', input_string)
    return input_string.replace(',', '.')

print(europenize("10.200,30"))  # Expected: "10200.30"
print(europenize("10,200.30"))  # Expected: "10,200.30"
