import os

# --- CONFIGURATION ---
OUTPUT_FILE = "project_context.md"
# Folders to skip entirely
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.vscode', 'venv', 'env'}
# Extensions to skip (binaries, images, etc.)
IGNORE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pyc', '.exe', '.dll', '.so', '.pdf'}
# Mapping extensions to markdown language tags
LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.jsx': 'jsx',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.md': 'markdown',
    '.sh': 'bash',
    '.yml': 'yaml',
    '.yaml': 'yaml'
}

def generate_markdown():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# Project Source Code Context\n\n")
        
        # Optional: Add a directory tree at the top
        outfile.write("## Project Structure\n```text\n")
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if not any(f.endswith(ext) for ext in IGNORE_EXTS):
                    outfile.write(f"{sub_indent}{f}\n")
        outfile.write("```\n\n---\n\n")

        # Process and write file contents
        for root, dirs, files in os.walk('.'):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in IGNORE_EXTS or file == OUTPUT_FILE:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        
                        relative_path = os.path.relpath(file_path, '.')
                        lang = LANG_MAP.get(ext, '')
                        
                        outfile.write(f"## File: {relative_path}\n")
                        outfile.write(f"```{lang}\n")
                        outfile.write(content)
                        outfile.write(f"\n```\n\n")
                        print(f"Included: {relative_path}")
                except Exception as e:
                    print(f"Skipped {file_path} due to error: {e}")

if __name__ == "__main__":
    generate_markdown()
    print(f"\nDone! Project saved to {OUTPUT_FILE}")