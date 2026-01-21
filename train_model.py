from pathlib import Path
import pickle

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier


DATA_CANDIDATES = (
    Path("source_code/Iris-Classification-WebApp/Iris.csv"),
    Path("source_code/Iris-Classification-WebApp/iris.csv"),
)


def load_dataset() -> pd.DataFrame:
    for path in DATA_CANDIDATES:
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(
        "Iris dataset not found. Expected one of: "
        + ", ".join(str(p) for p in DATA_CANDIDATES)
    )


def main() -> None:
    data = load_dataset()
    if "Id" in data.columns:
        data = data.drop(columns=["Id"])

    species_map = {"Iris-setosa": 0, "Iris-versicolor": 1, "Iris-virginica": 2}
    data["Species"] = data["Species"].map(species_map).astype(int)

    x = data.drop(columns=["Species"]).values
    y = data["Species"].values

    trainx, testx, trainy, testy = train_test_split(
        x, y, test_size=0.20, random_state=42, stratify=y
    )
    model = KNeighborsClassifier(n_neighbors=5, metric="minkowski", p=2)
    model.fit(trainx, trainy)

    with open("model.pkl", "wb") as f:
        pickle.dump(model, f)

    print(f"Saved model.pkl (accuracy={model.score(testx, testy):.3f})")


if __name__ == "__main__":
    main()
