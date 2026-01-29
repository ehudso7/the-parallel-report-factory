from src.pipeline import run

if __name__ == "__main__":
    result = run()
    print("DONE")
    for k, v in result.items():
        print(f"{k}: {v}")
