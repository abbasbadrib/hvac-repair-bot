import os
import sys

print("=" * 50)
print("Checking project structure")
print("=" * 50)

print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print("")

print("Files in current directory:")
for f in sorted(os.listdir('.')):
    print(f"  - {f}")
print("")

if os.path.exists('app'):
    print("Files in app directory:")
    for f in sorted(os.listdir('app')):
        print(f"  - {f}")
print("")

if os.path.exists('app/handlers'):
    print("Files in app/handlers:")
    for f in sorted(os.listdir('app/handlers')):
        print(f"  - {f}")
print("")
