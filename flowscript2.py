import re
from prettytable import PrettyTable
from textwrap import fill

# Define token patterns
TOKEN_PATTERNS = {
    "EVENT": r"on|schedule|if|repeat|activate",
    "SENSOR": r"motion|temperature|humidity|door|sound|triggered",
    "DEVICE": r"lights|AC|fan|door|alarm|sprinkler|watering",
    "OPERATION": r"turn on|turn off|increase|decrease|open|close|start|check",
    "MODE": r"night mode|vacation mode|silent mode",
    "TIME": r"\d{1,2}:\d{2} (AM|PM)",
    "TIME_INTERVAL": r"\d+ (seconds|minutes|hours)",
    "NUMBER": r"\d+",
    "OPERATOR": r">|<|>=|<=|==",
    "THEN": r"then",
    "FROM_TO": r"from|to",
    "DETECTED": r"detected",
    "AT": r"at",
    "EVERY": r"every"
}

# Combine token patterns
TOKEN_REGEX = re.compile(
    "|".join(f"(?P<{key}>{pattern})" for key, pattern in TOKEN_PATTERNS.items()), re.IGNORECASE
)

# Tokenizer function
def tokenize(command):
    tokens = []
    for match in TOKEN_REGEX.finditer(command):
        token_type = match.lastgroup
        value = match.group(token_type)
        tokens.append((token_type, value))
    return tokens

# Matching function
def match_pattern(tokens, expected_pattern):
    extracted_types = [t[0] for t in tokens]
    return extracted_types == expected_pattern, "Valid command." if extracted_types == expected_pattern else "Syntax error in command."

# Validation functions
def validate_event(tokens):
    return match_pattern(tokens, ["EVENT", "SENSOR", "DETECTED", "THEN", "OPERATION", "DEVICE"])

def validate_schedule(tokens):
    return match_pattern(tokens, ["EVENT", "OPERATION", "DEVICE", "AT", "TIME"])

def validate_condition(tokens):
    return match_pattern(tokens, ["EVENT", "SENSOR", "OPERATOR", "NUMBER", "THEN", "OPERATION", "DEVICE"])

def validate_loop(tokens):
    return match_pattern(tokens, ["EVENT", "OPERATION", "SENSOR", "EVERY", "TIME_INTERVAL"])

def validate_mode(tokens):
    return match_pattern(tokens, ["EVENT", "MODE", "FROM_TO", "TIME", "FROM_TO", "TIME"])

# Syntax validation function
def validate_syntax(tokens):
    if not tokens:
        return False, "Empty command."
    
    first_token = tokens[0][1].lower()
    if first_token == "on":
        return validate_event(tokens)
    elif first_token == "schedule":
        return validate_schedule(tokens)
    elif first_token == "if":
        return validate_condition(tokens)
    elif first_token == "repeat":
        return validate_loop(tokens)
    elif first_token == "activate":
        return validate_mode(tokens)
    else:
        return False, "Invalid command start."

# Invalid command validation function
def validate_invalid_command(command, tokens):
    # Check if "when" is used instead of "on"
    if "when" in command:
        return f"'when' is not a valid keyword. Correct syntax: 'on motion detected then turn on lights'."
    
    # Check if 'then' is missing in conditions (e.g., "if temperature > 30 start AC")
    if "if" in command and "then" not in [t[0] for t in tokens]:
        return "The 'then' keyword is required before 'start AC'."
    
    # Check for invalid operation like "open lights"
    if any(t[0] == "OPERATION" and t[1] == "open" for t in tokens) and any(t[0] == "DEVICE" and t[1] == "lights" for t in tokens):
            return "'open lights' is not a valid action. The correct operation is 'turn on lights'."
    
    # Check for incorrect time format
    time_match = re.search(r"(\d{1,2}):(\d{2}) (AM|PM)", command)
    if time_match:
        hours, minutes, meridiem = time_match.groups()
        if not (1 <= int(hours) <= 12) or not (0 <= int(minutes) <= 59):
            return "Invalid time format. Ensure hours are between 1-12 and minutes between 00-59."
    
    # Check if 'from' and 'to' are missing for mode activation
    if "activate" in command and ("from" not in command or "to" not in command):
        return "The 'from' and 'to' keywords are missing. Correct syntax: 'activate silent mode from 10 PM to 6 AM'." 

    return "Error: Invalid command. Ensure your syntax follows the required format."

# Function to wrap text for table formatting
def wrap_text(text, width=50):
    return fill(text, width=width)

# Example test cases
commands = [
    # Valid commands
    "on motion detected then turn on lights",
    "schedule turn on watering at 6:00 AM",
    "if temperature > 30 then turn on AC",
    "repeat check temperature every 10 minutes",
    "activate night mode from 10:00 PM to 6:00 AM",
    "repeat close door every 30 minutes",
    # Invalid commands
    "when motion detected turn on lights",
    "if temperature > 30 start AC",
    "on humidity triggered then open lights",
    "schedule cooling at 14:99 PM",
    "activate silent mode 10 PM 6 AM",
    "on",
    "lights"
]

valid_commands = []
invalid_commands = []

# Initialize PrettyTable for formatting
valid_table = PrettyTable()
invalid_table = PrettyTable()

# Set up table headers
valid_table.field_names = ["Command", "Tokens", "Validation"]
invalid_table.field_names = ["Command", "Tokens", "Error"]

for cmd in commands:
    tokens = tokenize(cmd)
    
    # Format tokens as ('TYPE', 'VALUE')
    formatted_tokens = ", ".join([f"({repr(t[0])}, {repr(t[1])})" for t in tokens])  # Format as ('TYPE', 'VALUE')
    
    # Wrap the formatted tokens for better table readability
    wrapped_tokens = wrap_text(formatted_tokens, 50)

    valid, message = validate_syntax(tokens)
    if valid:
        valid_commands.append([wrap_text(cmd, 25), wrapped_tokens, wrap_text(message, 40)])
    else:
        error_message = validate_invalid_command(cmd, tokens)
        invalid_commands.append([wrap_text(cmd, 25), wrapped_tokens, wrap_text(error_message, 50)])

# Add rows to PrettyTable for valid commands
for row in valid_commands:
    valid_table.add_row(row)

# Add rows to PrettyTable for invalid commands
for row in invalid_commands:
    invalid_table.add_row(row)

# Print tables
print("\nVALID COMMANDS")
print(valid_table)

print("\nINVALID COMMANDS")
print(invalid_table)