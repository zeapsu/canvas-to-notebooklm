import inspect
from notebooklm import NotebookLMClient

print("Inspecting NotebookLMClient...")
try:
    # Try to see if we can inspect the class without instantiation for methods
    methods = [m for m in dir(NotebookLMClient) if not m.startswith('_')]
    print(f"Public methods on class: {methods}")
    
    # Check __init__ signature
    sig = inspect.signature(NotebookLMClient.__init__)
    print(f"__init__ signature: {sig}")

except Exception as e:
    print(f"Error inspecting class: {e}")
