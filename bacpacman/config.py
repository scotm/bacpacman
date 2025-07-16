import questionary

# Define a custom style for the prompts
custom_style = questionary.Style(
    [
        ("qmark", "fg:#673ab7 bold"),  # Question mark
        ("question", "bold"),  # Question text
        ("answer", "fg:#f44336 bold"),  # Answer text
        ("pointer", "fg:#673ab7 bold"),  # Pointer character
        ("highlighted", "fg:#673ab7 bold"),  # Highlighted choice
        ("selected", "fg:#ffffff bg:#673ab7"),  # Selected choice
        ("separator", "fg:#cc5454"),  # Separator
        ("instruction", "fg:#858585"),  # Instruction text
        ("text", ""),  # Default text
        ("disabled", "fg:#858585 italic"),  # Disabled choices
    ]
)
