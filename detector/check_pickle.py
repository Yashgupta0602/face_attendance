import pickle

with open("detector/encodings.pickle", "rb") as f:
    data = pickle.load(f)

print("✅ Pickle file loaded!")
print("Keys in pickle:", data.keys())

print("\nSample Data Preview:")
print(data)
