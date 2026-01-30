import inspect
from notebooklm import Notebook, Source

print("Inspecting Notebook class...")
try:
    methods = [m for m in dir(Notebook) if not m.startswith('_')]
    print(f"Public methods on Notebook: {methods}")
except Exception as e:
    print(f"Error inspecting Notebook: {e}")

print("\nInspecting Source class...")
try:
    methods = [m for m in dir(Source) if not m.startswith('_')]
    print(f"Public methods on Source: {methods}")
except Exception as e:
    print(f"Error inspecting Source: {e}")
