import json


def debug_print_response(response):
    print("##########################")
    print("Response Candidates:")
    if not response.candidates:
        print("  No candidates in response.")
    else:
        for i, candidate in enumerate(response.candidates):
            print(f"  Candidate {i}:")
            if hasattr(candidate, 'index'):
                print(f"    Index: {candidate.index}")
            print(f"    Finish Reason: {candidate.finish_reason}")

            if candidate.content and candidate.content.parts:
                print("    Content Parts:")
                for j, part in enumerate(candidate.content.parts):
                    part_type_name = type(part).__name__
                    print(f"      Part {j}: ({part_type_name})")
                    if part.text:
                        print(f'        Text: "{part.text}"')
                    if part.function_call:
                        print(f"        Function Call: {part.function_call.name}")
                        try:
                            # Attempt to pretty-print args if they are dict-like
                            args_str = json.dumps(dict(part.function_call.args), indent=2)
                        except (TypeError, AttributeError):
                            args_str = str(part.function_call.args)
                        print(f"          Args: {args_str}")
                    # You can add more specific part handling here if needed
                    # e.g., for executable_code, file_data etc.
            elif candidate.content:
                print(f"    Content Role: {candidate.content.role}")
                print(f"    Content: (No parts or unhandled structure)")
            else:
                print("    Content: Empty")

            if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                print("    Safety Ratings:")
                for rating in candidate.safety_ratings:
                    print(f"      - Category: {rating.category}, Probability: {rating.probability}")
            
            if hasattr(candidate, 'token_count') and candidate.token_count is not None:
                print(f"    Token Count (Candidate): {candidate.token_count}")

            if i < len(response.candidates) - 1:
                print("    --------------------") # Separator between candidates
    print("##########################")