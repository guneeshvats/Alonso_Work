import re

def group_tables_by_page(file_path):
    # Step 1: Read the file content
    with open(file_path, 'r') as file:
        file_content = file.read()

    # Step 2: Extract sections by page number
    pattern = r'Header:.*?PageNo\|(\d+):.*?(?=Header:|$)'
    matches = re.findall(pattern, file_content, re.S)

    # Step 3: Group sections by page number
    pages = {}
    for match in re.finditer(pattern, file_content, re.S):
        page_no = match.group(1)
        table_content = match.group(0)
        if page_no not in pages:
            pages[page_no] = []
        pages[page_no].append(table_content.strip())

    # Step 4: Create the formatted output
    formatted_output = ""
    for page_no in sorted(pages.keys(), key=int):
        formatted_output += f"\nPage - {page_no}\n\n"
        formatted_output += "\n\n".join(pages[page_no])
        formatted_output += "\n\n"

    # Step 5: Write the formatted output back to the file
    with open(file_path, 'w') as file:
        file.write(formatted_output)

# Example usage
file_path = 'unsan.txt'  # Replace with your actual file path
group_tables_by_page(file_path)
