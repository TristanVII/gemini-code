import os
import time
import sys
import traceback
from geminicode.context import Context
from geminicode.work_tree.tree import WorkTree
from geminicode.gemini.client import AIClient


def main():
    try:
        ctx = Context(os.getcwd())
        print(f"Initialized in directory: {ctx.cwd}")
        tree = WorkTree(ctx)
        ai_client = AIClient(tree)

        print("\nWelcome to GeminiCode CLI!")
        print("Type 'exit' to quit, or enter your query:")
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                # Check for exit command
                if user_input.lower() in ['exit', 'quit']:
                    print("\nExiting GeminiCode CLI.")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Process the query
                ai_client.add_text_message(user_input)
                ai_client.process_messages()
                
            except KeyboardInterrupt:
                print("\nExiting GeminiCode CLI.")
                break
            except Exception as e:
                print(f"Error processing query: {e}", file=sys.stderr)
                print("Traceback:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                continue

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("Traceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 