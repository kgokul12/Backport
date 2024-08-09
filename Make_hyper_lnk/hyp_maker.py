# Function to get user input for texts
def get_user_input():
    texts = []
    print("Enter the text (or type 'done' to finish): ")
    while True:
        text = input()
        if text.lower() == 'done':
            break
        texts.append(text)
    
    return texts

# Get user input for texts
texts = get_user_input()

# Get user input for the URL
base_url = input("Enter the base URL (e.g., 'https://example.com/'): ")

# Generate HTML content with hyperlinks
html_content = "<html><body>\n"
for text in texts:
    link = base_url + text.strip()
    text = text[:14]
    html_content += f'<a href="{link}">{text}</a><br>\n'
html_content += "</body></html>"

# Write the HTML content to a file
with open("Commits.html", "w") as file:
    file.write(html_content)

print("HTML file with hyperlinks created.")

