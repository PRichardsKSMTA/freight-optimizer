import pandas as pd
import numpy as np
from itertools import permutations, combinations
 
# --- CONFIG (set these to match the run you’re debugging) ---
MODEL = "tsp"            # "tsp" or "two_tour"
MAX_DEADHEAD = 500       # None for no cap (be inclusive when debugging)
MARGIN_TARGET = 0.0      # Use 0 to remove margin pressure in diagnostics
PROFIT_CUTOFF = -2000    # matches DataManager
USE_ZIP3 = True          # set True if your run did ZIP3 normalization
QUANTILE = 0.0           # set 0.0 to disable pruning for diagnostics
TRIP_IDS_TO_EXPLAIN = ["<PUT_ONE_OR_MORE_TRIP_IDS_HERE>"]
 
# --- LOAD THE INPUTS YOUR RUN SAVED ---
trip_df = pd.read_csv("output/trip_df.csv", index_col=0)  # has normalized columns already
em = pd.read_csv("output/empty_miles_df.csv", index_col=[0,1])  # MultiIndex (origin_zip,destination_zip)
 
# Normalize (same as DataManager) ---------------------------------------------
trip_df = trip_df.copy()
trip_df["trip_orgn_zip"] = trip_df["trip_orgn_zip"].astype(str).str.zfill(5)
trip_df["trip_dst_zip"]  = trip_df["trip_dst_zip"].astype(str).str.zfill(5)
if USE_ZIP3:
    trip_df["trip_orgn_zip"] = trip_df["trip_orgn_zip"].str[:3].str.ljust(5, "0")
    trip_df["trip_dst_zip"]  = trip_df["trip_dst_zip"].str[:3].str.ljust(5, "0")
 
trip_df["trip_profit"] = trip_df["trip_revenue"] - trip_df["trip_cost"]
 
# Map trip_id -> row index used internally
id_to_idx = {trip_df.loc[i, "trip_id"]: i for i in trip_df.index}
 
missing = [tid for tid in TRIP_IDS_TO_EXPLAIN if tid not in id_to_idx]
if missing:
    print("These trip_ids were NOT in the dataset (filtered before optimization):", missing)
 
focus_idxs = [id_to_idx[tid] for tid in TRIP_IDS_TO_EXPLAIN if tid in id_to_idx]
 
def explain_tsp_for(idx):
    # Build candidate arcs involving this trip only (keeps runtime modest)
    all_idxs = trip_df.index.tolist()
    outs = [(idx, j) for j in all_idxs if j != idx]
    ins  = [(i, idx) for i in all_idxs if i != idx]
    arcs = outs + ins
    df = pd.DataFrame(arcs, columns=["t1","t2"])
 
    # Join trip fields
    df = df.join(trip_df[["trip_dst_zip","trip_profit","must_take_flag","trip_distance","trip_cost","trip_revenue"]]
                 .rename(columns={"trip_dst_zip":"trip_dst_zip1","trip_profit":"trip_profit1",
                                  "must_take_flag":"must_take_orgn"}), on="t1")
    df = df.join(trip_df[["trip_orgn_zip","must_take_flag"]]
                 .rename(columns={"trip_orgn_zip":"trip_orgn_zip2","must_take_flag":"must_take_dest"}), on="t2")
 
    # Merge empty miles cost for the connection
    df = df.join(em, on=[("trip_dst_zip1","trip_orgn_zip2")])
 
    report = {}
 
    # Missing empty miles
    miss_mask = df["empty_cost"].isna()
    report["missing_empty_miles"] = int(miss_mask.sum())
    df = df[~miss_mask].copy()
 
    # Deadhead cap
    if MAX_DEADHEAD is not None:
        cap_mask = (df["empty_miles"] > MAX_DEADHEAD) & (~df["must_take_orgn"])
        report["pruned_deadhead_cap"] = int(cap_mask.sum())
        df = df[~cap_mask].copy()
 
    # Profit / margin
    df["profit"] = df["trip_profit1"] - df["empty_cost"]
    df["is_must_take"] = (df["must_take_orgn"] | df["must_take_dest"]).astype(int)
    df["profit_adj"] = df["profit"] + 10000*df["is_must_take"]
    df["margin_improvement"] = df["profit"] - df["trip_revenue"]*MARGIN_TARGET
 
    # Profit cutoff
    pc_mask = (~df["is_must_take"]) & (df["profit"] <= PROFIT_CUTOFF)
    report["pruned_profit_cutoff"] = int(pc_mask.sum())
    df_keep = df[~pc_mask].copy()
 
    # Quantile pruning (optional)
    if QUANTILE and QUANTILE > 0:
        # Keep arcs with profit >= quantile for either endpoint
        t1_q = df_keep.groupby("t1")["profit"].quantile(QUANTILE).rename("t1_q")
        t2_q = df_keep.groupby("t2")["profit"].quantile(QUANTILE).rename("t2_q")
        df_keep = df_keep.join(t1_q, on="t1").join(t2_q, on="t2")
        q_mask = ~((df_keep["profit_adj"] >= df_keep["t1_q"]) | (df_keep["profit_adj"] >= df_keep["t2_q"]))
        report["pruned_quantile"] = int(q_mask.sum())
        df_keep = df_keep[~q_mask].copy()
 
    # Count viable ins/outs
    viable_outs = df_keep[df_keep["t1"] == idx].shape[0]
    viable_ins  = df_keep[df_keep["t2"] == idx].shape[0]
    report["viable_outgoing"] = int(viable_outs)
    report["viable_incoming"] = int(viable_ins)
 
    # Top candidates
    top = df_keep.sort_values("profit_adj", ascending=False).head(10)[
        ["t1","t2","profit","profit_adj","empty_miles","empty_cost","margin_improvement"]
    ]
    return report, top
 
def explain_two_tour_for(idx):
    # Build candidate pairs involving this trip only
    all_idxs = [j for j in trip_df.index if j != idx]
    pairs = [(min(idx,j), max(idx,j)) for j in all_idxs]  # unordered
    df = pd.DataFrame(pairs, columns=["t1","t2"])
 
    # Join trip fields for both
    one = trip_df[["trip_orgn_zip","trip_dst_zip","trip_profit","must_take_flag","trip_revenue"]]
    df = df.join(one.rename(columns={"trip_orgn_zip":"trip_orgn_zip1","trip_dst_zip":"trip_dst_zip1",
                                     "trip_profit":"trip_profit1","must_take_flag":"must_take_orgn",
                                     "trip_revenue":"revenue1"}), on="t1")
    df = df.join(one.rename(columns={"trip_orgn_zip":"trip_orgn_zip2","trip_dst_zip":"trip_dst_zip2",
                                     "trip_profit":"trip_profit2","must_take_flag":"must_take_dest",
                                     "trip_revenue":"revenue2"}), on="t2")
 
    # Two deadheads
    df = df.assign(
        deadhead1 = em.lookup(df["trip_dst_zip1"].values, df["trip_orgn_zip2"].values) if not em.empty else np.nan,
        deadhead2 = em.lookup(df["trip_dst_zip2"].values, df["trip_orgn_zip1"].values) if not em.empty else np.nan,
    )
    # Safer alternative if lookup is unavailable:
    # df = df.join(em.rename(columns={"empty_cost":"deadhead1"}), on=[("trip_dst_zip1","trip_orgn_zip2")])
    # df = df.join(em.rename(columns={"empty_cost":"deadhead2"}), on=[("trip_dst_zip2","trip_orgn_zip1")])
 
    report = {}
    miss_mask = df["deadhead1"].isna() | df["deadhead2"].isna()
    report["missing_empty_miles_pairs"] = int(miss_mask.sum())
    df = df[~miss_mask].copy()
 
    if MAX_DEADHEAD is not None:
        cap1 = (df["deadhead1"] > MAX_DEADHEAD) & (~df["must_take_orgn"])
        cap2 = (df["deadhead2"] > MAX_DEADHEAD) & (~df["must_take_dest"])
        report["pruned_deadhead_cap"] = int((cap1 | cap2).sum())
        df = df[~(cap1 | cap2)].copy()
 
    df["profit"]  = df["trip_profit1"] + df["trip_profit2"] - df["deadhead1"] - df["deadhead2"]
    df["revenue"] = df["revenue1"] + df["revenue2"]
    df["is_must_take"] = (df["must_take_orgn"] | df["must_take_dest"]).astype(int)
    df["profit_adj"] = df["profit"] + 10000*df["is_must_take"]
    df["margin_improvement"] = df["profit"] - df["revenue"]*MARGIN_TARGET
 
    pc_mask = (~df["is_must_take"]) & (df["profit"] <= PROFIT_CUTOFF)
    report["pruned_profit_cutoff"] = int(pc_mask.sum())
    df_keep = df[~pc_mask].copy()
 
    if QUANTILE and QUANTILE > 0:
        t1_q = df_keep.groupby("t1")["profit"].quantile(QUANTILE).rename("t1_q")
        df_keep = df_keep.join(t1_q, on="t1")
        q_mask = df_keep["profit_adj"] < df_keep["t1_q"]
        report["pruned_quantile"] = int(q_mask.sum())
        df_keep = df_keep[~q_mask].copy()
 
    report["viable_pairs"] = int(df_keep.shape[0])
    top = df_keep.sort_values("profit_adj", ascending=False).head(10)[
        ["t1","t2","profit","profit_adj","margin_improvement","deadhead1","deadhead2"]
    ]
    return report, top
 
for tid in TRIP_IDS_TO_EXPLAIN:
    if tid not in id_to_idx:
        continue
    idx = id_to_idx[tid]
    print(f"\n=== Diagnostics for trip_id {tid} (row idx {idx}) ===")
    if MODEL.lower() == "tsp":
        report, top = explain_tsp_for(idx)
    else:
        report, top = explain_two_tour_for(idx)
    for k,v in report.items():
        print(f"{k}: {v}")
    print("\nTop viable candidates (up to 10):")
    print(top)