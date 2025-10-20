import pandas as pd
# coords_df = pd.read_csv("coordenadas.csv")
coords_df = pd.read_csv("Oriente.csv")
coords_df["lon"] = coords_df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[0]))
coords_df["lat"] = coords_df["WKT"].apply(lambda x: float(x.split("(")[1].split(" ")[1].replace(")", "")))
coords_df=coords_df.drop(columns="WKT")
coords_df.to_csv("coordenadas.csv", index=False, encoding="utf-8-sig")
