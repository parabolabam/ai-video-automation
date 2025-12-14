try:
    import ddgs
    print(f"Version: {ddgs.__version__}")
    print(dir(ddgs))
except ImportError:
    print("Could not import ddgs")
except Exception as e:
    print(f"Error: {e}")
