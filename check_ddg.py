from duckduckgo_search import DDGS
try:
    with DDGS() as ddgs:
        print("Searching...")
        results = ddgs.text("python", max_results=2)
        print("Results:", list(results))
        print("Success!")
except Exception as e:
    print(f"Error: {e}")
