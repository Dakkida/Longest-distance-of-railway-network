import random 
import sys
import train_ticket_firster as calFister
import train_ticket as cal

def generate(n_stations, n_lines, seed=None):
    """駅 n_stations 個・路線 n_lines 本のランダムな路線リストを返す。"""
    rng = random.Random(seed)

    # 路線数は最低でも「全駅をつなぐのに必要な本数(n-1)」以上にする
    n_lines = max(n_lines, n_stations - 1)
    # 単純グラフで張れる路線数の上限を超えないようにする
    max_edges = n_stations * (n_stations - 1) // 2
    n_lines = min(n_lines, max_edges)

    lines = []
    existing = set()

    # 1) 連結になる骨組み(全駅を一筆でつなぐ道)を作る
    order = list(range(1, n_stations + 1))
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):
        key = (min(a, b), max(a, b))
        existing.add(key)
        lines.append((a, b, round(rng.uniform(0.5, 20.0), 2)))

    # 2) 残りの路線をランダムに追加(重複ペアと自己ループは除く)
    while len(lines) < n_lines:
        u = rng.randint(1, n_stations)
        v = rng.randint(1, n_stations)
        if u == v:
            continue
        key = (min(u, v), max(u, v))
        if key in existing:
            continue
        existing.add(key)
        lines.append((u, v, round(rng.uniform(0.5, 20.0), 2)))

    rng.shuffle(lines)

    # 3) 一部の距離を整数に(問題文の "3, 4, 4" のような表記も混ぜる)
    result = []
    for a, b, d in lines:
        dist = int(d) if rng.random() < 0.2 else d
        result.append((a, b, dist))
    return result

def main():
    args = sys.argv[1:]
    n_stations = int(args[0]) if len(args) >= 1 else 12
    n_lines = int(args[1]) if len(args) >= 2 else 20
    out_path = args[2] if len(args) >= 3 else "input.txt"
    seed = int(args[3]) if len(args) >= 4 else None

    lines = generate(n_stations, n_lines, seed)
    with open(out_path, "w", newline="") as f:
        for a, b, d in lines:
            f.write(f"{a}, {b}, {d}\n")

    print(f"駅 {n_stations} 個、路線 {len(lines)} 本を {out_path} に生成しました")
    print("実行しますか？ (y/n): ", end="")
    if input().strip().lower() == "y":
        print("test")

if __name__ == "__main__":
    main()