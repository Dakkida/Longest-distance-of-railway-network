import random
import sys
import time
import train_ticket_firster as calFister
import train_ticket as cal


def path_distance(graph, path):
    """経路(駅IDの列)の距離合計を求める。答えの一致検証に使う。"""
    total = 0.0
    for a, b in zip(path, path[1:]):
        total += max(w for v, w in graph[a] if v == b)
    return total


def run_once(text):
    """1つの入力に対して両アルゴリズムを実行し、実行時間と結果を返す。

    計測は「parse + longest_path」の同一スコープでそろえ、標準入出力や
    プロセス起動のばらつきを含めないインプロセス計測にする。
    """
    # firster (高速版: 分枝限定法)
    t0 = time.perf_counter()
    gf, nf = calFister.parse_input(text)
    pf, _ = calFister.longest_path(gf, nf)
    tf = time.perf_counter() - t0

    # normal (総当たり版: DFS 全探索)
    t0 = time.perf_counter()
    gn, nn = cal.input_graph(text)
    pn, _ = cal.longest_path(gn, nn)
    tn = time.perf_counter() - t0

    # 両者の最長距離が一致するかを検証(経路自体は逆順や同距離別経路があり得る)
    df = path_distance(gf, pf)
    dn = path_distance(gn, pn)
    return tf, tn, pf, pn, df, dn

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
    start = time.perf_counter()

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

    print("指定回数実行 or 一回実行(y/n): ", end="")
    choice = input().strip().lower()
    if choice == "y":
        print("何回実行しますか？: ", end="")
        count = int(input().strip())
        total_time_firster = 0.0
        total_time_normal = 0.0
        mismatch = 0
        for i in range(count):
            # 毎回ランダムな路線を生成し、同じ入力で両者を比較する
            lines = generate(n_stations, n_lines, seed)
            with open(out_path, "w", newline="") as f:
                for a, b, d in lines:
                    f.write(f"{a}, {b}, {d}\n")
            text = open(out_path, "r").read()

            tf, tn, _pf, _pn, df, dn = run_once(text)
            total_time_firster += tf
            total_time_normal += tn
            if abs(df - dn) > 1e-9:
                mismatch += 1
                print(f"  [警告] {i + 1}回目で結果が不一致: firster={df} normal={dn}")

        avg_time_firster = total_time_firster / count
        avg_time_normal = total_time_normal / count
        print(f"平均実行時間 (train_ticket_firster.py): {avg_time_firster:.4f} 秒")
        print(f"平均実行時間 (train_ticket.py):         {avg_time_normal:.4f} 秒")
        if avg_time_firster > 0:
            print(f"高速化倍率 (normal / firster): {avg_time_normal / avg_time_firster:.1f} 倍")
        print(f"結果一致: {count - mismatch}/{count} 回")
    else:
        print("どのファイルを実行しますか？ (y/n)(firster/normal): ", end="")
        choice = input().strip().lower()
        text = open(out_path, "r").read()
        if choice == "y":
            t0 = time.perf_counter()
            graph, nodes = calFister.parse_input(text)
            path, _ = calFister.longest_path(graph, nodes)
            elapsed = time.perf_counter() - t0
            print("train_ticket_firster.py の出力:")
            print("\r\n".join(str(x) for x in path))
            print(f"実行時間: {elapsed:.4f} 秒")
        elif choice == "n":
            t0 = time.perf_counter()
            graph, nodes = cal.input_graph(text)
            path, _ = cal.longest_path(graph, nodes)
            elapsed = time.perf_counter() - t0
            print("train_ticket.py の出力:")
            print("\r\n".join(str(x) for x in path))
            print(f"実行時間: {elapsed:.4f} 秒")

    end = time.perf_counter() #計測終了
    print('{:.2f}'.format((end-start))) 
if __name__ == "__main__":
    main()