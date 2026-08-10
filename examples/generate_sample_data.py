from engibench.parser import parse_line

examples = [
    '{"temperature_C":25.4,"voltage_V":3.31}',
    "temperature_C=25.4,voltage_V=3.31",
    "25.4,3.31,0.12",
]

for line in examples:
    print(parse_line(line, source="example"))
